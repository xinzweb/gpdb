#!/usr/bin/env bash

export ivyrepo_host=repo.pivotal.io
export ivyrepo_user=build_readonly
export ivyrepo_passwd="J3sFcOJ6VXbH3zqp"

curl -u${ivyrepo_user}:${ivyrepo_passwd} -O "https://${ivyrepo_host}/gpdb-ext-release-local/emc/DDBoostSDK/3.3.0.4-550644/targzs/DDBoostSDK-rhel5_x86_64-3.3.0.4-550644.targz"
