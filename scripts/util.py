import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Optional
import os

def plot_cdf(
    data_series: pd.Series,
    saveas: str,
    title: str = "Cumulative Distribution Function",
    xlabel: str = "Value",
    ylabel: str = "Cumulative Probability",
    ax: Optional[plt.Axes] = None,
) -> None:
    """
    Plots the Cumulative Distribution Function (CDF) of a pandas Series.

    This function sorts the data and plots each point against its
    cumulative probability, providing a visual representation of the
    data distribution.

    Args:
        data_series (pd.Series): The data to plot. Should not contain NaNs.
        title (str, optional): The title for the plot.
        xlabel (str, optional): The label for the x-axis.
        ylabel (str, optional): The label for the y-axis.
        ax (plt.Axes, optional): An existing Matplotlib Axes object to plot on.
                                 If None, a new figure and axes are created
                                 and plt.show() is called.
    """
    # Create a new figure and axes if none are provided
    show_plot = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
        show_plot = True

    # Sort the data in ascending order
    data_sorted = data_series.sort_values()

    # Calculate the y-values for the CDF.
    # Each point's y-value is its rank divided by the total number of points.
    y_cdf = np.arange(1, len(data_sorted) + 1) / len(data_sorted)

    # Plot the CDF
    ax.plot(data_sorted, y_cdf)

    # Set plot properties
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, 1.05)  # Set y-axis from 0 to 1 with a little padding
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    os.makedirs(os.path.dirname(saveas), exist_ok=True)
    plt.savefig(saveas)
    plt.close()
