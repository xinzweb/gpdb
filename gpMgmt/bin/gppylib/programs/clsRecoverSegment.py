#!/usr/bin/env python
# Line too long            - pylint: disable=C0301
# Invalid name             - pylint: disable=C0103
#
# Copyright (c) Greenplum Inc 2010. All Rights Reserved.
#
# Note: the option to recover to a new host is not very good if we have a multi-home configuration
#
# Options removed when 4.0 gprecoverseg was implemented:
#        --version
#       -S "Primary segment dbid to force recovery": I think this is done now by bringing the primary down, waiting for
#           failover, and then doing recover full
#       -z "Primary segment data dir and host to force recovery" see removed -S option for comment
#       -f        : force Greenplum Database instance shutdown and restart
#       -F (HAS BEEN CHANGED) -- used to mean "force recovery" and now means "full recovery)
#
# import mainUtils FIRST to get python version check
# THIS IMPORT SHOULD COME FIRST
from gppylib.mainUtils import *

from optparse import OptionGroup
import os, sys, signal, time
from gppylib import gparray, gplog, userinput, utils
from gppylib.util import gp_utils
from gppylib.commands import gp, pg, unix
from gppylib.commands.base import Command, WorkerPool
from gppylib.db import dbconn
from gppylib.gpparseopts import OptParser, OptChecker
from gppylib.operations.startSegments import *
from gppylib.operations.buildMirrorSegments import *
from gppylib.operations.rebalanceSegments import GpSegmentRebalanceOperation
from gppylib.programs import programIoUtils
from gppylib.system import configurationInterface as configInterface
from gppylib.system.environment import GpMasterEnvironment
from gppylib.testold.testUtils import *
from gppylib.parseutils import line_reader, parse_gprecoverseg_line, canonicalize_address
from gppylib.utils import ParsedConfigFile, ParsedConfigFileRow, writeLinesToFile, \
     normalizeAndValidateInputPath, TableLogger
from gppylib.gphostcache import GpInterfaceToHostNameCache
from gppylib.operations.utils import ParallelOperation
from gppylib.operations.package import SyncPackages
from gppylib.heapchecksum import HeapChecksum

logger = gplog.get_default_logger()


class PortAssigner:
    """
    Used to assign new ports to segments on a host

    Note that this could be improved so that we re-use ports for segments that are being recovered but this
      does not seem necessary.

    """

    MAX_PORT_EXCLUSIVE = 65536

    def __init__(self, gpArray):
        #
        # determine port information for recovering to a new host --
        #   we need to know the ports that are in use and the valid range of ports
        #
        segments = gpArray.getDbList()
        ports = [seg.getSegmentPort() for seg in segments if seg.isSegmentQE()]
        if len(ports) > 0:
            self.__minPort = min(ports)
        else:
            raise Exception("No segment ports found in array.")
        self.__usedPortsByHostName = {}

        byHost = GpArray.getSegmentsByHostName(segments)
        for hostName, segments in byHost.iteritems():
            usedPorts = self.__usedPortsByHostName[hostName] = {}
            for seg in segments:
                usedPorts[seg.getSegmentPort()] = True

    def findAndReservePort(self, hostName, address):
        """
        Find an unused port of the given type (normal postmaster or replication port)
        When found, add an entry:  usedPorts[port] = True   and return the port found
        Otherwise raise an exception labeled with the given address
        """
        if hostName not in self.__usedPortsByHostName:
            self.__usedPortsByHostName[hostName] = {}
        usedPorts = self.__usedPortsByHostName[hostName]

        minPort = self.__minPort
        for port in range(minPort, PortAssigner.MAX_PORT_EXCLUSIVE):
            if port not in usedPorts:
                usedPorts[port] = True
                return port
        raise Exception("Unable to assign port on %s" % address)


# -------------------------------------------------------------------------

class RemoteQueryCommand(Command):
    def __init__(self, qname, query, hostname, port, dbname=None):
        self.qname = qname
        self.query = query
        self.hostname = hostname
        self.port = port
        self.dbname = dbname or os.environ.get('PGDATABASE', None) or 'template1'
        self.res = None

    def get_results(self):
        return self.res

    def run(self):
        logger.debug('Executing query (%s:%s) for segment (%s:%s) on database (%s)' % (
            self.qname, self.query, self.hostname, self.port, self.dbname))
        with dbconn.connect(dbconn.DbURL(hostname=self.hostname, port=self.port, dbname=self.dbname),
                            utility=True) as conn:
            res = dbconn.execSQL(conn, self.query)
            self.res = res.fetchall()


# -------------------------------------------------------------------------

