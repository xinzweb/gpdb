/*-------------------------------------------------------------------------
 *
 * autovacuum.h
 *	  header file for integrated autovacuum daemon
 *
 *
 * Portions Copyright (c) 1996-2009, PostgreSQL Global Development Group
 * Portions Copyright (c) 1994, Regents of the University of California
 *
 * $PostgreSQL: pgsql/src/include/postmaster/autovacuum.h,v 1.15 2009/01/01 17:24:01 momjian Exp $
 *
 *-------------------------------------------------------------------------
 */
#ifndef AUTOVACUUM_H
#define AUTOVACUUM_H

#include "storage/lock.h"
#include "tcop/utility.h"

/* GUC variables */
extern bool autovacuum_start_daemon;
extern int	autovacuum_max_workers;
extern int	autovacuum_naptime;
extern int	autovacuum_vac_thresh;
extern double autovacuum_vac_scale;
extern int	autovacuum_anl_thresh;
extern double autovacuum_anl_scale;
extern int	autovacuum_freeze_max_age;
extern int	autovacuum_vac_cost_delay;
extern int	autovacuum_vac_cost_limit;

/* autovacuum launcher PID, only valid when worker is shutting down */
extern int	AutovacuumLauncherPid;

extern int	Log_autovacuum_min_duration;

/* Status inquiry functions */
extern bool AutoVacuumingActive(void);
extern bool IsAutoVacuumLauncherProcess(void);
extern bool IsAutoVacuumWorkerProcess(void);
extern Oid GetAutoVacuumTemplate0DbId(void);

/* Functions to start autovacuum process, called from postmaster */
extern void autovac_init(void);
extern int	autovac_start(void);  // OLD interface
extern void autovac_stopped(void);  // OLD interface
extern int	StartAutoVacLauncher(void);
extern int	StartAutoVacWorker(void);

/* called from postmaster when a worker could not be forked */
extern void AutoVacWorkerFailed(void);

/* autovacuum cost-delay balancer */
extern void AutoVacuumUpdateDelay(void);

#ifdef EXEC_BACKEND
extern void AutoVacMain(int argc, char *argv[]); // OLD interface
extern void AutovacuumIAm(void);
extern void AutoVacLauncherMain(int argc, char *argv[]);
extern void AutoVacWorkerMain(int argc, char *argv[]);
extern void AutovacuumWorkerIAm(void);
extern void AutovacuumLauncherIAm(void);
#endif

/* shared memory stuff */
extern Size AutoVacuumShmemSize(void);
extern void AutoVacuumShmemInit(void);

#endif   /* AUTOVACUUM_H */
