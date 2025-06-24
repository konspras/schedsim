import pandas as pd
import matplotlib.pyplot as plt
import fire
import numpy as np
import os
import sys # Keep for warnings/errors
import re # For parsing filenames

# Example call
# python3 ./scripts/plot_csv.py --csv_files="['out_quantum.csv']" --x_axis_column Quantum --y_axis_columns="['50th','99th']" --ymax=200
# For detailed latency:
# python3 ./scripts/plot_csv.py --csv_files="['detailed_latency_load_topo0_mu0.1_gen1_proc0_cores10_ctx0.0.csv']" --x_axis_column ServiceTime --y_axis_columns="['Delay']" --plot_type="scatter" --ymax=200
# For CDF plots:
# python3 ./scripts/plot_csv.py --csv_files="['results/detailed_latency_load_topo0_mu0.1_gen1_proc0_cores1_ctx0.0_lambda0.0010.csv']" --y_axis_columns="['Delay']" --plot_type="cdf"

def _get_experiment_dir_name(topo, mu, gen_type, proc_type, cores, ctx_cost):
    """Generates a directory name for plots based on experiment parameters."""
    return f"topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_ctx{ctx_cost}"


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

def _plot_summary_data(csv_file, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=False, load_level=None):
    """Plots summary data (50th, 99th percentiles)."""
    if not os.path.exists(csv_file):
        print(f"Summary CSV not found: {csv_file}", file=sys.stderr)
        return

    df = pd.read_csv(csv_file)
    plt.figure(figsize=(10, 7))

    x_col = 'Quantum' if is_quantum_sweep else 'Interarrival_Rate'
    title_suffix = f"Load (λ)" if not is_quantum_sweep else f"Quantum (Q)"
    plot_filename_suffix = "load" if not is_quantum_sweep else "quantum"

    plt.plot(df[x_col], df['50th'], label='50th Percentile')
    plt.plot(df[x_col], df['99th'], label='99th Percentile')

    plt.xlabel(f'{x_col} (us)')
    plt.ylabel('Latency (us)')
    title_params = f"Topo:{topo}, Gen:{gen_type}, Proc:{proc_type}, Cores:{cores}, Ctx:{ctx_cost}"
    if is_quantum_sweep:
        title_params += f", Load:{load_level}"
    plt.title(f"Summary Latency vs. {title_suffix} ({title_params})")
    plt.legend()
    plt.grid(True)

    exp_plot_dir = os.path.join(output_dir, "plots", _get_experiment_dir_name(topo, mu, gen_type, proc_type, cores, ctx_cost))
    plot_filename = os.path.join(exp_plot_dir, f"summary_{plot_filename_suffix}.png")
    os.makedirs(os.path.dirname(plot_filename), exist_ok=True)
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved summary plot to {plot_filename}")

def _plot_detailed_scatter(csv_files, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=False, load_level=None):
    """Plots detailed latency vs. service time as a scatter plot."""
    if not csv_files:
        print("No detailed CSV files found for scatter plot.", file=sys.stderr)
        return

    plt.figure(figsize=(12, 8))
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        
        # Extract lambda or quantum from filename for label
        label_suffix = ""
        if is_quantum_sweep:
            match_val = re.search(r'_quantum(\d+\.?\d*)\.csv$', os.path.basename(csv_file))
            if match_val: label_suffix = f" (Q={float(match_val.group(1)):.1f})"
        else: # Load sweep
            match_val = re.search(r'_lambda(\d+\.?\d*)\.csv$', os.path.basename(csv_file))
            if match_val: label_suffix = f" (λ={float(match_val.group(1)):.4f})"

        plt.scatter(df['ServiceTime'], df['Delay'], s=5, alpha=0.3, label=f"{os.path.basename(csv_file).split('_lambda')[0].split('_quantum')[0]}{label_suffix}")
    
    plt.xlabel('Service Time (us)')
    plt.ylabel('Delay (us)')
    title_params = f"Topo:{topo}, Gen:{gen_type}, Proc:{proc_type}, Cores:{cores}, Ctx:{ctx_cost}"
    if is_quantum_sweep:
        title_params += f", Load:{load_level}"
    plt.title(f"Detailed Latency vs. Service Time ({title_params})")
    plt.legend()
    plt.grid(True)

    exp_plot_dir = os.path.join(output_dir, "plots", _get_experiment_dir_name(topo, mu, gen_type, proc_type, cores, ctx_cost))
    plot_filename = os.path.join(exp_plot_dir, "detailed_scatter.png")
    os.makedirs(os.path.dirname(plot_filename), exist_ok=True)
    plt.savefig(plot_filename)
    plt.close()
    print(f"Saved detailed scatter plot to {plot_filename}")

