#!/usr/bin/python3

import fire
import os
import sys
import subprocess
import csv
from pprint import pprint

# Import the plotting function
from plot_csv import plot_experiment_results
from common import *
import util


def _extract_detailed_data(raw_output_content):
    """
    Extracts detailed latency vs service time data from the raw simulation output.
    Returns (header_list, data_rows_list_of_lists).
    """
    detailed_data_start_marker = "---DETAILED_LATENCY_VS_SERVICE_TIME_DATA_START---"
    detailed_data_end_marker = "---DETAILED_LATENCY_VS_SERVICE_TIME_DATA_END---"
    
    lines = raw_output_content.splitlines()
    
    in_data_section = False
    header = []
    data_rows = []
    
    for line in lines:
        if line == detailed_data_start_marker:
            in_data_section = True
            continue
        if line == detailed_data_end_marker:
            in_data_section = False
            break # Stop parsing after the end marker
        
        if in_data_section:
            if not header: # First line after start marker is header
                header = line.split(',')
            else:
                data_rows.append(line.split(','))
    return header, data_rows



def run(prm: SimParams):
    '''
    Runs a sweep over different load levels for a fixed configuration.
    mu in us
    output_dir: Directory to save raw output files.
    '''
    service_time_per_core_us = 1 / prm.mu
    rps_capacity_per_core = 1 / service_time_per_core_us * 1000.0 * 1000.0
    total_rps_capacity = rps_capacity_per_core * prm.cores
    injected_rps = [load_lvl * total_rps_capacity for load_lvl in prm.load_levels]
    lambdas = [rps / 1000.0 / 1000.0 for rps in injected_rps]
    res_file = prm.get_raw_outfile()
    os.makedirs(prm.output_dir, exist_ok=True)

    with open(res_file, 'w') as f:
        for l in sorted(lambdas): # Sort lambdas for consistent output order
            prm.lmd = l
            cmd = prm.form_command()
            stdout = util.run_cmd(cmd)
            f.write(stdout) # Write raw output to file

            # --- Generate detailed CSV for THIS run ---
            raw_output_content = stdout
            detailed_header, detailed_rows = _extract_detailed_data(raw_output_content)
            if detailed_header and detailed_rows:
                detailed_out_file = prm.form_detailed_outfile()
                with open(detailed_out_file, 'w', newline='') as f_detailed:
                    writer = csv.writer(f_detailed)
                    writer.writerow(detailed_header)
                    writer.writerows(detailed_rows)
                print(f"Detailed latency CSV saved to {detailed_out_file}")

    # --- Start of merged CSV logic for SUMMARY ---
    print(f"Processing {res_file} into summary CSV...")
    results = {}
    out_file = prm.form_outfile()
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

    # pprint(results)

    with open(out_file, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Interarrival_Rate', '50th', '99th'])
        for rate in sorted(results.keys(), key=float):
            writer.writerow(
                [rate, results[rate]['50th'], results[rate]['99th']])
    print(f"CSV saved to {out_file}")
    plot_experiment_results(prm)


def run_quantum_sweep(prm: SimParams):
    '''
    Runs schedsim for a fixed load level, sweeping over quantum sizes.
    mu in us
    load_level is the target system load (e.g., 0.8 for 80%)
    '''
    if prm.proc_type != 2:
        print("Error: Quantum sweep is only meaningful for procType=2 (Time Sharing).", file=sys.stderr)
        sys.exit(1)

    if prm.load_level is None:
        raise ValueError("Must set load_level for quantum sweep")

    service_time_per_core_us = 1 / prm.mu
    rps_capacity_per_core = 1 / service_time_per_core_us * 1000.0 * 1000.0
    total_rps_capacity = rps_capacity_per_core * prm.cores
    injected_rps = prm.load_level * total_rps_capacity
    l = injected_rps / 1000.0 / 1000.0
    prm.lmd = l

    res_file = prm.get_raw_outfile()
    with open(res_file, 'w') as f:
        for q in prm.quantums_to_sweep:
            prm.quantum_us = q
            stdout = util.run_cmd(prm.form_command())
            
            f.write(stdout) # Write raw output to file
    
            # --- Generate detailed CSV for THIS run ---
            raw_output_content = stdout
            detailed_header, detailed_rows = _extract_detailed_data(raw_output_content)
            if detailed_header and detailed_rows:
                detailed_out_file = prm.form_detailed_outfile()
                with open(detailed_out_file, 'w', newline='') as f_detailed:
                    writer = csv.writer(f_detailed)
                    writer.writerow(detailed_header)
                    writer.writerows(detailed_rows)
                print(f"Detailed latency CSV saved to {detailed_out_file}")

    # --- Start of merged CSV logic for SUMMARY ---
    print(f"Processing {res_file} into summary CSV...")
    results = {}
    out_file = prm.form_outfile()
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

    # pprint(results)

    with open(out_file, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(['Quantum', '50th', '99th'])
        for quantum in sorted(results.keys(), key=float):
            writer.writerow(
                [quantum, results[quantum]['50th'], results[quantum]['99th']])
    print(f"CSV saved to {out_file}")
    plot_experiment_results(prm)


def run_any(cmd: str, **kwargs):
    args = kwargs
    if "mu" not in args:
        if "cdfWorkload" not in args:
            raise ValueError("Must set mu or cdfWorkload")
        if args["gen_type"] != 5:
            raise ValueError("CDF only valid with gentype 5")

        wl = args["cdfWorkload"]
        meansz = -1.0  # CAREFUL: MUST DIVIDE BY SAME AMOUNT AS adv_generators.go does when reading CDF
        if wl == "w4":
            meansz = 127796.6
        else:
            raise ValueError(f"Unknown workload: {wl}")
        meansz /= 100.0
        # meansz now reflects the mean service time in us
        args["mu"] = 1.0 / meansz

    params = SimParams(**args)
    
    if cmd == "run":
        params.sweep_type = SweepType.LOAD_SWEEP
        run(params)
    elif cmd == "run_quantum":
        params.sweep_type = SweepType.QUANTUM_SWEEP
        run_quantum_sweep(params)
    else:
        raise ValueError(f"Unknown command: {cmd}")

if __name__ == "__main__":
    fire.Fire(run_any)
