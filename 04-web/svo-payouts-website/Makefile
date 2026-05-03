# Local smoke build (образ как в CI). Из корня репозитория:
#   make docker-build

.PHONY: docker-build
docker-build:
	docker build -f web/Dockerfile -t svo-site:local ./web
