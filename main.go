package main

import (
	"flag"
	"fmt"

	"github.com/epfl-dcsl/schedsim/topologies"
)

func GetWorkloadPath(wl string) string {
	fmt.Printf("GetWorkloadPath(): Workload: %v\n", wl)
	switch wl {
	case "":
		return ""
	case "w3":
		return "homa-size-distributions/Google_AllRPC.txt"
	case "w4":
		return "homa-size-distributions/Facebook_HadoopDist_All.txt"
	case "w5":
		return "homa-size-distributions/DCTCP_MsgSizeDistBytes.txt"
	case "GPT3B":
		return "homa-size-distributions/GPT3B.txt"
	case "GPT3_adel":
		return "homa-size-distributions/GPT3_Adel.txt"
	default:
		panic("Unknown workload: " + wl)
	}
}

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
	var cdfWorkload = flag.String("cdfWorkload", "", "path to CDF workload file to draw processing times")

	flag.Parse()

	var path = GetWorkloadPath(*cdfWorkload)
	fmt.Printf("Workload path: %v\n", path)

	fmt.Printf("Selected topology: %v\n", *topo)

	if *topo == 0 {
		topologies.SingleQueue(*lambda, *mu, *duration, *genType, *procType, *quantum, *cores, *ctxCost, path)
	} else if *topo == 1 {
		topologies.MultiQueue(*lambda, *mu, *duration, *genType, *procType, *quantum, *cores, *ctxCost)
	} else if *topo == 2 {
		topologies.BoundedQueue(*lambda, *mu, *duration, *bufferSize, *cores)
	} else {
		panic("Unknown topology")
	}
}
