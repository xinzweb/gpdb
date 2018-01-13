-- This test assumes 3 primaries and 3 mirrors from a gpdemo segwalrep cluster

-- start_ignore
create language plpythonu;
-- end_ignore

create or replace function pg_ctl(datadir text, command text, port int, contentid int)
returns text as $$
    import subprocess

    cmd = 'pg_ctl -D %s ' % datadir
    if command in ('stop', 'restart'):
        cmd = cmd + '-w -m immediate %s' % command
    elif command == 'start':
        opts = '-p %d -\-gp_dbid=0 -\-silent-mode=true -i -M mirrorless -\-gp_contentid=%d -\-gp_num_contents_in_cluster=3' % (port, contentid)
        cmd = cmd + '-o "%s" start' % opts
    elif command == 'reload':
        cmd = cmd + 'reload'
    else:
        return 'Invalid command input'

    return subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True).replace('.', '')
$$ language plpythonu;

-- make sure we are in-sync for the primary we will be testing with
select content, role, preferred_role, mode, status from gp_segment_configuration where content=2;

-- print synchronous_standby_names should be set to '*' at start of test
2U: show synchronous_standby_names;

-- create table and show commits are not blocked
create table segwalrep_commit_blocking (a int) distributed by (a);
insert into segwalrep_commit_blocking values (1);

-- WALREP_FIXME: we don't wait for the GUC to propagate to the ftsprobe process; it's
-- possible that one final probe could get through after we shut down the mirror
-- in the next line and throw off the test (since if the mirror is marked down,
-- the primary won't block). As a temporary nasty hack, try to reduce possible
-- flake by issuing a probe manually, which will delay the next one by a minute.
select gp_request_fts_probe_scan();

-- turn off fts
! gpconfig -c gp_fts_probe_pause -v true --masteronly --skipvalidation;
1U: select pg_ctl((select datadir from gp_segment_configuration c where c.role='p' and c.content=-1), 'reload', NULL, NULL);

-- stop a mirror and show commit on dbid 2 will block
1U: select pg_ctl((select datadir from gp_segment_configuration c where c.role='m' and c.content=0), 'stop', NULL, NULL);
2U&: insert into segwalrep_commit_blocking values (1);

-- restart primary dbid 2
1U: select pg_ctl((select datadir from gp_segment_configuration c where c.role='p' and c.content=0), 'restart', NULL, NULL);

-- should show dbid 2 utility mode connection closed because of primary restart
2U<:
2Uq:

-- synchronous_standby_names should be set to '*' after primary restart
2U: show synchronous_standby_names;

-- this should block since mirror is not up and sync replication is on
3: begin;
3: insert into segwalrep_commit_blocking values (1);
3&: commit;

-- this should not block due to direct dispatch to primary with active synced mirror
4: insert into segwalrep_commit_blocking values (3);

-- bring the mirror back up
1U: select pg_ctl((select datadir from gp_segment_configuration c where c.role='m' and c.content=0), 'start', (select port from gp_segment_configuration where content = 0 and preferred_role = 'm'), 0);

-- should unblock and commit now that mirror is back up and in-sync
3<:

-- turn on fts
! gpconfig -c gp_fts_probe_pause -v false --masteronly --skipvalidation;
1U: select pg_ctl((select datadir from gp_segment_configuration c where c.role='p' and c.content=-1), 'reload', NULL, NULL);

-- everything should be back to normal
4: insert into segwalrep_commit_blocking select i from generate_series(1,10)i;
4: select * from segwalrep_commit_blocking order by a;
