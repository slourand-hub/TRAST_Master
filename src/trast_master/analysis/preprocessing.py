import numpy as np


def clean_finite_time_signal(time_axis, signal):
    time_axis = np.asarray(time_axis, dtype=float)
    signal = np.asarray(signal, dtype=float)

    if time_axis.shape != signal.shape:
        raise ValueError("time_axis and signal must have the same shape")

    mask = np.isfinite(time_axis) & np.isfinite(signal)
    cleaned_time = time_axis[mask]
    cleaned_signal = signal[mask]

    if cleaned_time.size < 2:
        raise ValueError("Not enough finite samples after cleaning")

    return cleaned_time, cleaned_signal