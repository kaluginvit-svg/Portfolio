# Registry на VPS (подставь IP или домен своего сервера)
VPS_HOST ?= 155.212.174.153
REGISTRY ?= $(VPS_HOST):5000
IMAGE_NAME ?= myapp
VERSION ?= 1.0.0
FULL_IMAGE = $(REGISTRY)/$(IMAGE_NAME)

.PHONY: build push login

# Сборка образа с тегами: версия и latest
build:
	docker build -t $(FULL_IMAGE):$(VERSION) -t $(FULL_IMAGE):latest .

# Пуш образа с тегами версия и latest
push: build
	docker push $(FULL_IMAGE):$(VERSION)
	docker push $(FULL_IMAGE):latest

# Авторизация в Registry на VPS
# Логин/пароль — те, что настроены в registry (htpasswd или ваш способ)
login:
	docker login $(REGISTRY)

# Примеры:
#   make login VPS_HOST=192.168.1.10
#   make push VPS_HOST=registry.mydomain.com
# Если registry по HTTP (без HTTPS), добавь в /etc/docker/daemon.json:
#   "insecure-registries": ["vps-ip:5000"]
