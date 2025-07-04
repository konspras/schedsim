import pandas as pd
import matplotlib.pyplot as plt
import fire
import numpy as np
import os
import sys # Keep for warnings/errors
import re # For parsing filenames
import util
from common import *

def _extract_numerical_param_from_filename(filename):
    """
    Extracts the numerical lambda or quantum value from a detailed CSV filename
    for sorting purposes.
    """
    basename = os.path.basename(filename)
    match_lambda = re.search(r'_lambda(\d+\.?\d*)\.csv$', basename)
    if match_lambda:
        return float(match_lambda.group(1))
    match_quantum = re.search(r'_quantum(\d+\.?\d*)\.csv$', basename)
    if match_quantum:
        return float(match_quantum.group(1))
    return 0.0 # Should not happen if filenames follow expected pattern

import os
import pandas as pd
import matplotlib.pyplot as plt

def _plot_summary_data(csv_file: str, prm: SimParams):
    """Plots summary data (50th, 99th percentiles) and slowdown."""
    if not os.path.exists(csv_file):
        raise ValueError(f"Summary CSV not found: {csv_file}", file=sys.stderr)

    df = pd.read_csv(csv_file)
    x_col = prm.getXcol_name()
    title_suffix = prm.get_title_suffix()
    plot_filename_suffix = prm.get_plot_fname_suffix()
    exp_plot_dir = prm.get_plot_dir()
    os.makedirs(exp_plot_dir, exist_ok=True)

    # --- 1) Latency plot (unchanged) ---
    plt.figure(figsize=(10, 7))
    plt.plot(df[x_col], df['50th'], label='50th Percentile')
    plt.plot(df[x_col], df['99th'], label='99th Percentile')
    plt.xlabel(f'{x_col} (us)')
    plt.ylabel('Latency (us)')
    title_params = prm.get_title_params()
    plt.title(f"Summary Latency vs. {title_suffix} ({title_params})")
    plt.legend()
    plt.grid(True)
    latency_plot = os.path.join(exp_plot_dir, f"summary_{plot_filename_suffix}.png")
    plt.savefig(latency_plot)
    plt.close()
    print(f"Saved summary plot to {latency_plot}")

    # --- 2) Slowdown plot (new) ---
    # we assume the CSV has '50th_sldn' and '99th_sldn' columns
    plt.figure(figsize=(10, 7))
    plt.plot(df[x_col], df['50th_sldn'], marker='o', linestyle='-', label='50th Slowdown')
    plt.plot(df[x_col], df['99th_sldn'], marker='o', linestyle='-', label='99th Slowdown')
    plt.xlabel(f'{x_col} (us)')
    plt.ylabel('Slowdown (delay / service time)')
    plt.yscale('log')
    plt.title(f"Summary Slowdown vs. {title_suffix} ({title_params})")
    plt.legend()
    plt.grid(True, which='both', ls='--')
    slowdown_plot = os.path.join(exp_plot_dir, f"summary_slowdown_{plot_filename_suffix}.png")
    plt.savefig(slowdown_plot)
    plt.close()
    print(f"Saved slowdown plot to {slowdown_plot}")


