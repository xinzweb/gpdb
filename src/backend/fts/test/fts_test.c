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
probeWalRepUpdateConfig_will_be_called_with(
		int16 dbid,
		int16 segindex,
		bool IsSegmentAlive)
{
	/* Mock heap_open gp_configuration_history_relation */
	static RelationData gp_configuration_history_relation;
	expect_value(heap_open, relationId, GpConfigHistoryRelationId);
	expect_any(heap_open, lockmode);
	will_return(heap_open, &gp_configuration_history_relation);

	/* Mock heap_open gp_segment_configuration_relation */
	static RelationData gp_segment_configuration_relation;
	expect_value(heap_open, relationId, GpSegmentConfigRelationId);
	expect_any(heap_open, lockmode);
	will_return(heap_open, &gp_segment_configuration_relation);

	/* Mock heap_form_tuple inline function */
	expect_any_count(heaptuple_form_to, tupleDescriptor, -1);
	expect_any_count(heaptuple_form_to, values, -1);
	expect_any_count(heaptuple_form_to, isnull, -1);
	expect_any_count(heaptuple_form_to, dst, -1);
	expect_any_count(heaptuple_form_to, dstlen, -1);
	will_be_called_count(heaptuple_form_to, -1);

	/* Mock simple_heap_insert */
	expect_any_count(simple_heap_insert, relation, -1);
	expect_any_count(simple_heap_insert, tup, -1);
	will_be_called_count(simple_heap_insert, -1);

	/* Mock CatalogUpdateIndexes */
	expect_any_count(CatalogUpdateIndexes, heapRel, -1);
	expect_any_count(CatalogUpdateIndexes, heapTuple, -1);
	will_be_called_count(CatalogUpdateIndexes, -1);

	/* Mock heap_close */
	expect_any_count(relation_close, relation, -1);
	expect_any_count(relation_close, lockmode, -1);
	will_be_called_count(relation_close, -1);

	/* Mock ScanKeyInit */
	expect_any_count(ScanKeyInit, entry, -1);
	expect_any_count(ScanKeyInit, attributeNumber, -1);
	expect_any_count(ScanKeyInit, strategy, -1);
	expect_any_count(ScanKeyInit, procedure, -1);
	expect_any_count(ScanKeyInit, argument, -1);
	will_be_called_count(ScanKeyInit, -1);

	/* Mock systable_beginscan */
	expect_any_count(systable_beginscan, heapRelation, -1);
	expect_any_count(systable_beginscan, indexId, -1);
	expect_any_count(systable_beginscan, indexOK, -1);
	expect_any_count(systable_beginscan, snapshot, -1);
	expect_any_count(systable_beginscan, nkeys, -1);
	expect_any_count(systable_beginscan, key, -1);
	will_be_called_count(systable_beginscan, -1);

	static HeapTupleData config_tuple;
	expect_any(systable_getnext, sysscan);
	will_return(systable_getnext, &config_tuple);

	HeapTuple new_tuple = palloc(sizeof(HeapTupleData));
	expect_any(heap_modify_tuple, tuple);
	expect_any(heap_modify_tuple, tupleDesc);
	expect_any(heap_modify_tuple, replValues);
	expect_any(heap_modify_tuple, replIsnull);
	expect_any(heap_modify_tuple, doReplace);
	will_return(heap_modify_tuple, new_tuple);

	expect_any_count(simple_heap_update, relation, -1);
	expect_any_count(simple_heap_update, otid, -1);
	expect_any_count(simple_heap_update, tup, -1);
	will_be_called_count(simple_heap_update, -1);

	expect_any_count(systable_endscan, sysscan, -1);
	will_be_called_count(systable_endscan, -1);
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
		probeWalRepUpdateConfig_will_be_called_with(
				primary.dbid,
				primary.segindex,
				response.result.isPrimaryAlive);

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
