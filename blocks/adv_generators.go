package blocks

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"strings"
)

// PBGenerator implements a playback generator for given service times.
// The interarrival distribution is exponential
type PBGenerator struct {
	genericGenerator
	// service times per CPU (discrete values)
	sTimes   [][]int
	cpuCount int
	WaitTime randDist
}

// NewPBGenerator returns a PBGenerator
// Parameters: lambda for the exponential interarrival and the filenames
// with the service times
func NewPBGenerator(lambda float64, paths []string) *PBGenerator {
	g := PBGenerator{}

	for _, p := range paths {
		inFile, _ := os.Open(p)
		defer inFile.Close()
		scanner := bufio.NewScanner(inFile)
		scanner.Split(bufio.ScanLines)

		newTimes := make([]int, 0)
		for scanner.Scan() {
			n, _ := strconv.Atoi(scanner.Text())
			newTimes = append(newTimes, n)
		}
		g.sTimes = append(g.sTimes, newTimes)
	}
	g.cpuCount = len(paths)
	g.WaitTime = newExponDistr(lambda)
	return &g
}

func (g *PBGenerator) Run() {
	for {
		i := rand.Intn(g.cpuCount)
		j := rand.Intn(len(g.sTimes[i]))
		serviceTime := g.sTimes[i][j]
		req := g.Creator.NewRequest(float64(serviceTime))
		g.WriteOutQueueI(req, i)
		g.Wait(g.WaitTime.getRand())
	}
}

// CDFGenerator implements a generator with CDF-based service times
// and exponential interarrival distribution. It assumes a single CDF source.
type CDFGenerator struct {
	genericGenerator
	// Single CDF distribution for sampling service times
	cdf      cdfDistrib
	WaitTime randDist
}

// cdfDistrib holds points of a cumulative distribution function for sampling
// x: service sizes; p: cumulative probabilities
type cdfDistrib struct {
	x []float64
	p []float64
}

// sample draws a service time by inverse-CDF interpolation
func (c *cdfDistrib) sample() float64 {
	u := rand.Float64()
	// fmt.Printf("NewCDFGenerator::sample() u = %f \n", u)
	// lower bound
	if u <= c.p[0] {
		return c.x[0]
	}
	// find interval and interpolate
	for i := 1; i < len(c.p); i++ {
		// fmt.Printf("p %f   x %f\n", c.p[i], c.x[i])
		if u <= c.p[i] {
			deltaP := c.p[i] - c.p[i-1]
			if deltaP <= 0 {
				// fmt.Printf("Returning c.x[i] %f\n", c.x[i])
				return c.x[i]
			}
			frac := (u - c.p[i-1]) / deltaP
			// fmt.Printf("Returning c.x[i-1] + frac %f\n", c.x[i-1]+frac*(c.x[i]-c.x[i-1]))
			return c.x[i-1] + frac*(c.x[i]-c.x[i-1])
		}
	}
	// fallback to max value
	var ret = c.x[len(c.x)-1]
	// fmt.Printf("Sample returns: %v\n", ret)
	return ret
}

// NewCDFGenerator returns a CDFGenerator
// Parameters: lambda for exponential interarrival and the path to a single CDF file.
// CDF file: first line is mean (ignored), subsequent lines: <size> <cumProb>
func NewCDFGenerator(lambda float64, path string) *CDFGenerator {
	if !(path != "") {
		panic("CDF path: '" + path + "' unknown, cannot create CDFGenerator")
	}
	g := CDFGenerator{}

	f, err := os.Open(path)
	if err != nil {
		panic(fmt.Sprintf("failed to open CDF file %s: %v", path, err))
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	scanner.Split(bufio.ScanLines)

	// skip mean line
	if !scanner.Scan() {
		panic(fmt.Sprintf("empty CDF file: %s", path))
	}

	// read CDF points
	var cd cdfDistrib
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}
		fields := strings.Fields(line)
		if len(fields) != 2 {
			panic(fmt.Sprintf("invalid CDF line '%s' in %s", line, path))
		}
		xVal, err := strconv.ParseFloat(fields[0], 64)
		if err != nil {
			panic(err)
		}

		pVal, err := strconv.ParseFloat(fields[1], 64)
		if err != nil {
			panic(err)
		}
		// xval is in bytes and should I feed it as us, the values will be very big
		// eg w5 goes to 10M+ which is 10 seconds (and starts at 1 byte==1us)
		// so I will divide by 10 (0.1us to 1s)
		// Or by 1000 (0.001us to 0.001s==1ms==1000us)
		cd.x = append(cd.x, xVal/100.0)
		cd.p = append(cd.p, pVal)
	}
	if len(cd.x) == 0 {
		panic(fmt.Sprintf("no CDF data in file: %s", path))
	}
	g.cdf = cd
	g.WaitTime = newExponDistr(lambda)
	return &g
}

// Run is the main loop of the CDFGenerator: sample a service time and wait
func (g *CDFGenerator) Run() {
	for {
		st := g.cdf.sample()
		req := g.Creator.NewRequest(st)
		g.WriteOutQueueI(req, 0)
		g.Wait(g.WaitTime.getRand())
	}
}
