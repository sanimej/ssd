FROM golang:1.7
RUN git clone https://github.com/docker/docker.git /go/src/github.com/docker/docker/
ADD ssd.go /
RUN go build /ssd.go
ENTRYPOINT ["./ssd"]
