#!/usr/bin/env python3
"""
plot_quantum_curves.py

Loads a hardcoded dict of CSV files (each with a 'Quantum' column and various metrics),
then plots a specified column against 'Quantum' (both axes log scale) for each file,
saving the figure as PDF and PNG.
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# HEIGHT
FIG_HEIGHT = 1.1

FIG_HEIGHT_9 = 0.9
FIG_HEIGHT_13 = 1.3
FIG_HEIGHT_15 = 1.5
FIG_HEIGHT_20 = 2.0

# WIDTH
SINGLE_COL_WIDTH = 3.1
DOUBLE_COL_WIDTH = 3.25

SINGLE_COL_HALF_WIDTH = 1.55
DOUBLE_COL_HALF_WIDTH = 1.62

# FONTS
FIGURE_FONT_SZ = 9
FIGURE_FONT_SZ_SMALL = 7
FIGURE_FONT_SZ_VSMALL = 6
FIGURE_FONT_SZ_VvSMALL = 5.5
FIGURE_FONT_SZ_VVSMALL = 5

# LEGEND
LEGEND_HEIGHT = 0.2
LEGEND_BORDER_PAD = 0.1
LEGEND_COLUMN_SPACING = 0.2
LEGEND_MORE_COLUMN_SPACING = 0.4
LEGEND_WIDTH = 0.3
LEGEND_FONTSIZE = 5
LEGEND_FONTSIZE_5p5 = 5.5
LEGEND_FONTSIZE_6 = 6
LEGEND_FONTSIZE_7 = 7

# ============================================================================
def load_csv_files(file_map):
    """
    Load each CSV given in file_map into a dict of DataFrames using the same keys.

    Args:
        file_map (dict[str, str | Path]): mapping label → path to CSV file

    Returns:
        dict[str, pd.DataFrame]: mapping each label to its DataFrame
    """
    data = {}
    for label, path in file_map.items():
        p = Path(path)
        if not p.is_file():
            print(f"Warning: file for '{label}' not found, skipping: {p}", file=sys.stderr)
            continue
        data[label] = pd.read_csv(p)
    print(f"Loaded data for labels: {list(data.keys())}")
    return data


def plot_column(dataframes,
                column,
                out_dir=None,
                fig_size=(DOUBLE_COL_WIDTH, FIG_HEIGHT),
                font_size=FIGURE_FONT_SZ,
                line_width=3,
                marker_size=0):
    """
    Plot 'column' vs 'Quantum' for each DataFrame in dataframes on log-log axes,
    normalizing each curve so its first value is 1.0.
    Saves both PDF and PNG in out_dir.
    """
    colors = [
        '#7b9acc',  # Desaturated Blue
        '#f08080',  # Soft Red (Light Coral)
        '#8fbc8f',  # Muted Green (Dark Sea Green)
        '#b19cd9',  # Light Purple
        '#f2c46d',  # Sandy Yellow/Orange
        '#778899'   # Neutral Gray (Light Slate Gray)
    ]
    linestyles = ['dashed', 'dotted', 'dashdot', 'solid']

    # Configure fonts
    plt.rc('font', size=font_size)
    plt.rc('axes', titlesize=font_size * 1.1)
    plt.rc('axes', labelsize=font_size)
    plt.rc('xtick', labelsize=font_size * 0.9)
    plt.rc('ytick', labelsize=font_size * 0.9)
    plt.rc('legend', fontsize=font_size * 0.9)

    # Ensure output directory
    if out_dir is None:
        out_dir = Path(__file__).parent
    else:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    # Create figure
    plt.figure(figsize=fig_size)

    # Plot each normalized series
    for i, (label, df) in enumerate(dataframes.items()):
        if 'Quantum' not in df.columns or column not in df.columns:
            print(f"Warning: missing 'Quantum' or '{column}' in '{label}', skipping",
                  file=sys.stderr)
            continue

        x = df['Quantum'].astype(float)
        y_raw = df[column].astype(float)
        if y_raw.empty:
            print(f"Warning: no data in '{label}', skipping", file=sys.stderr)
            continue
        y = y_raw / y_raw.iloc[0]

        plt.plot(
            x,
            y,
            color=colors[i % len(colors)],
            linestyle=linestyles[i % len(linestyles)],
            marker='o',
            markersize=marker_size,
            linewidth=line_width,
            label=label
        )

    # Styling
    plt.xscale('log')
    plt.yscale('log')

    # Set y-axis ticks at decades from 0.1 to 10000 with exponential labels
    powers = list(range(0, 5))  # -1,0,1,2,3,4
    yticks = [10**p for p in powers]
    ylabels = [rf"$10^{{{p}}}$" for p in powers]
    plt.yticks(yticks, ylabels)

    plt.xlabel('Scheduling Quantum (KB)')
    plt.ylabel("Normalized Mean\nSlowdown")
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.legend(loc='center right',)

    # Save
    base = Path(out_dir) / f"quantum_{column.replace(' ', '_')}_norm"
    for ext in ('pdf', 'png'):
        out_path = base.with_suffix(f'.{ext}')
        plt.savefig(out_path, bbox_inches='tight')
        print(f"Saved plot: {out_path}")
    plt.close()



def main():
    # === Hardwired dict of CSV file paths ===
    cmn_pref = (
        "/home/prasopou/Documents/PhD/codebases/schedsim/results/"
    )
    # keys will be used as labels
    csv_files = {
        'W1':  f"{cmn_pref}/topo0_mu0.34160542250783477_gen5_prc3_c1_ctx0.0_wlw3_dur20000000_QUANTUM_SWEEP/data/summary.csv",
        'W2':  f"{cmn_pref}/topo0_mu0.007824934309676469_gen5_prc3_c1_ctx0.0_wlw4_dur20000000_QUANTUM_SWEEP/data/summary.csv",
        'W3':  f"{cmn_pref}/topo0_mu0.0003821096272520586_gen5_prc3_c1_ctx0.0_wlw5_dur20000000_QUANTUM_SWEEP/data/summary.csv",
        'W4': f"{cmn_pref}/topo0_mu7.946598855689765e-06_gen5_prc3_c1_ctx0.0_wlGPT3B_dur2000000000_QUANTUM_SWEEP/data/summary.csv",
    }

    # Load CSVs
    dfs = load_csv_files(csv_files)
    if not dfs:
        print("Error: no valid CSV files loaded.", file=sys.stderr)
        sys.exit(1)

    # Plot e.g. '99th'
    plot_column(dfs, 'MeanSlowdown')

if __name__ == '__main__':
    main()
