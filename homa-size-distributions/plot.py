#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import fire
from typing import List

# EXAMPLE
# python3 plot.py --cdf-files '["Google_AllRPC.txt", "Facebook_HadoopDist_All.txt", "DCTCP_MsgSizeDist.txt", "GPT3B.txt"]' --output-base-filename "./CDFs"

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


def plot_workload_cdfs(cdf_files: List[str], output_base_filename: str = "workload_cdf_comparison"):
    """
    Plots CDFs from one or more workload CDF files and saves them as PNG and PDF.

    Each input file is expected to have a header line (which is ignored) followed by
    two space-separated columns: flow size (in bytes) and cumulative probability.

    Args:
        cdf_files (List[str]): A list of paths to the CDF files to plot.
        output_base_filename (str): The base name for the output plot files (e.g., 'plots/my_plot').
                                    The .png and .pdf extensions will be added automatically.
    """
    if not cdf_files:
        print("Error: No CDF files provided to plot.", file=sys.stderr)
        sys.exit(1)

    # Use a professional plot style
    plt.style.use('seaborn-v0_8-whitegrid')
    plt.figure(figsize=(DOUBLE_COL_WIDTH, FIG_HEIGHT))
    ax = plt.gca()

    # Define distinct styles and colors to cycle through for each file
    # colors = plt.cm.viridis(np.linspace(0, 1, len(cdf_files)))
    colors = [
        '#7b9acc',  # Desaturated Blue
        '#f08080',  # Soft Red (Light Coral)
        '#8fbc8f',  # Muted Green (Dark Sea Green)
        '#b19cd9',  # Light Purple
        '#f2c46d',  # Sandy Yellow/Orange
        '#778899'   # Neutral Gray (Light Slate Gray)
    ]
    linestyles = ['dashed', 'dotted', 'dashdot', 'solid']

    for i, cdf_file in enumerate(cdf_files):
        if not os.path.exists(cdf_file):
            print(f"Warning: CDF file not found, skipping: {cdf_file}", file=sys.stderr)
            continue

        try:
            # Create a simple label "W1", "W2", etc., based on file order.
            label = f"W{i+1}"

            # Read the data using pandas.
            # - sep=r'\s+': handles one or more spaces as a delimiter.
            # - skiprows=1: skips the header row containing the mean size.
            # - header=None: specifies that the file has no header row for pandas to use.
            # - names=[...]: assigns column names for easy access.
            df = pd.read_csv(
                cdf_file,
                sep=r'\s+',
                skiprows=1,
                header=None,
                names=['size_bytes', 'cum_prob']
            )

            if df.empty:
                print(f"Warning: CDF file is empty or unreadable, skipping: {cdf_file}", file=sys.stderr)
                continue

            # Special handling for the DCTCP workload, which provides sizes in MTUs.
            # We convert it to bytes by multiplying by a standard MTU size of 1500.
            if 'DCTCP_MsgSizeDist.txt' in os.path.basename(cdf_file):
                print(f"Info: Converting DCTCP flow sizes from MTUs to bytes (x1500) for {cdf_file}")
                df['size_bytes'] = df['size_bytes'] * 1500

            # Plot the CDF curve for the current file
            ax.plot(
                df['size_bytes'],
                df['cum_prob'],
                label=label,
                color=colors[i],
                linestyle=linestyles[i % len(linestyles)],
                linewidth=2.5
            )

        except Exception as e:
            print(f"Error processing file {cdf_file}: {e}", file=sys.stderr)
            continue

    # Check if any data was successfully plotted before proceeding
    if not ax.get_legend_handles_labels()[0]:
        print("No data was plotted. Aborting plot generation.", file=sys.stderr)
        plt.close()
        return

    # --- Configure Plot Aesthetics ---
    ax.set_xlabel("Flow Size (Bytes)", fontsize=FIGURE_FONT_SZ)
    ax.set_ylabel("CDF", fontsize=FIGURE_FONT_SZ)
    # ax.set_title("Workload Flow Size Distribution", fontsize=16)
    ax.set_xscale('log')  # Log scale is standard for flow sizes
    ax.set_ylim(0, 1.05)
    ax.grid(True, which="both", ls="--", linewidth=0.6)
    ax.legend(fontsize=FIGURE_FONT_SZ)
    plt.xticks(fontsize=FIGURE_FONT_SZ)
    plt.yticks(fontsize=FIGURE_FONT_SZ)

    # --- Save the Plot ---
    png_file = f"{output_base_filename}.png"
    pdf_file = f"{output_base_filename}.pdf"

    print(f"Saving plot to {png_file} and {pdf_file}")

    plt.savefig(png_file, bbox_inches='tight', dpi=300)
    plt.savefig(pdf_file, bbox_inches='tight')
    print(f"Successfully saved plot to {png_file} and {pdf_file}")
    plt.close()

if __name__ == "__main__":
    fire.Fire(plot_workload_cdfs)