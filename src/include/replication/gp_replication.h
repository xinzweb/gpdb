/*-------------------------------------------------------------------------
 *
 * gp_replication.h
 *
 * Portions Copyright (c) 2012-Present Pivotal Software, Inc.
 *
 *
 * IDENTIFICATION
 *	    src/include/replication/gp_replication.h
 *
 *-------------------------------------------------------------------------
 */

#ifndef GPDB_GP_REPLICATION_H
#define GPDB_GP_REPLICATION_H

#include "postgres.h"
#include "fmgr.h"

extern void GetMirrorStatus(bool *IsMirrorUp, bool *IsInSync);
extern void SetSyncStandbysDefined(void);

extern Datum gp_replication_error(PG_FUNCTION_ARGS __attribute__((unused)) );

#endif
