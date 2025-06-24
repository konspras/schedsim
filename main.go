package main

import (
	"flag"
	"fmt"

	"github.com/epfl-dcsl/schedsim/topologies"
)

func main() {
	var topo = flag.Int("topo", 0, "topology selector")
	var mu = flag.Float64("mu", 0.02, "mu service rate [reqs/us]") // default 50usec
	var lambda = flag.Float64("lambda", 0.005, "lambda poisson interarrival [reqs/us]")
	var genType = flag.Int("genType", 0, "type of generator")
	var procType = flag.Int("procType", 0, "type of processor")
	var duration = flag.Float64("duration", 10000000, "experiment duration [us]")
	var bufferSize = flag.Int("buffersize", 1, "size of the bounded buffer")
	var quantum = flag.Float64("quantum", 10.0, "time sharing processor quantum [us]")
	var cores = flag.Int("cores", 1, "number of processor cores")
	var ctxCost = flag.Float64("ctxCost", 0.0, "absolute context switch cost [us]")

	flag.Parse()
	fmt.Printf("Selected topology: %v\n", *topo)

	if *topo == 0 {
		topologies.SingleQueue(*lambda, *mu, *duration, *genType, *procType, *quantum, *cores, *ctxCost)
	} else if *topo == 1 {
		topologies.MultiQueue(*lambda, *mu, *duration, *genType, *procType, *cores, *ctxCost)
	} else if *topo == 2 {
		topologies.BoundedQueue(*lambda, *mu, *duration, *bufferSize, *cores)
	} else {
		panic("Unknown topology")
	}
}
