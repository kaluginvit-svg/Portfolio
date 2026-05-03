# Сборка из каталога go-server: docker build -t go-server .
# Из корня репозитория: docker build -f go-server/Dockerfile -t go-server go-server
FROM golang:1.22-bookworm AS build

WORKDIR /src
COPY . .

RUN go mod tidy \
	&& CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags="-s -w" -o /userserver ./cmd/userserver

FROM alpine:3.19
RUN apk add --no-cache ca-certificates

WORKDIR /app
COPY --from=build /userserver /usr/local/bin/userserver

ENV DB_PATH=/app/data/users.db
ENV PASSWORDS_FILE=/app/data/passwords.txt

EXPOSE 8080

ENTRYPOINT ["/usr/local/bin/userserver"]
