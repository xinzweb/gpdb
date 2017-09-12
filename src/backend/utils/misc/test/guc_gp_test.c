//
// Created by xzhang on 9/11/17.
//
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>

#include "cmockery.h"

#include "../guc_gp.c"

static void check_result (const char * expected_result);

void
test__gp_set_synchronous_standby_name_false(void **state)
{
	will_return(superuser, true);

	expect_any(LWLockAcquire, lockid);
	expect_any(LWLockAcquire, mode);
	will_be_called(LWLockAcquire);

	expect_any(LWLockRelease, lockid);
	will_be_called(LWLockRelease);

	gp_replication_config_filename = "/tmp/test_gp_replication.conf";

	gp_set_synchronous_standby_name(false);

	check_result("synchronous_standby_names = ''");
}

void
test__gp_set_synchronous_standby_name_true(void **state)
{
	will_return(superuser, true);

	expect_any(LWLockAcquire, lockid);
	expect_any(LWLockAcquire, mode);
	will_be_called(LWLockAcquire);

	expect_any(LWLockRelease, lockid);
	will_be_called(LWLockRelease);

	gp_replication_config_filename = "/tmp/test_gp_replication.conf";

	gp_set_synchronous_standby_name(true);

	check_result("synchronous_standby_names = '*'");
}

static void
check_result (const char * expected_result)
{
	FILE *fp;
	char *line = NULL;
	size_t len = 0;
	ssize_t read;
	bool found = false;

	fp = fopen(gp_replication_config_filename, "r");
	assert_true(fp);

	while ((read = getline(&line, &len, fp)) != -1)
	{
		if (strncmp(line, expected_result, strlen(expected_result)) == 0)
		{
			found = true;
			break;
		}
	}

	fclose(fp);
	if (line)
		free(line);

	assert_true(found);
}


int
main(int argc, char* argv[])
{
	cmockery_parse_arguments(argc, argv);

	const UnitTest tests[] = {
		unit_test(test__gp_set_synchronous_standby_name_false),
		unit_test(test__gp_set_synchronous_standby_name_true)
	};
	return run_tests(tests);
}