import matplotlib.pyplot as plt
import numpy as np


def plot_raw_trace(time_axis, signal, title="Raw trace", show=True):
    time_axis = np.asarray(time_axis, dtype=float)
    signal = np.asarray(signal, dtype=float)

    fig, ax = plt.subplots()
    ax.plot(time_axis, signal)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Signal")
    ax.set_title(title)
    ax.grid(True)

    if show:
        plt.show()

    return fig, ax