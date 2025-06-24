#!/usr/bin/python3

import fire
import os
import sys
import subprocess
from multiprocessing import Process
from enum import Enum, auto
import csv
from pprint import pprint

# Only written for single Q
load_levels = [0.01, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]
# Add quantums to sweep for TS processors
quantums_to_sweep = [1.0, 5.0, 10.0, 20.0, 50.0, 100.0]
metrics = ['Count', 'Stolen', 'AVG', 'STDDev',
           '50th', '90th', '95th', '99th', 'Reqs/time_unit']


def run(topo, mu, gen_type, proc_type, cores, ctx_cost=0.0, output_dir="."):
    '''
    Runs a sweep over different load levels for a fixed configuration.
    mu in us
    output_dir: Directory to save raw output files.
    '''
    service_time_per_core_us = 1 / mu
    rps_capacity_per_core = 1 / service_time_per_core_us * 1000.0 * 1000.0
    total_rps_capacity = rps_capacity_per_core * cores
    injected_rps = [load_lvl * total_rps_capacity for load_lvl in load_levels]
    lambdas = [rps / 1000.0 / 1000.0 for rps in injected_rps]
    res_file = os.path.join(output_dir, "out.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(res_file, 'w') as f:
        for l in sorted(lambdas): # Sort lambdas for consistent output order
            cmd = f"./schedsim --topo={topo} --mu={mu} --genType={gen_type} --procType={proc_type} --lambda={l} --cores={cores} --ctxCost={ctx_cost}"
            if proc_type == 2:
                cmd += " --quantum=10.0"  # Use default quantum for load sweeps
            print(f"Running... {cmd}")
            subprocess.run(cmd, stdout=f, shell=True)

    # --- Start of merged CSV logic ---
    print(f"Processing {res_file} into CSV...")
    results = {}
    out_file = os.path.join(output_dir, f"load_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_ctx{ctx_cost}.csv")
    with open(res_file, 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        rate = 0
        next_is_res = False
        for row in csv_reader:
            if len(row) >= 3 and "interarrival_rate" in row[2]:
                rate = row[2].split(":")[1]
                results[rate] = {}
            if next_is_res:
                for i, metric in enumerate(metrics):
                    results[rate][metric] = row[i]
            next_is_res = "Count" == row[0]

    pprint(results)

    with open(out_file, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Interarrival_Rate', '50th', '99th'])
        for rate in sorted(results.keys(), key=float):
            writer.writerow(
                [rate, results[rate]['50th'], results[rate]['99th']])
    print(f"CSV saved to {out_file}")
    # --- End of merged CSV logic ---

def run_quantum_sweep(topo, mu, gen_type, proc_type, cores, load_level=0.8, ctx_cost=0.0, output_dir="."):
    '''
    Runs schedsim for a fixed load level, sweeping over quantum sizes.
    mu in us
    load_level is the target system load (e.g., 0.8 for 80%)
    '''
    if proc_type != 2:
        print("Error: Quantum sweep is only meaningful for procType=2 (Time Sharing).", file=sys.stderr)
        sys.exit(1)

    service_time_per_core_us = 1 / mu
    rps_capacity_per_core = 1 / service_time_per_core_us * 1000.0 * 1000.0
    total_rps_capacity = rps_capacity_per_core * cores
    injected_rps = load_level * total_rps_capacity
    l = injected_rps / 1000.0 / 1000.0

    res_file = os.path.join(output_dir, "out_quantum.txt")
    os.makedirs(output_dir, exist_ok=True)
    with open(res_file, 'w') as f:
        for q in quantums_to_sweep:
            cmd = f"./schedsim --topo={topo} --mu={mu} --genType={gen_type} --procType={proc_type} --lambda={l} --quantum={q} --cores={cores} --ctxCost={ctx_cost}"
            print(f"Running... {cmd}")
            subprocess.run(cmd, stdout=f, shell=True)
    
    # --- Start of merged CSV logic ---
    print(f"Processing {res_file} into CSV...")
    results = {}
    out_file = os.path.join(output_dir, f"quantum_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_load{load_level}_ctx{ctx_cost}.csv")
    with open(res_file, 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        quantum = 0
        next_is_res = False
        for row in csv_reader:
            if len(row) >= 4 and "quantum" in row[3]:
                quantum = row[3].split(":")[1]
                results[quantum] = {}
            if next_is_res:
                for i, metric in enumerate(metrics):
                    results[quantum][metric] = row[i]
            next_is_res = "Count" == row[0]

    pprint(results)

    with open(out_file, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Quantum', '50th', '99th'])
        for quantum in sorted(results.keys(), key=float):
            writer.writerow(
                [quantum, results[quantum]['50th'], results[quantum]['99th']])
    print(f"CSV saved to {out_file}")
    # --- End of merged CSV logic ---


if __name__ == "__main__":
    fire.Fire({
        "run": run,
        "run_quantum": run_quantum_sweep,
    })
