#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include "cmockery.h"

#include "postgres.h"

#define probeWalRepUpdateConfig probeWalRepUpdateConfig_mock

static int16 expected_probeWalRepUpdateConfig_dbid;
static int16 expected_probeWalRepUpdateConfig_segindex;
static bool expected_probeWalRepUpdateConfig_isSegmentAlive;

void
probeWalRepUpdateConfig_mock(int16 dbid, int16 segindex, bool isSegmentAlive)
{
	assert_int_equal(dbid, expected_probeWalRepUpdateConfig_dbid);
	assert_int_equal(segindex, expected_probeWalRepUpdateConfig_segindex);
	assert_int_equal(isSegmentAlive, expected_probeWalRepUpdateConfig_isSegmentAlive);
}

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
mock_FtsIsActive(bool expected_return_value)
{
	static FtsProbeInfo fts_info;

	ftsProbeInfo = &fts_info;

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
	mock_FtsIsActive(false);

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
	shutdown_requested = true;
	mock_FtsIsActive(true);

	bool result = probeWalRepPublishUpdate(&context);

	/* restore the original value to let the rest of the test pass */
	shutdown_requested = false;

	assert_false(result);
}

static void
mock_primary_and_mirror_probe_response(
		probe_context *context,
		bool expected_isPrimaryAlive,
		bool expected_isMirrorAlive)
{
	static probe_response_per_segment response;
	static CdbComponentDatabaseInfo primary;
	static CdbComponentDatabases databases;
	static CdbComponentDatabaseInfo mirror;

	context->count = 1;
	context->responses = &response;

	/* mock primary UP */
	response.segment_db_info = &primary;
	primary.role = GP_SEGMENT_CONFIGURATION_ROLE_PRIMARY;
	primary.segindex = 1;
	primary.dbid = 1;
	primary.status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	/* mock FtsIsActive true */
	mock_FtsIsActive(true);

	/* mock mirror UP from FtsGetPeerSegment */
	cdb_component_dbs = &databases;

	databases.total_segment_dbs = 1;

	databases.segment_db_info = &mirror;
	mirror.role = GP_SEGMENT_CONFIGURATION_ROLE_MIRROR;
	mirror.segindex = primary.segindex;
	mirror.dbid = primary.dbid + 1;
	mirror.status = GP_SEGMENT_CONFIGURATION_STATUS_UP;

	response.result.isPrimaryAlive = expected_isPrimaryAlive;
	response.result.isMirrorAlive = expected_isMirrorAlive;

	if (!expected_isPrimaryAlive || !expected_isMirrorAlive)
	{
		/* mock xact functions */
		will_be_called(StartTransactionCommand);
		will_be_called(GetTransactionSnapshot);

		/* mock probeWalRepUpdateConfig */
		if(!expected_isPrimaryAlive)
		{
			expected_probeWalRepUpdateConfig_dbid = primary.dbid;
			expected_probeWalRepUpdateConfig_segindex = primary.segindex;
			expected_probeWalRepUpdateConfig_isSegmentAlive = response.result.isPrimaryAlive;
		}
		else if (!expected_isMirrorAlive)
		{
			expected_probeWalRepUpdateConfig_dbid = mirror.dbid;
			expected_probeWalRepUpdateConfig_segindex = mirror.segindex;
			expected_probeWalRepUpdateConfig_isSegmentAlive = response.result.isMirrorAlive;
		}
		else
		{
			/* never reachable */
			fail();
		}

		will_be_called(CommitTransactionCommand);
	}
}

/*
 *  Case: 1 segment, is_updated is false, because neither primary nor mirror
 * updated
 */
void
test_probeWalRepPublishUpdate_no_update(void **state)
{
	probe_context context;

	mock_primary_and_mirror_probe_response(
		&context,
		true /* expected_isPrimaryAlive */,
		true /* expected_isMirrorAlive */);

	bool result = probeWalRepPublishUpdate(&context);

	assert_false(result);
}

void
test_probeWalRepPublishUpdate_update_primary(void **state)
{
	probe_context context;

	mock_primary_and_mirror_probe_response(
		&context,
		false /* expected_isPrimaryAlive */,
		true /* expected_isMirrorAlive */);

	bool result = probeWalRepPublishUpdate(&context);

	assert_true(result);
}

void
test_probeWalRepPublishUpdate_update_mirror(void **state)
{
	probe_context context;

	mock_primary_and_mirror_probe_response(
			&context,
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

	MemoryContextInit();

	return run_tests(tests);
}
