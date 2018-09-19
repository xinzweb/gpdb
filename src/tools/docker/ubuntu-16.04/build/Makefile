BUILD_ROOT=../../../../../

.PHONY: build
build: dist

.PHONY: apt
apt: Dockerfile_apt
	docker build --tag ubuntu_ent_build:16.04_apt --file Dockerfile_apt $(BUILD_ROOT)

.PHONY: orca
orca: Dockerfile_orca
	docker build --tag ubuntu_ent_build:16.04_orca --file Dockerfile_orca $(BUILD_ROOT)

.PHONY: dist
dist: Dockerfile_dist
	docker build --tag ubuntu_ent_build:16.04_dist --file Dockerfile_dist $(BUILD_ROOT)

.PHONY: mkpgbouncer
mkpgbouncer: Dockerfile_mkpgbouncer
	docker build --tag ubuntu_ent_build:16.04_mkpgbouncer --file Dockerfile_mkpgbouncer $(BUILD_ROOT)

.PHONY: mkpgbench
mkpgbench: Dockerfile_mkpgbench
	docker build --tag ubuntu_ent_build:16.04_mkpgbench --file Dockerfile_mkpgbench $(BUILD_ROOT)

.PHONY: copydocs
copydocs: Dockerfile_copydocs
	docker build --tag ubuntu_ent_build:16.04_copydocs --file Dockerfile_copydocs $(BUILD_ROOT)

.PHONY: copylibs
copylibs: Dockerfile_copylibs
	docker build --tag ubuntu_ent_build:16.04_copylibs --file Dockerfile_copylibs $(BUILD_ROOT)