def _plot_detailed_scatter(csv_files, prm: SimParams):
    """Plots detailed latency vs. service time and slowdown vs. service time as scatter plots."""
    if not csv_files:
        raise ValueError(f"csv_files not found: {csv_files}", file=sys.stderr)

    # --- Read data and calculate slowdown once ---
    dataframes = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        id = csv_file.split("/")[-1].split(".csv")[0]
        label_suffix = f"{prm.get_title_suffix()}={id}"
        
        # Calculate slowdown, handling potential division by zero.
        df['Slowdown'] = df['Delay'] / df['ServiceTime']
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(subset=['Slowdown'], inplace=True)
        
        dataframes.append({'df': df, 'label': label_suffix})

    exp_plot_dir = prm.get_plot_dir()
    os.makedirs(exp_plot_dir, exist_ok=True)
    title_params = prm.get_title_params()

    # --- Plot 1: Delay vs Service Time ---
    plt.figure(figsize=(12, 8))
    for item in dataframes:
        plt.scatter(item['df']['ServiceTime'], item['df']['Delay'], s=5, alpha=0.3, label=item['label'])
    
    plt.xlabel('Service Time (us)')
    plt.ylabel('Delay (us)')
    plt.title(f"Detailed Latency vs. Service Time ({title_params})")
    plt.legend()
    plt.grid(True)
    plot_filename = os.path.join(exp_plot_dir, "detailed_scatter.png")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved detailed scatter plot to {plot_filename}")

    # --- Plot 2: Slowdown vs Service Time (Size) ---
    plt.figure(figsize=(12, 8))
    for item in dataframes:
        plt.scatter(item['df']['ServiceTime'], item['df']['Slowdown'], s=5, alpha=0.3, label=item['label'])
    
    plt.xlabel('Service Time (us)')
    plt.ylabel('Slowdown (Delay / Service Time)')
    plt.title(f"Slowdown vs. Service Time ({title_params})")
    plt.yscale('log') # Slowdown is often best viewed on a log scale
    plt.legend()
    plt.grid(True, which="both", ls="--")
    plot_filename = os.path.join(exp_plot_dir, "detailed_slowdown_scatter.png")
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved detailed slowdown scatter plot to {plot_filename}")

def _plot_detailed_cdfs(csv_files, prm: SimParams):
    """Plots CDFs of Delay (overall and tail)."""
    if not csv_files:
        raise ValueError(f"csv_files not found: {csv_files}", file=sys.stderr)

    exp_plot_dir = prm.get_plot_dir()
    os.makedirs(exp_plot_dir, exist_ok=True)

    percentiles_to_plot = [0, 80, 95, 99] # 0th percentile means overall CDF

    for p_val in percentiles_to_plot:
        plt.figure(figsize=(10, 7))
        all_empty_filtered = True
        
        for csv_file in csv_files:
            id = csv_file.split("/")[-1].split(".csv")[0]
            df = pd.read_csv(csv_file)
            
            delay_data = df['Delay']
            
            if p_val > 0:
                # Filter based on the percentile of Delay itself
                delay_threshold = delay_data.quantile(p_val / 100.0)
                filtered_data = delay_data[delay_data >= delay_threshold]
                plot_label_suffix = f" (Delay >= P{p_val})"
                plot_filename_prefix = f"p{p_val}_delay_cdf"
            else: # 0th percentile means no filtering
                filtered_data = delay_data
                plot_label_suffix = ""
                plot_filename_prefix = "overall_delay_cdf"

            if not filtered_data.empty:
                all_empty_filtered = False
                data_sorted = filtered_data.sort_values()
                y_cdf = np.arange(1, len(data_sorted) + 1) / len(data_sorted)
                
                # Determine label prefix based on sweep type (lambda or quantum)
                label_prefix = f"ID={id}"

                plt.plot(data_sorted, y_cdf, label=f"{label_prefix}{plot_label_suffix}")

        if not all_empty_filtered:
            plt.xlabel('Delay (us)')
            plt.ylabel("CDF")
            title_params = prm.get_title_params()
            # title_params += f", Load:{load_level}"
            
            if p_val > 0:
                plt.title(f"CDF of Delay for P{p_val}+ Delay ({title_params})")
            else:
                plt.title(f"Overall CDF of Delay ({title_params})")
            
            plt.grid(True, which="both", ls="--")
            plt.legend()
            
            plot_filename = os.path.join(exp_plot_dir, f"{plot_filename_prefix}.png")
            plt.savefig(plot_filename)
            print(f"Saved {plot_filename_prefix} plot to {plot_filename}")
            # else:
            #     print(f"No data for {plot_filename_prefix} plot (P{p_val}+ Delay).")
            plt.close()

