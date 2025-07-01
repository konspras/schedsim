from dataclasses import dataclass, asdict
from typing import Optional
import os
from enum import Enum, auto

metrics = ['Count', 'Stolen', 'AVG', 'STDDev',
           '50th', '90th', '95th', '99th', 'Reqs/time_unit']


class SweepType(Enum):
    LOAD_SWEEP = auto()
    QUANTUM_SWEEP = auto()

class Defaults:
    topo: int = 0
    load_level: float = 0.5
    lmd: float = 0.005
    mu: float = 0.1
    gen_type: int = 1
    proc_type: int = 2
    cores: int = 1
    ctx_cost: float = 0.0
    output_dir: str = "results/"
    duration: int = 20000000
    quantum_us: float = 10.0
    sweep_type: SweepType = SweepType.LOAD_SWEEP



@dataclass
class SimParams:
    topo: int
    mu: float
    gen_type: int
    proc_type: int
    cores: int
    ctx_cost: float
    # Not always known by CLI user
    load_level: Optional[float] = None
    lmd: Optional[float] = None
    sweep_type: Optional[SweepType] = None
    # With default values
    quantum_us: float = Defaults.quantum_us
    output_dir: str = Defaults.output_dir
    duration: int = Defaults.duration
    cdfWorkload: str = ""  # "" means no cdf

    # Sweeps
    load_levels = [0.01, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
    # Add quantums to sweep for TS processors
    # quantums_to_sweep = [1.0]
    quantums_to_sweep = [1.0, 5.0, 10.0, 20.0, 50.0, 100.0, 500.0]

    def validate(self):
        missing = [k for k, v in asdict(self).items() if v is None]
        if missing:
            details = self.dump()
            raise ValueError(
                f"Validate of SimParams failed: the following fields are None: {missing}\n"
                f"Current values:\n{details}"
            )
        correct_load = abs(self.lmd - (self.mu * self.cores * self.load_level)) < 0.0001
        if not correct_load:
            raise ValueError(f"load and mu/lmd/cores not aligned: lmd {self.lmd}, load {self.load_level}, mu {self.mu}, cores {self.cores}")
    
    def dump(self):
        for field, value in asdict(self).items():
            print(f"{field} = {value}")



    def form_command(self):
        self.validate()
        cmd = f"./schedsim --topo={self.topo} --mu={self.mu} --genType={self.gen_type} --procType={self.proc_type}"
        cmd += f" --lambda={self.lmd} --cores={self.cores} --ctxCost={self.ctx_cost} --duration={self.duration}"
        cmd += f" --quantum={self.quantum_us} --cdfWorkload={self.cdfWorkload}"
        return cmd

    def get_experiment_dirname(self):
        self.validate()
        d = os.path.join(self.output_dir, f"topo{self.topo}_mu{self.mu}_gen{self.gen_type}_proc{self.proc_type}_cores{self.cores}_ctx{self.ctx_cost}_lambda{self.lmd:.4f}")
        os.makedirs(d, exist_ok=True)
        return d

    def get_raw_outfile(self):
        self.validate()
        d = os.path.join(self.get_experiment_dirname(), "data")
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "raw_out.txt")
        return f

    def form_outfile(self):
        self.validate()
        d = os.path.join(self.get_experiment_dirname(), "data")
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, "summary.csv")
        return f

    def _form_detailed_outfile(self, id):
        self.validate()
        d = os.path.join(self.get_experiment_dirname(), "data/detailed")
        os.makedirs(d, exist_ok=True)
        f = os.path.join(d, f"{id}.csv")
        return f
    
    def get_sweep_id(self):
        self.validate()
        id = ""
        all = []
        if self.sweep_type == SweepType.LOAD_SWEEP:
            id = self.load_level
            all = self.load_levels
        elif self.sweep_type == SweepType.QUANTUM_SWEEP:
            id = self.quantum_us
            all = self.quantums_to_sweep
        else:
            raise ValueError(f"Unknown sweep type: {self.sweep_type}")
        return id, all
        
    def form_detailed_outfile(self):
        self.validate()
        return self._form_detailed_outfile(self.get_sweep_id()[0])
    
    def get_all_detailed_outfiles(self):
        self.validate()
        return [self._form_detailed_outfile(id) for id in self.get_sweep_id()[1]]
    
    # Simple helpers for printing params when potting
    def get_plot_dir(self):
        self.validate()
        return os.path.join(self.get_experiment_dirname(), "plots")
    
    def getXcol_name(self):
        self.validate()
        if self.sweep_type == SweepType.LOAD_SWEEP:
            return "Interarrival_Rate"
        elif self.sweep_type == SweepType.QUANTUM_SWEEP:
            return "Quantum"
        else:
            raise ValueError(f"Unknown sweep type: {self.sweep_type}")

    def get_title_suffix(self):
        self.validate()
        if self.sweep_type == SweepType.LOAD_SWEEP:
            return f"Load"
        elif self.sweep_type == SweepType.QUANTUM_SWEEP:
            return f"Quantum"
        else:
            raise ValueError(f"Unknown sweep type: {self.sweep_type}")
    
    def get_plot_fname_suffix(self):
        self.validate()
        if self.sweep_type == SweepType.LOAD_SWEEP:
            return "load"
        elif self.sweep_type == SweepType.QUANTUM_SWEEP:
            return "quantum"
        else:
            raise ValueError(f"Unknown sweep type: {self.sweep_type}")
    
    def get_title_params(self):
        self.validate()
        return f"Topo:{self.topo}, Gen:{self.gen_type}, Proc:{self.proc_type}, Cores:{self.cores}, Ctx:{self.ctx_cost} Load:{self.load_level}"

