#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include "cmockery.h"

/* Actual function body */
#include "../fts.c"

/* Case: 0 segment, is_updated is always false */
void
test_probeWalRepPublishUpdate_for_zero_segment(void **state)
{
	probe_context context;

	context.count = 0;

	bool result = probeWalRepPublishUpdate(&context);

	assert_false(result);
}

/* mock FtsIsActive */
void
mock_FtsIsActive(FtsProbeInfo *fts_info, bool expected_return_value)
{
	ftsProbeInfo = fts_info;
	if (shutdown_requested)
	{
		ftsProbeInfo->fts_discardResults = false;
	}
	else
	{
		ftsProbeInfo->fts_discardResults = !expected_return_value;
	}
}

/*
 * Case: 1 segment, is_updated is false, because FtsIsActive failed
 */
void
test_probeWalRepPublishUpdate_for_FtsIsActive_false(void **state)
{
	probe_context context;
	context.count = 1;
	probe_response_per_segment response;
	context.responses = &response;
	CdbComponentDatabaseInfo info;
	response.segment_db_info = &info;
	info.role = GP_SEGMENT_CONFIGURATION_ROLE_PRIMARY;

	/* mock FtsIsActive false */
	FtsProbeInfo fts_info;
	mock_FtsIsActive(&fts_info, false);

	bool result = probeWalRepPublishUpdate(&context);

	assert_false(result);
}

/*
 * Case: 1 segment, is_updated is false, because shutdown_requested is true.
 */
void
test_probeWalRepPublishUpdate_for_shutdown_requested(void **state)
{
	probe_context context;
	context.count = 1;
	probe_response_per_segment response;
	context.responses = &response;
	CdbComponentDatabaseInfo info;
	response.segment_db_info = &info;
	info.role = GP_SEGMENT_CONFIGURATION_ROLE_PRIMARY;

	/* mock FtsIsActive true */
	FtsProbeInfo fts_info;
	shutdown_requested = true;
	mock_FtsIsActive(&fts_info, true);

	bool result = probeWalRepPublishUpdate(&context);

	/* restore the original value to let the rest of the test pass */
	shutdown_requested = false;

	assert_false(result);
}

/*
 *  Case: 1 segment, is_updated is false, because neither primary nor mirror
 * updated
 */
void
test_probeWalRepPublishUpdate_no_update(void **state)
{
	probe_context context;
	context.count = 1;
	probe_response_per_segment response;
	context.responses = &response;

	/* mock primary */
	CdbComponentDatabaseInfo primary;
	response.segment_db_info = &primary;
	primary.role = GP_SEGMENT_CONFIGURATION_ROLE_PRIMARY;
	primary.segindex = 1;
	primary.dbid = 1;
	primary.status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	/* mock FtsIsActive true */
	FtsProbeInfo fts_info;
	mock_FtsIsActive(&fts_info, true);

	/* mock mirror from FtsGetPeerSegment */
	CdbComponentDatabases databases;
	cdb_component_dbs = &databases;

	databases.total_segment_dbs = 1;
	CdbComponentDatabaseInfo mirror;
	mirror.role = GP_SEGMENT_CONFIGURATION_ROLE_MIRROR;
	databases.segment_db_info = &mirror;
	mirror.segindex = primary.segindex;
	mirror.dbid = primary.dbid + 1;
	mirror.status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	response.result.isMirrorAlive = true;
	response.result.isPrimaryAlive = true;

	bool result = probeWalRepPublishUpdate(&context);

	assert_false(result);
}

static void
probeWalRepUpdateConfig_will_be_called_with(
	int16 dbid,
	int16 segindex,
	bool IsSegmentAlive)
{
	mock_probeWalRepUpdateConfig = true;
}

static void
mock_primary_and_mirror_probe_response(
	probe_context *context,
	probe_response_per_segment *response,
	FtsProbeInfo *fts_info,
	CdbComponentDatabases *databases,
	CdbComponentDatabaseInfo *primary,
	CdbComponentDatabaseInfo *mirror,
	bool expected_isPrimaryAlive,
	bool expected_isMirrorAlive)
{
	context->count = 1;
	context->responses = response;

	/* mock primary UP */
	response->segment_db_info = primary;
	primary->role = GP_SEGMENT_CONFIGURATION_ROLE_PRIMARY;
	primary->segindex = 1;
	primary->dbid = 1;
	primary->status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	/* mock FtsIsActive true */
	mock_FtsIsActive(fts_info, true);

	/* mock mirror UP from FtsGetPeerSegment */
	cdb_component_dbs = databases;

	databases->total_segment_dbs = 1;

	databases->segment_db_info = mirror;
	mirror->role = GP_SEGMENT_CONFIGURATION_ROLE_MIRROR;
	mirror->segindex = primary->segindex;
	mirror->dbid = primary->dbid + 1;
	mirror->status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	response->result.isPrimaryAlive = expected_isPrimaryAlive;
	response->result.isMirrorAlive = expected_isMirrorAlive;

	/* mock xact functions */
	will_be_called(StartTransactionCommand);
	will_be_called(GetTransactionSnapshot);

	/* mock probeWalRepUpdateConfig */
	probeWalRepUpdateConfig_will_be_called_with(
		primary->dbid,
		primary->segindex,
		response->result.isPrimaryAlive);

	will_be_called(CommitTransactionCommand);
}

void
test_probeWalRepPublishUpdate_update_primary(void **state)
{
	probe_context context;
	probe_response_per_segment response;
	FtsProbeInfo fts_info;
	CdbComponentDatabaseInfo primary;
	CdbComponentDatabases databases;
	CdbComponentDatabaseInfo mirror;

	mock_primary_and_mirror_probe_response(
		&context,
		&response,
		&fts_info,
		&databases,
		&primary,
		&mirror,
		false /* expected_isPrimaryAlive */,
		true /* expected_isMirrorAlive */);

	bool result = probeWalRepPublishUpdate(&context);

	assert_true(result);
}

void
test_probeWalRepPublishUpdate_update_mirror(void **state)
{
	probe_context context;
	probe_response_per_segment response;
	FtsProbeInfo fts_info;
	CdbComponentDatabaseInfo primary;
	CdbComponentDatabases databases;
	CdbComponentDatabaseInfo mirror;

	mock_primary_and_mirror_probe_response(
			&context,
			&response,
			&fts_info,
			&databases,
			&primary,
			&mirror,
			true /* expected_isPrimaryAlive */,
			false /* expected_isMirrorAlive */);

	bool result = probeWalRepPublishUpdate(&context);

	assert_true(result);
}

int
main(int argc, char* argv[])
{
	cmockery_parse_arguments(argc, argv);

	const UnitTest tests[] = {
		unit_test(test_probeWalRepPublishUpdate_for_zero_segment),
		unit_test(test_probeWalRepPublishUpdate_for_shutdown_requested),
		unit_test(test_probeWalRepPublishUpdate_for_FtsIsActive_false),
		unit_test(test_probeWalRepPublishUpdate_no_update),
		unit_test(test_probeWalRepPublishUpdate_update_primary),
		unit_test(test_probeWalRepPublishUpdate_update_mirror),
	};
	return run_tests(tests);
}
