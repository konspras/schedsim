## Running a single simulation

`go build`

`./schedsim [OPTION...]`

### Options
* --topo: single queue (0), multi queue (1), bounded queue (2)
* --mu: service rate per core [reqs/us]
* --lambda: arrival rate [reqs/us]
* --cores: number of processor cores (default: 1)
* --genType: MM (0), MD (1), MB[90-10] (2), MB[99.9-0.1] (3)
* --procType: FIFO (0), Processor sharing (1), Time Sharing (2)
* --quantum: quantum for Time Sharing processor [us] (default: 10.0)
* --ctxCost: absolute context switch cost [us] (default: 0.0)
 
#### Examples
`./schedsim --topo=0 --mu=0.1 --lambda=0.005 --genType=2 --procType=0`

## genType Notation
[Kendall’s notation](https://en.wikipedia.org/wiki/Kendall%27s_notation):

A/S/c
* A denotes the time between arrivals to the queue
    * M: Poisson
    * D: fixed inter-arrival time
* S the service time distribution
    * M: Exponential
    * D: Fixed
    * L: Lognormal
    * B: Bimodal
* c the number of service channels open at the node

## Running for multiple arrival rates and configs

Add schedsim to path:

`export PATH="$PATH:${PWD}"` (from where schedsim is)

Example: 

`./scripts/run_new.py "single_queue"`
### Running for multiple arrival rates (generates CSV automatically)
`python3 ./scripts/run_many.py run --topo=0 --mu=0.1 --gen_type=1 --proc_type=0 --cores=10 --ctx_cost=0.0 --output_dir="results"`

### Running quantum sweep (generates CSV automatically)
`python3 ./scripts/run_many.py run_quantum --topo=0 --mu=0.1 --gen_type=1 --proc_type=2 --cores=10 --ctx_cost=0.0 --output_dir="results"`
