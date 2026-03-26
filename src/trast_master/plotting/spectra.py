import numpy as np
import matplotlib.pyplot as plt

from trast_master.analysis.trast_metrics import choose_representative_indices


def plot_raw_normalized_spectra(df, n_spectrum_pulsewidths: int, max_h: int):
    idx_list = choose_representative_indices(len(df), n_spectrum_pulsewidths)
    harmonics = np.arange(1, max_h + 1)

    fig, ax = plt.subplots(figsize=(10, 6))
    for idx in idx_list:
        pw_us = df.loc[idx, "pulse_width_us"]
        spectrum = [df.loc[idx, f"c{h}_over_c0_raw"] for h in harmonics if f"c{h}_over_c0_raw" in df.columns]
        hh = np.arange(1, len(spectrum) + 1)
        ax.plot(hh, spectrum, marker="o", markersize=3, linewidth=1.2, label=fr"{pw_us:.3g} $\mu$s")

    ax.set_xlabel("Harmonic index h")
    ax.set_ylabel(r"Normalized magnitude $|c_h|/|c_0|$")
    ax.set_title("Raw normalized spectra for representative pulse widths")
    ax.grid(True, alpha=0.3)
    ax.legend(title="Pulse width")
    fig.tight_layout()
    plt.show(block=False)
    plt.pause(0.1)