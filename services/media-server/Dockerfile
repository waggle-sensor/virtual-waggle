FROM golang:1.14 AS builder
WORKDIR /build
COPY go.mod main.go ./
RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /build/media-server

FROM alpine:latest
COPY --from=builder /build/media-server /media-server
EXPOSE 5000
ENTRYPOINT [ "/media-server" ]
CMD [ "-root", "/data" ]
