import pandas as pd
import matplotlib.pyplot as plt
import fire
import os

# Example call
# python3 ./scripts/plot_csv.py --csv_files="['out_quantum.csv']" --x_axis_column Quantum --y_axis_columns="['50th','99th']" --ymax=200

def plot_csv_data(csv_files, x_axis_column, y_axis_columns, ymax=None):
    print(f"plotting from csv files {csv_files}")
    print(f"x_axis_column {x_axis_column}")
    print(f"y_axis_columns {y_axis_columns}")
    x_axis_column = str(x_axis_column)
    y_axis_columns = [str(v) for v in y_axis_columns]

    for file_name in csv_files:
        # Read CSV file into a pandas DataFrame
        df = pd.read_csv(file_name)
        print("Input Data")
        print(df)

        # Extract x-axis and y-axis data
        x_data = df[x_axis_column]
        for y_column in y_axis_columns:
            print(f"y_column {y_column}")
            y_data = df[y_column]
            
            # Plot the data
            plt.plot(x_data, y_data, label=f"{file_name[:-4]}-{y_column}")

    # Add labels and legend
    plt.xlabel(x_axis_column)
    plt.ylabel(f"{y_axis_columns}")
    plt.title(f"{csv_files}")
    plt.grid(True)
    if ymax:
        plt.ylim((0,ymax))
    plt.legend()
    
    try:
        os.mkdir("plots")
    except FileExistsError:
        pass
    plt.savefig(f"plots/{'|'.join(csv_files)}-{x_axis_column}-{'|'.join(y_axis_columns)}.png")

if __name__ == '__main__':
    fire.Fire(plot_csv_data)
