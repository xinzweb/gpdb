import os
import sys
import tempfile

from StringIO import StringIO

from commands.base import CommandResult
from commands.gp import GpReadConfig
from gparray import Segment, GpArray, SegmentPair
import shutil
from mock import *
from gp_unittest import *

from gphostcache import GpHost

class GpConfig(GpTestCase):
    def setUp(self):

        self.gparray = self.createGpArrayWith2Primary2Mirrors()
        self.host_cache = Mock()

    def createGpArrayWith2Primary2Mirrors(self):
        master = Segment.initFromString(
            "1|-1|p|p|s|u|mdw|mdw|5432|/data/master")
        primary0 = Segment.initFromString(
            "2|0|p|p|s|u|sdw1|sdw1|40000|/data/primary0")
        primary1 = Segment.initFromString(
            "3|1|p|p|s|u|sdw2|sdw2|40001|/data/primary1")
        mirror0 = Segment.initFromString(
            "4|0|m|m|s|u|sdw2|sdw2|50000|/data/mirror0")
        mirror1 = Segment.initFromString(
            "5|1|m|m|s|u|sdw1|sdw1|50001|/data/mirror1")
        return GpArray([master, primary0, primary1, mirror0, mirror1])

    def test_GpReadConfig_creates_command_string(self):
        seg = self.gparray.master
        seg = self.gparray.master
        args = dict(name="my_command",
                    host="host",
                    seg=seg,
                    guc_name="statement_mem",)
        subject = GpReadConfig(**args)

        self.assertEquals(subject.cmdStr, "/bin/cat /data/master/postgresql.conf")

    @patch("gppylib.commands.base.Command.__init__", create=False)
    @patch("gppylib.commands.base.Command.get_results", return_value=CommandResult(0, "#statement_mem = 100\nstatement_mem = 200", "", True, False))
    @patch("gppylib.commands.base.Command.run")
    def test_GpReadConfig_returns_selected_guc(self, mock_run, mock_results, mock_init):
        seg = self.gparray.master
        args = dict(name="my_command",
                    host="host",
                    seg=seg,
                    guc_name="statement_mem",
        )

        subject = GpReadConfig(**args)

        subject.run(validateAfter=True)
        self.assertEquals('200', subject.get_guc_value())

    @patch("gppylib.commands.base.Command.__init__", create=False)
    @patch("gppylib.commands.base.Command.get_results", return_value=CommandResult(0, "statement_mem=100\n statement_mem=200 #blah", "", True, False))
    @patch("gppylib.commands.base.Command.run")
    def test_GpReadConfig_returns_selected_guc_with_whitespace_before_key(self, mock_run, mock_results, mock_init):
        seg = self.gparray.master
        args = dict(name="my_command",
                    host="host",
                    seg=seg,
                    guc_name="statement_mem",
        )

        subject = GpReadConfig(**args)

        subject.run(validateAfter=True)
        self.assertEquals('200', subject.get_guc_value())


if __name__ == '__main__':
    run_tests()
