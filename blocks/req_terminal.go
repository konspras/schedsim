package blocks

import (
	"fmt"
	"math"
	"sort"

	"github.com/epfl-dcsl/schedsim/engine"
)

const (
	bUCKETCOUNT = 100000
	gRANULARITY = 0.01
)

// RequestDrain describes the behaviour of a the element that receives a request
// after processor serving and is in charge of keeping the statistics
type RequestDrain interface {
	TerminateReq(r engine.ReqInterface)
	SetName(name string)
}

// RequestData stores the service time and delay for a single request.
type RequestData struct {
	ServiceTime float64
	Delay       float64
}

// AllKeeper implements the RequestDrain interface and caclulates statistics
// on all the given requests, without sampling
type AllKeeper struct {
	items       []RequestData // Changed to store RequestData
	name        string
	stolenCount int
}

// TerminateReq is the function called by the processor after finishing
// request processing
func (k *AllKeeper) TerminateReq(req engine.ReqInterface) {
	delay := req.GetDelay()

	// Default to remaining service time for backward compatibility
	var serviceTime float64
	// Check if the request has an original service time we can get.
	if reqWithOriginalTime, ok := req.(OriginalServiceTimeGetter); ok {
		serviceTime = reqWithOriginalTime.GetOriginalServiceTime()
	} else {
		// Fallback for older request types that don't track original time
		serviceTime = req.GetServiceTime()
	}

	k.items = append(k.items, RequestData{ServiceTime: serviceTime, Delay: delay})
	if stealable, ok := req.(*StealableReq); ok {
		if stealable.stolen {
			k.stolenCount++
		}
	}
}

// SetName gives a name to the particular AllKeeper
func (k *AllKeeper) SetName(name string) {
	k.name = name
}

func (k *AllKeeper) avg() float64 {
	tmp := 0.0
	for _, item := range k.items {
		tmp += item.Delay // Operate on Delay
	}
	return tmp / float64(len(k.items))
}

func (k *AllKeeper) std() float64 {
	tmp := 0.0
	for _, item := range k.items {
		tmp += item.Delay * item.Delay // Operate on Delay
	}
	return math.Sqrt((tmp/float64(len(k.items)) - k.avg()))
}

func (k *AllKeeper) getPercentiles() map[float64]float64 {
	res := make(map[float64]float64)
	// Create a temporary slice of delays to sort for percentiles
	delays := make([]float64, len(k.items))
	for i, item := range k.items {
		delays[i] = item.Delay
	}
	sort.Float64s(delays)

	for _, v := range []float64{0.5, 0.9, 0.95, 0.99} {
		idx := int(float64(len(delays)) * v)
		if idx >= len(delays) {
			idx = len(delays) - 1
		} // Handle edge case for 99th percentile if few items
		res[v] = delays[idx]
	}
	return res
}

func (k *AllKeeper) slowdownAvg() float64 {
	var sum float64
	for _, item := range k.items {
		sum += item.Delay / item.ServiceTime
	}
	return sum / float64(len(k.items))
}

func (k *AllKeeper) slowdownStd() float64 {
	avg := k.slowdownAvg()
	var sumSq float64
	for _, item := range k.items {
		d := item.Delay / item.ServiceTime
		sumSq += (d - avg) * (d - avg)
	}
	return math.Sqrt(sumSq / float64(len(k.items)))
}

func (k *AllKeeper) slowdownPercentiles() map[float64]float64 {
	// collect all slowdowns
	slows := make([]float64, len(k.items))
	for i, item := range k.items {
		slows[i] = item.Delay / item.ServiceTime
	}
	sort.Float64s(slows)

	res := make(map[float64]float64)
	for _, p := range []float64{0.5, 0.9, 0.95, 0.99} {
		idx := int(float64(len(slows)) * p)
		if idx >= len(slows) {
			idx = len(slows) - 1
		}
		res[p] = slows[idx]
	}
	return res
}

// PrintStats prints the collected statistics at the end of the similation.
// This is called by the model
func (k *AllKeeper) PrintStats() {
	fmt.Printf("Stats collector: %v\n", k.name)
	// header for delay
	fmt.Printf("Count\tStolen\tAVG\tSTDDev\t50th\t90th\t95th\t99th\tReqs/time_unit\n")

	// delay row
	fmt.Printf("%d\t%d\t%v\t%v\t",
		len(k.items), k.stolenCount, k.avg(), k.std(),
	)
	if len(k.items) > 0 {
		pct := k.getPercentiles()
		for _, p := range []float64{0.5, 0.9, 0.95, 0.99} {
			fmt.Printf("%v\t", pct[p])
		}
	}
	fmt.Printf("%v\n", float64(len(k.items))/engine.GetTime())

	// slowdown header & row
	fmt.Printf("Slowdown\t\t%v\t%v\t", k.slowdownAvg(), k.slowdownStd())
	if len(k.items) > 0 {
		spct := k.slowdownPercentiles()
		for _, p := range []float64{0.5, 0.9, 0.95, 0.99} {
			fmt.Printf("%v\t", spct[p])
		}
	}
	fmt.Println() // end slowdown row

	k.PrintDetailedLatencyVsServiceTime()
}

// PrintDetailedLatencyVsServiceTime prints each request's service time and delay.
func (k *AllKeeper) PrintDetailedLatencyVsServiceTime() {
	fmt.Println("---DETAILED_LATENCY_VS_SERVICE_TIME_DATA_START---")
	fmt.Println("ServiceTime,Delay") // CSV header
	for _, item := range k.items {
		fmt.Printf("%v,%v\n", item.ServiceTime, item.Delay)
	}
	fmt.Println("---DETAILED_LATENCY_VS_SERVICE_TIME_DATA_END---")
}

