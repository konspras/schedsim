package topologies

import (
	"fmt"

	"github.com/epfl-dcsl/schedsim/blocks"
	"github.com/epfl-dcsl/schedsim/engine"
)

// SingleQueue implement a single-generator-multiprocessor topology with a single
// queue. Each processor just dequeues from this queue
func SingleQueue(lambda, mu, duration float64,
	genType, procType int, quantum float64, cores int,
	ctxCost float64, path string) {

	engine.InitSim()

	//Init the statistics
	stats := &blocks.AllKeeper{}
	stats.SetName("Main Stats")
	engine.InitStats(stats)

	// Add generator
	var g blocks.Generator
	if genType == 0 {
		g = blocks.NewMMRandGenerator(lambda, mu)
	} else if genType == 1 {
		g = blocks.NewMDRandGenerator(lambda, 1/mu)
	} else if genType == 2 {
		g = blocks.NewMBRandGenerator(lambda, 1, 10*(1/mu-0.9), 0.9)
	} else if genType == 3 {
		g = blocks.NewMBRandGenerator(lambda, 1, 1000*(1/mu-0.999), 0.999)
	} else if genType == 4 {
		// Bimodal distribution calculated around the mean service time.
		// 90% of jobs are small, 10% are large.
		// Small jobs are 1/10th of the mean service time.
		// Large jobs are sized to preserve the overall mean.
		meanServiceTime := 1.0 / mu
		ratio := 0.9
		peak1 := meanServiceTime / 10.0
		// peak2 is derived from: mean = ratio * peak1 + (1-ratio) * peak2
		peak2 := (meanServiceTime - ratio*peak1) / (1.0 - ratio)
		fmt.Printf("Peak1: %v, Peak2: %v, Ratio: %v", peak1, peak2, ratio)
		g = blocks.NewMBRandGenerator(lambda, peak1, peak2, ratio)
	} else if genType == 5 {
		g = blocks.NewCDFGenerator(lambda, path)
	}

	g.SetCreator(&blocks.SimpleReqCreator{})

	// Create queues
	var q engine.QueueInterface
	if procType == 3 {
		q = blocks.NewPQueue()
	} else {
		q = blocks.NewQueue()
	}

	// Create processors

	if procType == 0 {
		for i := 0; i < cores; i++ {
			p := blocks.NewRTCProcessor(ctxCost)
			p.AddInQueue(q)
			p.SetReqDrain(stats)
			engine.RegisterActor(p)
		}
	} else if procType == 1 {
		p := blocks.NewPSProcessor()
		p.SetWorkerCount(cores)
		p.AddInQueue(q)
		p.SetReqDrain(stats)
		engine.RegisterActor(p)
	} else if procType == 2 {
		for i := 0; i < cores; i++ {
			p := blocks.NewTSProcessor(quantum, ctxCost)
			p.AddInQueue(q)
			p.SetReqDrain(stats)
			engine.RegisterActor(p)
		}
	} else if procType == 3 { // SRPT
		for i := 0; i < cores; i++ {
			p := blocks.NewSrptTSProcessor(quantum, ctxCost)
			p.AddInQueue(q)
			p.SetReqDrain(stats)
			engine.RegisterActor(p)
		}
	}

	g.AddOutQueue(q)

	// Register the generator
	engine.RegisterActor(g)

	fmt.Printf("Cores:%v\tservice_rate:%v\tinterarrival_rate:%v", cores, mu, lambda)
	if procType == 2 || procType == 3 {
		fmt.Printf("\tquantum:%v", quantum)
	}
	fmt.Println()
	engine.Run(duration)
}
