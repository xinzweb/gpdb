BUILD_ROOT=../../../../../

.PHONY: docker
docker: docker-image

docker-image: Dockerfile
	docker build --iidfile docker-image --tag ubuntu_ent_build:16.04 --file Dockerfile $(BUILD_ROOT)

.PHONY: debug-build
debug-build:
	docker run -it --rm -v $$PWD/$(BUILD_ROOT):/root/gpdb pivotaldata/ubuntu-gpdb-dev:16.04_gcc_6_3 bash