// MonitorKeeper keeps statistics about queue lengths
type MonitorKeeper struct {
	delays   []float64
	initLen  []int
	finalLen []int
	name     string
}

// TerminateReq is the function called by the processor after finishing
// request processing
func (k *MonitorKeeper) TerminateReq(req engine.ReqInterface) {
	k.delays = append(k.delays, req.GetDelay())

	if monitorReq, ok := req.(*MonitorReq); ok {
		k.initLen = append(k.initLen, monitorReq.getInitLen())
		k.finalLen = append(k.finalLen, monitorReq.getFinalLen())
	}
}

// PrintStats prints the collected statistics at the end of the similation.
// This is called by the model
func (k *MonitorKeeper) PrintStats() {
	fmt.Println("#Latency\tEntrace Queue\tExit Queue")
	for idx, d := range k.delays {
		fmt.Printf("%v\t%v\t%v\n", d, k.initLen[idx], k.finalLen[idx])
	}
}

// SetName gives a name to the particular AllKeeper
func (k *MonitorKeeper) SetName(name string) {
	k.name = name
}

type histogram struct {
	granularity float64
	buckets     []int
	count       int64
	minBucket   int
	maxBucket   int
	sum         float64
	sumSquare   float64
}

func newHistogram() *histogram {
	return &histogram{
		granularity: gRANULARITY,
		buckets:     make([]int, bUCKETCOUNT),
		minBucket:   bUCKETCOUNT - 1,
		maxBucket:   0,
	}
}

func (hdr *histogram) addSample(s float64) {
	index := int(s / hdr.granularity)
	if index >= bUCKETCOUNT {
		index = bUCKETCOUNT - 1
	}
	if index < 0 || index >= bUCKETCOUNT {
		panic(fmt.Sprintf("Wrong index: %v\n", index))
	}
	hdr.buckets[index]++
	if index > hdr.maxBucket {
		hdr.maxBucket = index
	}
	if index < hdr.minBucket {
		hdr.minBucket = index
	}
	hdr.count++
	hdr.sum += s
	hdr.sumSquare += s * s
}

func (hdr *histogram) avg() float64 {
	return hdr.sum / float64(hdr.count)
}

func (hdr *histogram) stddev() float64 {
	squareAvg := hdr.sumSquare / float64(hdr.count)
	mean := hdr.avg()

	return math.Sqrt(squareAvg - mean*mean)
}

// FIXME: I assume that in every bucket there will be max one percentile
func (hdr *histogram) getPercentiles() map[float64]float64 {
	accum := make([]int, bUCKETCOUNT)
	res := map[float64]float64{}
	percentiles := []float64{0.5, 0.9, 0.95, 0.99}
	percentileI := 0

	accum[hdr.minBucket] = hdr.buckets[hdr.minBucket]

	// what if percentiles in the first bucket
	for float64(accum[hdr.minBucket]) > percentiles[percentileI]*float64(hdr.count) {
		// linear interpolation
		res[percentiles[percentileI]] = hdr.granularity / float64(hdr.buckets[hdr.minBucket]) * (percentiles[percentileI] * float64(hdr.count))
		percentileI++
	}
	if percentileI >= len(percentiles) {
		return res
	}

	for i := hdr.minBucket + 1; i <= hdr.maxBucket; i++ {
		accum[i] = accum[i-1] + hdr.buckets[i]
		for float64(accum[i]) > percentiles[percentileI]*float64(hdr.count) {
			// linear interpolation
			down := hdr.granularity * float64(i-1)

			res[percentiles[percentileI]] = down + hdr.granularity/float64(hdr.buckets[i])*(percentiles[percentileI]*float64(hdr.count)-float64(accum[i-1]))
			percentileI++
			if percentileI >= len(percentiles) {
				return res
			}
		}
	}
	return res
}

func (hdr *histogram) printPercentiles() {
	percentiles := hdr.getPercentiles()
	vals := []float64{0.5, 0.9, 0.95, 0.99}
	for _, v := range vals {
		fmt.Printf("%vth: %v\t", int(v*100.0), percentiles[v])
	}
	fmt.Println()

	fmt.Printf("Req/time_unit:%v\n", float64(hdr.count)/engine.GetTime())
}

// BookKeeper uses buckets to keep the information
type BookKeeper struct {
	hdr  *histogram
	name string
}

// NewBookKeeper returns a new *BookKeeper
func NewBookKeeper() *BookKeeper {
	return &BookKeeper{
		hdr: newHistogram(),
	}
}

// SetName gives a name to the particular AllKeeper
func (b *BookKeeper) SetName(name string) {
	b.name = name
}

// TerminateReq is the function called by the processor after finishing
// request processing
func (b *BookKeeper) TerminateReq(req engine.ReqInterface) {
	d := req.GetDelay()
	b.hdr.addSample(d)
}

// PrintStats prints the collected statistics at the end of the similation.
// This is called by the model
func (b *BookKeeper) PrintStats() {
	fmt.Printf("Stats collector: %v\n", b.name)
	fmt.Printf("Count\tAVG\tSTDDev\t50th\t90th\t95th\t99th Reqs/time_unit\n")
	fmt.Printf("%v\t%v\t%v\t", b.hdr.count, b.hdr.avg(), b.hdr.stddev())

	vals := []float64{0.5, 0.9, 0.95, 0.99}
	percentiles := b.hdr.getPercentiles()
	for _, v := range vals {
		fmt.Printf("%v\t", percentiles[v])
	}
	fmt.Printf("%v\n", float64(b.hdr.count)/engine.GetTime())
}