class GpRecoverSegmentProgram:
    #
    # Constructor:
    #
    # @param options the options as returned by the options parser
    #
    def __init__(self, options):
        self.__options = options
        self.__pool = None
        self.logger = logger

    def outputToFile(self, mirrorBuilder, gpArray, fileName):
        lines = []

        # one entry for each failure
        for mirror in mirrorBuilder.getMirrorsToBuild():
            output_str = ""
            seg = mirror.getFailedSegment()
            addr = canonicalize_address(seg.getSegmentAddress())
            output_str += ('%s:%d:%s' % (addr, seg.getSegmentPort(), seg.getSegmentDataDirectory()))

            seg = mirror.getFailoverSegment()
            if seg is not None:

                output_str += ' '
                addr = canonicalize_address(seg.getSegmentAddress())
                output_str += ('%s:%d:%s' % (
                    addr, seg.getSegmentPort(), seg.getSegmentDataDirectory()))

            lines.append(output_str)
        writeLinesToFile(fileName, lines)

    def getRecoveryActionsFromConfigFile(self, gpArray):
        """
        getRecoveryActionsFromConfigFile

        returns: a tuple (segments in change tracking disabled mode which are unable to recover, GpMirrorListToBuild object
                 containing information of segments which are able to recover)
        """

        # create fileData object from config file
        #
        filename = self.__options.recoveryConfigFile
        rows = []
        with open(filename) as f:
            for lineno, line in line_reader(f):
                fixed, flexible = parse_gprecoverseg_line(filename, lineno, line)
                rows.append(ParsedConfigFileRow(fixed, flexible, line))
        fileData = ParsedConfigFile(rows)

        allAddresses = [row.getFixedValuesMap()["newAddress"] for row in fileData.getRows()
                        if "newAddress" in row.getFixedValuesMap()]
        allNoneArr = [None] * len(allAddresses)
        interfaceLookup = GpInterfaceToHostNameCache(self.__pool, allAddresses, allNoneArr)

        failedSegments = []
        failoverSegments = []
        for row in fileData.getRows():
            fixedValues = row.getFixedValuesMap()
            flexibleValues = row.getFlexibleValuesMap()

            # find the failed segment
            failedAddress = fixedValues['failedAddress']
            failedPort = fixedValues['failedPort']
            failedDataDirectory = normalizeAndValidateInputPath(fixedValues['failedDataDirectory'],
                                                                "config file", row.getLine())
            failedSegment = None
            for segment in gpArray.getDbList():
                if segment.getSegmentAddress() == failedAddress and \
                                str(segment.getSegmentPort()) == failedPort and \
                                segment.getSegmentDataDirectory() == failedDataDirectory:

                    if failedSegment is not None:
                        #
                        # this could be an assertion -- configuration should not allow multiple entries!
                        #
                        raise Exception(("A segment to recover was found twice in configuration.  "
                                         "This segment is described by address:port:directory '%s:%s:%s' "
                                         "on the input line: %s") %
                                        (failedAddress, failedPort, failedDataDirectory, row.getLine()))
                    failedSegment = segment

            if failedSegment is None:
                raise Exception("A segment to recover was not found in configuration.  " \
                                "This segment is described by address:port:directory '%s:%s:%s' on the input line: %s" %
                                (failedAddress, failedPort, failedDataDirectory, row.getLine()))

            failoverSegment = None
            if "newAddress" in fixedValues:
                """
                When the second set was passed, the caller is going to tell us to where we need to failover, so
                  build a failover segment
                """
                # these two lines make it so that failoverSegment points to the object that is registered in gparray
                failoverSegment = failedSegment
                failedSegment = failoverSegment.copy()

                address = fixedValues["newAddress"]
                try:
                    port = int(fixedValues["newPort"])
                except ValueError:
                    raise Exception('Config file format error, invalid number value in line: %s' % (row.getLine()))

                dataDirectory = normalizeAndValidateInputPath(fixedValues["newDataDirectory"], "config file",
                                                              row.getLine())

                hostName = interfaceLookup.getHostName(address)
                if hostName is None:
                    raise Exception('Unable to find host name for address %s from line:%s' % (address, row.getLine()))

                # now update values in failover segment
                failoverSegment.setSegmentAddress(address)
                failoverSegment.setSegmentHostName(hostName)
                failoverSegment.setSegmentPort(port)
                failoverSegment.setSegmentDataDirectory(dataDirectory)

            # this must come AFTER the if check above because failedSegment can be adjusted to
            #   point to a different object
            failedSegments.append(failedSegment)
            failoverSegments.append(failoverSegment)

        peersForFailedSegments = self.findAndValidatePeersForFailedSegments(gpArray, failedSegments)

        segmentStates = self.check_segment_state_ready_for_recovery(gpArray.getSegDbList(), gpArray.getSegDbMap())

        segs = []
        segs_in_change_tracking_disabled = []
        segs_with_persistent_mirroring_disabled = []
        for index, failedSegment in enumerate(failedSegments):
            peerForFailedSegment = peersForFailedSegments[index]

            peerForFailedSegmentDbId = peerForFailedSegment.getSegmentDbId()
            if not self.__options.forceFullResynchronization and self.is_segment_mirror_state_mismatched(gpArray,
                                                                                                         peerForFailedSegment):
                segs_with_persistent_mirroring_disabled.append(peerForFailedSegmentDbId)
            elif (not self.__options.forceFullResynchronization and
                          peerForFailedSegmentDbId in segmentStates and
                      self.check_segment_change_tracking_disabled_state(segmentStates[peerForFailedSegmentDbId])):

                segs_in_change_tracking_disabled.append(peerForFailedSegmentDbId)
            else:
                segs.append(GpMirrorToBuild(failedSegment, peerForFailedSegment, failoverSegments[index],
                                            self.__options.forceFullResynchronization))

        self._output_segments_in_change_tracking_disabled(segs_in_change_tracking_disabled)
        self._output_segments_with_persistent_mirroring_disabled(segs_with_persistent_mirroring_disabled)

        return segs_in_change_tracking_disabled, GpMirrorListToBuild(segs, self.__pool, self.__options.quiet,
                                                                     self.__options.parallelDegree)

    def findAndValidatePeersForFailedSegments(self, gpArray, failedSegments):
        dbIdToPeerMap = gpArray.getDbIdToPeerMap()
        peersForFailedSegments = [dbIdToPeerMap.get(seg.getSegmentDbId()) for seg in failedSegments]

        for i in range(len(failedSegments)):
            peer = peersForFailedSegments[i]
            if peer is None:
                raise Exception("No peer found for dbid %s" % failedSegments[i].getSegmentDbId())
            elif peer.isSegmentDown():
                raise Exception(
                    "Both segments for content %s are down; Try restarting Greenplum DB and running %s again." %
                    (peer.getSegmentContentId(), getProgramName()))
        return peersForFailedSegments

    def getRecoveryActionsFromConfiguration(self, gpEnv, gpArray):
        """
        getRecoveryActionsFromConfiguration

        returns: a tuple (segments in change tracking disabled mode which are unable to recover, GpMirrorListToBuild object
                 containing information of segments which are able to recover)
        """
        segments = gpArray.getSegDbList()

        failedSegments = [seg for seg in segments if seg.isSegmentDown()]
        peersForFailedSegments = self.findAndValidatePeersForFailedSegments(gpArray, failedSegments)

        # Dictionaries used for building mapping to new hosts
        recoverAddressMap = {}
        recoverHostMap = {}
        interfaceHostnameWarnings = []

        # Check if the array is a "standard" array
        (isStandardArray, _ignore) = gpArray.isStandardArray()

        recoverHostIdx = 0

        if self.__options.newRecoverHosts and len(self.__options.newRecoverHosts) > 0:
            for seg in failedSegments:
                segAddress = seg.getSegmentAddress()
                segHostname = seg.getSegmentHostName()

                # Haven't seen this hostname before so we put it on a new host
                if not recoverHostMap.has_key(segHostname):
                    try:
                        recoverHostMap[segHostname] = self.__options.newRecoverHosts[recoverHostIdx]
                    except:
                        # If we get here, not enough hosts were specified in the -p option.  Need 1 new host
                        # per 1 failed host.
                        raise Exception('Not enough new recovery hosts given for recovery.')
                    recoverHostIdx += 1

                if isStandardArray:
                    # We have a standard array configuration, so we'll try to use the same
                    # interface naming convention.  If this doesn't work, we'll correct it
                    # below on name lookup
                    segInterface = segAddress[segAddress.rfind('-'):]
                    destAddress = recoverHostMap[segHostname] + segInterface
                    destHostname = recoverHostMap[segHostname]
                else:
                    # Non standard configuration so we won't make assumptions on
                    # naming.  Instead we'll use the hostname passed in for both
                    # hostname and address and flag for warning later.
                    destAddress = recoverHostMap[segHostname]
                    destHostname = recoverHostMap[segHostname]

                # Save off the new host/address for this address.
                recoverAddressMap[segAddress] = (destHostname, destAddress)

            # Now that we've generated the mapping, look up all the addresses to make
            # sure they are resolvable.
            interfaces = [address for (_ignore, address) in recoverAddressMap.values()]
            interfaceLookup = GpInterfaceToHostNameCache(self.__pool, interfaces, [None] * len(interfaces))

            for key in recoverAddressMap.keys():
                (newHostname, newAddress) = recoverAddressMap[key]
                try:
                    addressHostnameLookup = interfaceLookup.getHostName(newAddress)
                    # Lookup failed so use hostname passed in for everything.
                    if addressHostnameLookup is None:
                        interfaceHostnameWarnings.append(
                            "Lookup of %s failed.  Using %s for both hostname and address." % (newAddress, newHostname))
                        newAddress = newHostname
                except:
                    # Catch all exceptions.  We will use hostname instead of address
                    # that we generated.
                    interfaceHostnameWarnings.append(
                        "Lookup of %s failed.  Using %s for both hostname and address." % (newAddress, newHostname))
                    newAddress = newHostname

                # if we've updated the address to use the hostname because of lookup failure
                # make sure the hostname is resolvable and up
                if newHostname == newAddress:
                    try:
                        unix.Ping.local("ping new hostname", newHostname)
                    except:
                        raise Exception("Ping of host %s failed." % newHostname)

                # Save changes in map
                recoverAddressMap[key] = (newHostname, newAddress)

            if len(self.__options.newRecoverHosts) != recoverHostIdx:
                interfaceHostnameWarnings.append("The following recovery hosts were not needed:")
                for h in self.__options.newRecoverHosts[recoverHostIdx:]:
                    interfaceHostnameWarnings.append("\t%s" % h)

        portAssigner = PortAssigner(gpArray)

        forceFull = self.__options.forceFullResynchronization

        segmentStates = self.check_segment_state_ready_for_recovery(gpArray.getSegDbList(), gpArray.getSegDbMap())

        segs = []
        segs_in_change_tracking_disabled = []
        segs_with_persistent_mirroring_disabled = []
        for i in range(len(failedSegments)):

            failoverSegment = None
            failedSegment = failedSegments[i]
            liveSegment = peersForFailedSegments[i]

            if self.__options.newRecoverHosts and len(self.__options.newRecoverHosts) > 0:
                (newRecoverHost, newRecoverAddress) = recoverAddressMap[failedSegment.getSegmentAddress()]
                # these two lines make it so that failoverSegment points to the object that is registered in gparray
                failoverSegment = failedSegment
                failedSegment = failoverSegment.copy()
                failoverSegment.setSegmentHostName(newRecoverHost)
                failoverSegment.setSegmentAddress(newRecoverAddress)
                port = portAssigner.findAndReservePort(newRecoverHost, newRecoverAddress)
                failoverSegment.setSegmentPort(port)

            if not forceFull and self.is_segment_mirror_state_mismatched(gpArray, liveSegment):
                segs_with_persistent_mirroring_disabled.append(liveSegment.getSegmentDbId())

            elif (not forceFull and liveSegment.getSegmentDbId() in segmentStates and
                      self.check_segment_change_tracking_disabled_state(segmentStates[liveSegment.getSegmentDbId()])):

                segs_in_change_tracking_disabled.append(liveSegment.getSegmentDbId())

            else:
                segs.append(GpMirrorToBuild(failedSegment, liveSegment, failoverSegment, forceFull))

        self._output_segments_in_change_tracking_disabled(segs_in_change_tracking_disabled)
        self._output_segments_with_persistent_mirroring_disabled(segs_with_persistent_mirroring_disabled)

        return segs_in_change_tracking_disabled, GpMirrorListToBuild(segs, self.__pool, self.__options.quiet,
                                                                     self.__options.parallelDegree,
                                                                     interfaceHostnameWarnings)

    def _output_segments_in_change_tracking_disabled(self, segs_in_change_tracking_disabled=None):
        if segs_in_change_tracking_disabled:
            self.logger.warn(
                'Segments with dbid %s in change tracking disabled state, need to run recoverseg with -F option.' %
                (' ,'.join(str(seg_id) for seg_id in segs_in_change_tracking_disabled)))

    def check_segment_change_tracking_disabled_state(self, segmentState):
        if segmentState == gparray.SEGMENT_STATE_CHANGE_TRACKING_DISABLED:
            return True
        return False

    def _output_segments_with_persistent_mirroring_disabled(self, segs_persistent_mirroring_disabled=None):
        if segs_persistent_mirroring_disabled:
            self.logger.warn('Segments with dbid %s not recovered; persistent mirroring state is disabled.' %
                             (', '.join(str(seg_id) for seg_id in segs_persistent_mirroring_disabled)))

    def is_segment_mirror_state_mismatched(self, gpArray, segment):
        if gpArray.hasMirrors:
            # Determines whether cluster has mirrors
            with dbconn.connect(dbconn.DbURL()) as conn:
                res = dbconn.execSQL(conn,
                                     "SELECT mirror_existence_state "
                                     "from gp_dist_random('gp_persistent_relation_node') "
                                     "where gp_segment_id=%s group by 1;" % segment.getSegmentContentId()).fetchall()
                # For a mirrored system, there should not be any mirror_existance_state entries with no mirrors.
                # If any exist, the segment contains a PT inconsistency.
                for state in res:
                    if state[0] == 1:  # 1 is the mirror_existence_state representing no mirrors
                        return True
        return False

    def getRecoveryActionsBasedOnOptions(self, gpEnv, gpArray):
        if self.__options.rebalanceSegments:
            return None, GpSegmentRebalanceOperation(gpEnv, gpArray)
        elif self.__options.recoveryConfigFile is not None:
            return self.getRecoveryActionsFromConfigFile(gpArray)
        else:
            return self.getRecoveryActionsFromConfiguration(gpEnv, gpArray)

    def syncPackages(self, new_hosts):
        # The design decision here is to squash any exceptions resulting from the
        # synchronization of packages. We should *not* disturb the user's attempts to recover.
        try:
            self.logger.info('Syncing Greenplum Database extensions')
            operations = [SyncPackages(host) for host in new_hosts]
            ParallelOperation(operations, self.__options.parallelDegree).run()
            # introspect outcomes
            for operation in operations:
                operation.get_ret()
        except:
            self.logger.exception('Syncing of Greenplum Database extensions has failed.')
            self.logger.warning('Please run gppkg --clean after successful segment recovery.')

    def displayRecovery(self, mirrorBuilder, gpArray):
        self.logger.info('Greenplum instance recovery parameters')
        self.logger.info('---------------------------------------------------------')

        if self.__options.recoveryConfigFile:
            self.logger.info('Recovery from configuration -i option supplied')
        elif self.__options.newRecoverHosts is not None:
            self.logger.info('Recovery type              = Pool Host')
            for h in self.__options.newRecoverHosts:
                self.logger.info('Pool host for recovery     = %s' % h)
        elif self.__options.rebalanceSegments:
            self.logger.info('Recovery type              = Rebalance')
        else:
            self.logger.info('Recovery type              = Standard')

        if self.__options.rebalanceSegments:
            i = 1
            total = len(gpArray.get_unbalanced_segdbs())
            for toRebalance in gpArray.get_unbalanced_segdbs():
                tabLog = TableLogger()
                self.logger.info('---------------------------------------------------------')
                self.logger.info('Unbalanced segment %d of %d' % (i, total))
                self.logger.info('---------------------------------------------------------')
                programIoUtils.appendSegmentInfoForOutput("Unbalanced", gpArray, toRebalance, tabLog)
                tabLog.info(["Balanced role", "= Primary" if toRebalance.preferred_role == 'p' else "= Mirror"])
                tabLog.info(["Current role", "= Primary" if toRebalance.role == 'p' else "= Mirror"])
                tabLog.outputTable()
                i += 1
        else:
            i = 0
            total = len(mirrorBuilder.getMirrorsToBuild())
            for toRecover in mirrorBuilder.getMirrorsToBuild():
                self.logger.info('---------------------------------------------------------')
                self.logger.info('Recovery %d of %d' % (i + 1, total))
                self.logger.info('---------------------------------------------------------')

                tabLog = TableLogger()

                syncMode = "Full" if toRecover.isFullSynchronization() else "Incremental"
                tabLog.info(["Synchronization mode", "= " + syncMode])
                programIoUtils.appendSegmentInfoForOutput("Failed", gpArray, toRecover.getFailedSegment(), tabLog)
                programIoUtils.appendSegmentInfoForOutput("Recovery Source", gpArray, toRecover.getLiveSegment(),
                                                          tabLog)

                if toRecover.getFailoverSegment() is not None:
                    programIoUtils.appendSegmentInfoForOutput("Recovery Target", gpArray,
                                                              toRecover.getFailoverSegment(), tabLog)
                else:
                    tabLog.info(["Recovery Target", "= in-place"])
                tabLog.outputTable()

                i = i + 1

        self.logger.info('---------------------------------------------------------')

    def __getSimpleSegmentLabel(self, seg):
        addr = canonicalize_address(seg.getSegmentAddress())
        return "%s:%s" % (addr, seg.getSegmentDataDirectory())

    def __displayRecoveryWarnings(self, mirrorBuilder):
        for warning in self._getRecoveryWarnings(mirrorBuilder):
            self.logger.warn(warning)

    def _getRecoveryWarnings(self, mirrorBuilder):
        """
        return an array of string warnings regarding the recovery
        """
        res = []
        for toRecover in mirrorBuilder.getMirrorsToBuild():

            if toRecover.getFailoverSegment() is not None:
                #
                # user specified a failover location -- warn if it's the same host as its primary
                #
                src = toRecover.getLiveSegment()
                dest = toRecover.getFailoverSegment()

                if src.getSegmentHostName() == dest.getSegmentHostName():
                    res.append("Segment is being recovered to the same host as its primary: "
                               "primary %s    failover target: %s"
                               % (self.__getSimpleSegmentLabel(src), self.__getSimpleSegmentLabel(dest)))

        for warning in mirrorBuilder.getAdditionalWarnings():
            res.append(warning)

        return res

    def _get_dblist(self):
        # template0 does not accept any connections so we exclude it
        with dbconn.connect(dbconn.DbURL()) as conn:
            res = dbconn.execSQL(conn, "SELECT datname FROM PG_DATABASE WHERE datname != 'template0'")
        return res.fetchall()


    """
    The method uses gp_primarymirror to get the status of all the segments which are up and running.
    It checks to see if the segmentState field in the output is "Ready" or "ChangeTrackingDisabled".
    If even one of the segments is not able to connect, then we fail.
    """

    def _check_segment_state_for_connection(self, confProvider):
        self.logger.info('Checking if segments are ready to connect')
        gpArray = confProvider.loadSystemConfig(useUtilityMode=True)
        segments = [seg for seg in gpArray.getDbList() if
                    seg.isSegmentUp() and not seg.isSegmentMaster() and not seg.isSegmentStandby()]
        for seg in segments:
            cmd = gp.SendFilerepTransitionStatusMessage(name='Get segment status',
                                                        msg=gp.SEGMENT_STATUS_GET_STATUS,
                                                        dataDir=seg.getSegmentDataDirectory(),
                                                        port=seg.getSegmentPort(),
                                                        ctxt=gp.REMOTE,
                                                        remoteHost=seg.getSegmentHostName())
            self.__pool.addCommand(cmd)
        self.__pool.join()

        for item in self.__pool.getCompletedItems():
            result = item.get_results()
            if 'segmentState: Ready' not in result.stderr and 'segmentState: ChangeTrackingDisabled' not in result.stderr:
                raise Exception('Not ready to connect to database %s' % result.stderr)

    """
    When a primary segment goes down and its mirror has not yet failed over to Change Tracking,
    If we try to start a transaction it will fail. This results in the python scripts which try
    to run queries return a confusing error message. The solution here is to use gp_primarymirror
    to check the status of all the primary segments and make sure they are in "Ready" state. If
    they are not, then we retry for a maximum of 5 times before giving up.
    """

    def _check_database_connection(self, confProvider):
        retry = 0
        MAX_RETRIES = 5
        while retry < MAX_RETRIES:
            try:
                self._check_segment_state_for_connection(confProvider)
            except Exception as e:
                self.logger.debug('Encountered error %s' % str(e))
                self.logger.info('Unable to connect to database. Retrying %s' % (retry + 1))
            else:
                return True
            retry += 1
            time.sleep(5)
        return False

    def check_segment_state_ready_for_recovery(self, segmentList, dbsMap):
        # Make sure gpArray and segments are in agreement on current state of system.
        # Make sure segment state is ready for recovery
        getVersionCmds = {}
        for seg in segmentList:
            if seg.isSegmentQD() == True:
                continue
            if seg.isSegmentModeInChangeLogging() == False:
                continue
            cmd = gp.SendFilerepTransitionStatusMessage(name="Get segment status information"
                                                        , msg=gp.SEGMENT_STATUS_GET_STATUS
                                                        , dataDir=seg.getSegmentDataDirectory()
                                                        , port=seg.getSegmentPort()
                                                        , ctxt=gp.REMOTE
                                                        , remoteHost=seg.getSegmentHostName()
                                                        )
            getVersionCmds[seg.getSegmentDbId()] = cmd
            self.__pool.addCommand(cmd)
        self.__pool.join()

        # We can not check to see if the command was successful or not, because gp_primarymirror always returns a non-zero result.
        # That is just the way gp_primarymirror was designed.

        segmentStates = {}
        for dbid in getVersionCmds:
            cmd = getVersionCmds[dbid]
            mode = None
            segmentState = None
            dataState = None
            try:
                lines = str(cmd.get_results().stderr).split("\n")
                while not lines[0].startswith('mode: '):
                    self.logger.info(lines.pop(0))
                mode = lines[0].split(": ")[1].strip()
                segmentState = lines[1].split(": ")[1].strip()
                dataState = lines[2].split(": ")[1].strip()
            except:
                self.logger.warning("Problem getting Segment state dbid = %s, results = %s." % (
                    str(dbid), str(cmd.get_results().stderr)))
                continue

            db = dbsMap[dbid]
            if gparray.ROLE_TO_MODE_MAP[db.getSegmentRole()] != mode:
                raise Exception(
                    "Inconsistency in catalog and segment Role/Mode. Catalog Role = %s. Segment Mode = %s." % (
                        db.getSegmentRole(), mode))
            if gparray.MODE_TO_DATA_STATE_MAP[db.getSegmentMode()] != dataState:
                raise Exception(
                    "Inconsistency in catalog and segment Mode/DataState. Catalog Mode = %s. Segment DataState = %s." % (
                        db.getSegmentMode(), dataState))
            if segmentState != gparray.SEGMENT_STATE_READY and segmentState != gparray.SEGMENT_STATE_CHANGE_TRACKING_DISABLED:
                if segmentState == gparray.SEGMENT_STATE_INITIALIZATION or segmentState == gparray.SEGMENT_STATE_IN_CHANGE_TRACKING_TRANSITION:
                    raise Exception(
                        "Segment is not ready for recovery dbid = %s, segmentState = %s. Retry recovery in a few moments" % (
                            str(db.getSegmentDbId()), segmentState))
                else:
                    raise Exception("Segment is in unexpected state. dbid = %s, segmentState = %s." % (
                        str(db.getSegmentDbId()), segmentState))

            segmentStates[dbid] = segmentState
        return segmentStates

    def run(self):
        if self.__options.parallelDegree < 1 or self.__options.parallelDegree > 64:
            raise ProgramArgumentValidationException(
                "Invalid parallelDegree provided with -B argument: %d" % self.__options.parallelDegree)

        self.__pool = WorkerPool(self.__options.parallelDegree)
        gpEnv = GpMasterEnvironment(self.__options.masterDataDirectory, True)

        # verify "where to recover" options
        optionCnt = 0
        if self.__options.newRecoverHosts is not None:
            optionCnt += 1
        if self.__options.recoveryConfigFile is not None:
            optionCnt += 1
        if self.__options.rebalanceSegments:
            optionCnt += 1
        if optionCnt > 1:
            raise ProgramArgumentValidationException("Only one of -i, -p, and -r may be specified")

        faultProberInterface.getFaultProber().initializeProber(gpEnv.getMasterPort())

        confProvider = configInterface.getConfigurationProvider().initializeProvider(gpEnv.getMasterPort())

        if not self._check_database_connection(confProvider):
            raise Exception('Unable to connect to database and start transaction')

        gpArray = confProvider.loadSystemConfig(useUtilityMode=False)

        self.check_segment_state_ready_for_recovery(gpArray.getSegDbList(), gpArray.getSegDbMap())

        if not gpArray.hasMirrors:
            raise ExceptionNoStackTraceNeeded(
                'GPDB Mirroring replication is not configured for this Greenplum Database instance.')

        # We have phys-rep/filerep mirrors.

        if self.__options.newRecoverHosts is not None:
            try:
                uniqueHosts = []
                for h in self.__options.newRecoverHosts.split(','):
                    if h.strip() not in uniqueHosts:
                        uniqueHosts.append(h.strip())
                self.__options.newRecoverHosts = uniqueHosts
            except Exception, ex:
                raise ProgramArgumentValidationException( \
                    "Invalid value for recover hosts: %s" % ex)

        # If it's a rebalance operation, make sure we are in an acceptable state to do that
        # Acceptable state is:
        #    - No segments down
        #    - No segments in change tracking or unsynchronized state
        if self.__options.rebalanceSegments:
            if len(gpArray.get_invalid_segdbs()) > 0:
                raise Exception("Down segments still exist.  All segments must be up to rebalance.")
            if len(gpArray.get_synchronized_segdbs()) != len(gpArray.getSegDbList()):
                raise Exception(
                    "Some segments are not yet synchronized.  All segments must be synchronized to rebalance.")

        # retain list of hosts that were existing in the system prior to getRecoverActions...
        # this will be needed for later calculations that determine whether
        # new hosts were added into the system
        existing_hosts = set(gpArray.getHostList())

        # figure out what needs to be done
        mirrorsUnableToBuild, mirrorBuilder = self.getRecoveryActionsBasedOnOptions(gpEnv, gpArray)

        if self.__options.outputSampleConfigFile is not None:
            # just output config file and done
            self.outputToFile(mirrorBuilder, gpArray, self.__options.outputSampleConfigFile)
            self.logger.info('Configuration file output to %s successfully.' % self.__options.outputSampleConfigFile)
        elif self.__options.rebalanceSegments:
            assert (isinstance(mirrorBuilder, GpSegmentRebalanceOperation))

            # Make sure we have work to do
            if len(gpArray.get_unbalanced_segdbs()) == 0:
                self.logger.info("No segments are running in their non-preferred role and need to be rebalanced.")
            else:
                self.displayRecovery(mirrorBuilder, gpArray)

                if self.__options.interactive:
                    self.logger.warn("This operation will cancel queries that are currently executing.")
                    self.logger.warn("Connections to the database however will not be interrupted.")
                    if not userinput.ask_yesno(None, "\nContinue with segment rebalance procedure", 'N'):
                        raise UserAbortedException()

                fullRebalanceDone = mirrorBuilder.rebalance()
                self.logger.info("******************************************************************")
                if fullRebalanceDone:
                    self.logger.info("The rebalance operation has completed successfully.")
                else:
                    self.logger.info("The rebalance operation has completed with WARNINGS."
                                     " Please review the output in the gprecoverseg log.")
                self.logger.info("There is a resynchronization running in the background to bring all")
                self.logger.info("segments in sync.")
                self.logger.info("Use gpstate -e to check the resynchronization progress.")
                self.logger.info("******************************************************************")

        elif len(mirrorBuilder.getMirrorsToBuild()) == 0 and not mirrorsUnableToBuild:
            self.logger.info('No segments to recover')
        else:
            mirrorBuilder.checkForPortAndDirectoryConflicts(gpArray)
            self.validate_heap_checksum_consistency(gpArray, mirrorBuilder)

            self.displayRecovery(mirrorBuilder, gpArray)
            self.__displayRecoveryWarnings(mirrorBuilder)

            if self.__options.interactive:
                if not userinput.ask_yesno(None, "\nContinue with segment recovery procedure", 'N'):
                    raise UserAbortedException()

            # sync packages
            current_hosts = set(gpArray.getHostList())
            new_hosts = current_hosts - existing_hosts
            if new_hosts:
                self.syncPackages(new_hosts)

            if not mirrorBuilder.buildMirrors("recover", gpEnv, gpArray):
                sys.exit(1)

            confProvider.sendPgElogFromMaster("Recovery of %d segment(s) has been started." % \
                                              len(mirrorBuilder.getMirrorsToBuild()), True)

            self.logger.info("******************************************************************")
            self.logger.info("Updating segments for resynchronization is completed.")
            self.logger.info("For segments updated successfully, resynchronization will continue in the background.")
            self.logger.info("Use  gpstate -s  to check the resynchronization progress.")
            self.logger.info("******************************************************************")

        sys.exit(0)

    def validate_heap_checksum_consistency(self, gpArray, mirrorBuilder):
        live_segments = [target.getLiveSegment() for target in mirrorBuilder.getMirrorsToBuild()]
        if len(live_segments) == 0:
            self.logger.info("No checksum validation necessary when there are no segments to recover.")
            return

        heap_checksum = HeapChecksum(gpArray, num_workers=len(live_segments), logger=self.logger)
        successes, failures = heap_checksum.get_segments_checksum_settings(live_segments)
        # go forward if we have at least one segment that has replied
        if len(successes) == 0:
            raise Exception("No segments responded to ssh query for heap checksum validation.")
        consistent, inconsistent, master_checksum_value = heap_checksum.check_segment_consistency(successes)
        if len(inconsistent) > 0:
            self.logger.fatal("Heap checksum setting differences reported on segments")
            self.logger.fatal("Failed checksum consistency validation:")
            for gpdb in inconsistent:
                segment_name = gpdb.getSegmentHostName()
                checksum = gpdb.heap_checksum
                self.logger.fatal("%s checksum set to %s differs from master checksum set to %s" %
                                  (segment_name, checksum, master_checksum_value))
            raise Exception("Heap checksum setting differences reported on segments")
        self.logger.info("Heap checksum setting is consistent between master and the segments that are candidates "
                         "for recoverseg")

    def cleanup(self):
        if self.__pool:
            self.__pool.haltWork()  # \  MPP-13489, CR-2572
            self.__pool.joinWorkers()  # > all three of these appear necessary
            self.__pool.join()  # /  see MPP-12633, CR-2252 as well

    # -------------------------------------------------------------------------

    @staticmethod
    def createParser():

        description = ("Recover a failed segment")
        help = [""]

        parser = OptParser(option_class=OptChecker,
                           description=' '.join(description.split()),
                           version='%prog version $Revision$')
        parser.setHelp(help)

        addStandardLoggingAndHelpOptions(parser, True)

        addTo = OptionGroup(parser, "Connection Options")
        parser.add_option_group(addTo)
        addMasterDirectoryOptionForSingleClusterProgram(addTo)

        addTo = OptionGroup(parser, "Recovery Source Options")
        parser.add_option_group(addTo)
        addTo.add_option("-i", None, type="string",
                         dest="recoveryConfigFile",
                         metavar="<configFile>",
                         help="Recovery configuration file")
        addTo.add_option("-o", None,
                         dest="outputSampleConfigFile",
                         metavar="<configFile>", type="string",
                         help="Sample configuration file name to output; "
                              "this file can be passed to a subsequent call using -i option")

        addTo = OptionGroup(parser, "Recovery Destination Options")
        parser.add_option_group(addTo)
        addTo.add_option("-p", None, type="string",
                         dest="newRecoverHosts",
                         metavar="<targetHosts>",
                         help="Spare new hosts to which to recover segments")

        addTo = OptionGroup(parser, "Recovery Options")
        parser.add_option_group(addTo)
        addTo.add_option('-F', None, default=False, action='store_true',
                         dest="forceFullResynchronization",
                         metavar="<forceFullResynchronization>",
                         help="Force full segment resynchronization")
        addTo.add_option("-B", None, type="int", default=16,
                         dest="parallelDegree",
                         metavar="<parallelDegree>",
                         help="Max # of workers to use for building recovery segments.  [default: %default]")
        addTo.add_option("-r", None, default=False, action='store_true',
                         dest='rebalanceSegments', help='Rebalance synchronized segments.')

        parser.set_defaults()
        return parser

    @staticmethod
    def createProgram(options, args):
        if len(args) > 0:
            raise ProgramArgumentValidationException("too many arguments: only options may be specified", True)
        return GpRecoverSegmentProgram(options)

    @staticmethod
    def mainOptions():
        """
        The dictionary this method returns instructs the simple_main framework
        to check for a gprecoverseg.pid file under MASTER_DATA_DIRECTORY to
        prevent the customer from trying to run more than one instance of
        gprecoverseg at the same time.
        """
        return {'pidfilename': 'gprecoverseg.pid', 'parentpidvar': 'GPRECOVERPID'}