def _plot_detailed_cdfs(csv_files, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=False, load_level=None):
    """Plots CDFs of Delay (overall and tail)."""
    if not csv_files:
        print("No detailed CSV files found for CDF plots.", file=sys.stderr)
        return

    exp_plot_dir = os.path.join(output_dir, "plots", _get_experiment_dir_name(topo, mu, gen_type, proc_type, cores, ctx_cost))
    os.makedirs(exp_plot_dir, exist_ok=True)

    percentiles_to_plot = [0, 80, 95, 99] # 0th percentile means overall CDF

    for p_val in percentiles_to_plot:
        plt.figure(figsize=(10, 7))
        all_empty_filtered = True
        
        for csv_file in csv_files:
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
                label_prefix = ""
                if is_quantum_sweep:
                    match_val = re.search(r'_quantum(\d+\.?\d*)\.csv$', os.path.basename(csv_file))
                    if match_val: label_prefix = f"Q={float(match_val.group(1)):.1f}"
                else: # Load sweep
                    match_val = re.search(r'_lambda(\d+\.?\d*)\.csv$', os.path.basename(csv_file))
                    if match_val: label_prefix = f"λ={float(match_val.group(1)):.4f}"

                plt.plot(data_sorted, y_cdf, label=f"{label_prefix}{plot_label_suffix}")

        if not all_empty_filtered:
            plt.xlabel('Delay (us)')
            plt.ylabel("CDF")
            title_params = f"Topo:{topo}, Gen:{gen_type}, Proc:{proc_type}, Cores:{cores}, Ctx:{ctx_cost}"
            if is_quantum_sweep:
                title_params += f", Load:{load_level}"
                
                if p_val > 0:
                    plt.title(f"CDF of Delay for P{p_val}+ Delay ({title_params})")
                else:
                    plt.title(f"Overall CDF of Delay ({title_params})")
                
                plt.grid(True, which="both", ls="--")
                plt.legend()
                
                plot_filename = os.path.join(exp_plot_dir, f"{plot_filename_prefix}.png")
                plt.savefig(plot_filename)
                print(f"Saved {plot_filename_prefix} plot to {plot_filename}")
            else:
                print(f"No data for {plot_filename_prefix} plot (P{p_val}+ Delay).")
            plt.close()

def plot_experiment_results(topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir=".", load_level=0.8):
    """
    Main function to plot all relevant results for a given experiment configuration.
    It discovers summary and detailed CSVs and generates corresponding plots.
    """
    print(f"\n--- Plotting results for experiment: Topo={topo}, Mu={mu}, Gen={gen_type}, Proc={proc_type}, Cores={cores}, Ctx={ctx_cost} ---")

    # Determine summary CSV filenames
    summary_load_csv = os.path.join(output_dir, f"load_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_ctx{ctx_cost}.csv")
    summary_quantum_csv = os.path.join(output_dir, f"quantum_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_load{load_level}_ctx{ctx_cost}.csv")

    # Find all detailed CSV filenames matching the parameters
    all_detailed_csvs = []
    # Pattern for detailed load CSVs
    detailed_load_pattern = f"detailed_latency_load_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_ctx{ctx_cost}_lambda"
    # Pattern for detailed quantum CSVs
    detailed_quantum_pattern = f"detailed_latency_quantum_topo{topo}_mu{mu}_gen{gen_type}_proc{proc_type}_cores{cores}_load{load_level}_ctx{ctx_cost}_quantum"

    for f_name in os.listdir(output_dir):
        if f_name.startswith(detailed_load_pattern) and f_name.endswith(".csv"):
            all_detailed_csvs.append(os.path.join(output_dir, f_name))
        elif f_name.startswith(detailed_quantum_pattern) and f_name.endswith(".csv"):
            all_detailed_csvs.append(os.path.join(output_dir, f_name))

    # Sort detailed CSVs numerically by lambda or quantum for consistent plotting order
    all_detailed_csvs.sort(key=_extract_numerical_param_from_filename)

    # Plot summary data
    _plot_summary_data(summary_load_csv, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=False)
    _plot_summary_data(summary_quantum_csv, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=True, load_level=load_level)

    # Plot detailed data (scatter and CDFs)
    if all_detailed_csvs:
        # Determine if it's a quantum sweep or load sweep for detailed plots
        is_quantum_sweep_detailed = any("quantum" in os.path.basename(f) for f in all_detailed_csvs)
        _plot_detailed_scatter(all_detailed_csvs, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=is_quantum_sweep_detailed, load_level=load_level)
        _plot_detailed_cdfs(all_detailed_csvs, topo, mu, gen_type, proc_type, cores, ctx_cost, output_dir, is_quantum_sweep=is_quantum_sweep_detailed, load_level=load_level)
    else:
        print("No detailed CSVs found to plot scatter or CDFs.", file=sys.stderr)

if __name__ == '__main__':
    fire.Fire(plot_experiment_results)