def _plot_detailed_slowdown_cdfs(csv_files, prm: SimParams):
    """Plots CDFs of Slowdown (overall and tail)."""
    if not csv_files:
        raise ValueError(f"csv_files not found: {csv_files}", file=sys.stderr)

    exp_plot_dir = prm.get_plot_dir()
    os.makedirs(exp_plot_dir, exist_ok=True)

    percentiles_to_plot = [0, 80, 95, 99] # 0th percentile means overall CDF

    for p_val in percentiles_to_plot:
        plt.figure(figsize=(10, 7))
        all_empty_filtered = True
        
        for csv_file in csv_files:
            id = csv_file.split("/")[-1].split(".csv")[0]
            df = pd.read_csv(csv_file)
            
            # Calculate slowdown, handling potential division by zero.
            # A ServiceTime of 0 would result in infinite slowdown.
            df['Slowdown'] = df['Delay'] / df['ServiceTime']
            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.dropna(subset=['Slowdown'], inplace=True)

            slowdown_data = df['Slowdown']
            
            if p_val > 0:
                # Filter based on the percentile of Slowdown itself
                slowdown_threshold = slowdown_data.quantile(p_val / 100.0)
                filtered_data = slowdown_data[slowdown_data >= slowdown_threshold]
                plot_label_suffix = f" (Slowdown >= P{p_val})"
                plot_filename_prefix = f"p{p_val}_slowdown_cdf"
            else: # 0th percentile means no filtering
                filtered_data = slowdown_data
                plot_label_suffix = ""
                plot_filename_prefix = "overall_slowdown_cdf"

            if not filtered_data.empty:
                all_empty_filtered = False
                data_sorted = filtered_data.sort_values()
                y_cdf = np.arange(1, len(data_sorted) + 1) / len(data_sorted)
                
                label_prefix = f"ID={id}"
                plt.plot(data_sorted, y_cdf, label=f"{label_prefix}{plot_label_suffix}")

        if not all_empty_filtered:
            plt.xlabel('Slowdown (Delay / Service Time)')
            plt.ylabel("CDF")
            title_params = prm.get_title_params()
            plt.title(f"CDF of Slowdown (P{p_val}+) ({title_params})" if p_val > 0 else f"Overall CDF of Slowdown ({title_params})")
            plt.grid(True, which="both", ls="--")
            plt.legend()
            plot_filename = os.path.join(exp_plot_dir, f"{plot_filename_prefix}.png")
            plt.savefig(plot_filename)
            print(f"Saved {plot_filename_prefix} plot to {plot_filename}")
            plt.close()

def _plot_service_time(csv_files, prm: SimParams):
    """Plots the service time CDF."""
    if not csv_files:
        raise ValueError(f"csv_files not found: {csv_files}", file=sys.stderr)

    plt.figure(figsize=(12, 8))
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        
        # Extract lambda or quantum from filename for label
        label_suffix = csv_file.split("/")[-1].split(".csv")[0]
        exp_plot_dir = prm.get_plot_dir()
        plot_filename = os.path.join(exp_plot_dir, f"stime_cdf_{label_suffix}.png")
        util.plot_cdf(df['ServiceTime'], plot_filename, title=f"Input Service Time CDF {label_suffix}", 
                      xlabel="Service Time (us)", ylabel="CDF", xlog=True)
        print(f"Saved service time CDF plot to {plot_filename}")


def plot_experiment_results(prm: SimParams):
    """
    Main function to plot all relevant results for a given experiment configuration.
    It discovers summary and detailed CSVs and generates corresponding plots.
    """
    print(f"\n--- Plotting results for experiment with params:\n{prm.dump()}")

    # Determine summary CSV filenames
    summary_load_csv = prm.form_outfile()

    # Find all detailed CSV filenames matching the parameters
    all_detailed_csvs = prm.get_all_detailed_outfiles()

    # Sort detailed CSVs numerically by lambda or quantum for consistent plotting order
    all_detailed_csvs.sort(key=_extract_numerical_param_from_filename)

    # Plot summary data
    _plot_summary_data(summary_load_csv, prm)

    # Plot detailed data (scatter and CDFs)
    if all_detailed_csvs:
        _plot_service_time(all_detailed_csvs, prm)
        _plot_detailed_scatter(all_detailed_csvs, prm)
        _plot_detailed_cdfs(all_detailed_csvs, prm)
        _plot_detailed_slowdown_cdfs(all_detailed_csvs, prm)
    else:
        print("No detailed CSVs found to plot scatter or CDFs.", file=sys.stderr)
