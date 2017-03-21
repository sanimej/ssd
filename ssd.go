package main

import (
	"context"
	"fmt"
	"os"

	"github.com/docker/docker/client"
)

func main() {
	cli, err := client.NewEnvClient()
	if err != nil {
		panic(err)
	}

	nw, _, err := cli.NetworkInspectWithRaw(context.Background(), os.Args[1], true)
	if err != nil {
		panic(err)
	}
	for s, _ := range nw.Services {
		fmt.Println(s)
	}
}
