#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include "cmockery.h"

#include <poll.h>

static int poll_expected_return_value;

#define poll poll_mock

int poll_mock (struct pollfd * p1, nfds_t p2, int p3)
{
	return poll_expected_return_value;
}

static void poll_will_return(int expected_return_value)
{
	poll_expected_return_value = expected_return_value;
}

#include "postgres.h"

/* Actual function body */
#include "../ftsprobe.c"

static void write_log_will_be_called()
{
	expect_any(write_log, fmt);
	will_be_called(write_log);
}

static void probeTimeout_mock_timeout(ProbeConnectionInfo *info)
{
	/*
	 * set info->startTime to set proper elapse_ms
	 * (which is returned by inline function gp_seg_elapsed_ms()) to simulate
	 * timeout
	 */
	gp_fts_probe_timeout = 0;
	gp_set_monotonic_begin_time(&(info->startTime));
	pg_usleep(10); /* sleep to mock timeout */
	write_log_will_be_called();
}

static void probePollIn_mock_success(ProbeConnectionInfo *info)
{
	expect_any(PQsocket, conn);
	will_be_called(PQsocket);

	poll_will_return(1);
}


static void probePollIn_mock_timeout(ProbeConnectionInfo *info)
{
	expect_any(PQsocket, conn);
	will_be_called(PQsocket);

	/*
	 * Need poll() and errno to exercise probeTimeout()
	 */
	poll_will_return(0);
	probeTimeout_mock_timeout(info);

	write_log_will_be_called();
}

static void PQisBusy_will_return(bool expected_return_value)
{
	expect_any(PQisBusy, conn);
	will_return(PQisBusy, expected_return_value);
}

static void PQconsumeInput_will_return(int expected_return_value)
{
	expect_any(PQconsumeInput, conn);
	will_return(PQconsumeInput, expected_return_value);
}

static void PQerrorMessage_will_be_called()
{
	expect_any(PQerrorMessage, conn);
	will_be_called(PQerrorMessage);
}

static void PQgetResult_will_return(PGresult *expected_return_value)
{
	expect_any(PQgetResult, conn);
	will_return(PQgetResult, expected_return_value);
}

static void PQresultStatus_will_return(ExecStatusType expected_return_value)
{
	expect_any(PQresultStatus, res);
	will_return(PQresultStatus, expected_return_value);
}

static void PQclear_will_be_called()
{
	expect_any(PQclear, res);
	will_be_called(PQclear);
}

/*
 * Scenario: if primary didn't response in time to FTS probe, probeReceive on
 * master should fail.
 *
 * We are mocking the timeout behavior using probeTimeout().
 */
void
test_probeReceive_when_fts_handler_hung(void **state)
{
	ProbeConnectionInfo info;
	struct pg_conn conn;

	info.conn = &conn;

	PQisBusy_will_return(true);

	/*
	 * probePollIn() will return false by mocking probeTimeout()
	 */
	probePollIn_mock_timeout(&info);

	bool actual_return_value = probeReceive(&info);

	assert_false(actual_return_value);
}

/*
 * Scenario: if primary response FATAL to FTS probe, probeReceive on master
 * should fail due to PQconsumeInput() failed
 */
void
test_probeReceive_when_fts_handler_FATAL(void **state)
{
	ProbeConnectionInfo info;
	struct pg_conn conn;

	info.conn = &conn;

	PQisBusy_will_return(true);

	probePollIn_mock_success(&info);
	PQconsumeInput_will_return(0);

	write_log_will_be_called();
	PQerrorMessage_will_be_called();

	bool actual_return_value = probeReceive(&info);

	assert_false(actual_return_value);
}

/*
 * Scenario: if primary response ERROR to FTS probe, probeReceive on master
 * should fail due to PQresultStatus(lastResult) returned PGRES_FATAL_ERROR
 */
void
test_probeReceive_when_fts_handler_ERROR(void **state)
{
	ProbeConnectionInfo info;
	struct pg_conn conn;

	info.conn = &conn;

	PQisBusy_will_return(false);

	/*
	 * mock tmpResult to NULL, so that we break the for loop.
	 */
	PQgetResult_will_return(NULL);

	PQresultStatus_will_return(PGRES_FATAL_ERROR);
	PQclear_will_be_called();

	write_log_will_be_called();
	PQerrorMessage_will_be_called();

	bool actual_return_value = probeReceive(&info);

	assert_false(actual_return_value);
}

int
main(int argc, char* argv[])
{
	cmockery_parse_arguments(argc, argv);

	const UnitTest tests[] = {
		unit_test(test_probeReceive_when_fts_handler_hung),
		unit_test(test_probeReceive_when_fts_handler_FATAL),
		unit_test(test_probeReceive_when_fts_handler_ERROR),
	};
	return run_tests(tests);
}
