BUILD_ROOT=../../../../../

.PHONY: docker
docker: docker-image

# VPN is required for enterprise build to work
docker-image: Dockerfile
	docker build --add-host releng.sanmateo.greenplum.com:10.110.112.79 --iidfile docker-image --tag ubuntu_ent_build:16.04 --file Dockerfile $(BUILD_ROOT)

.PHONY: debug-build
debug-build:
	docker run -it --net host --rm -v $$PWD/$(BUILD_ROOT):/root/gpdb pivotaldata/ubuntu-gpdb-dev:16.04_gcc_6_3 bash
