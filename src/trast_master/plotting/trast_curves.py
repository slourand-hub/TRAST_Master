import matplotlib.pyplot as plt

from trast_master.analysis.trast_metrics import get_x


def plot_main_trast_overlay(df, x_axis: str, main_fft_max_harmonics, include_ls_trast: bool = False):
    x, xlabel = get_x(df, x_axis)
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(x, df["dc_trast_raw_norm"].values, marker="o", label="Raw DC-TRAST")

    markers = ["s", "^", "v", "D", "P", "X", "<", ">", "*", "h"]
    for i, H in enumerate(main_fft_max_harmonics):
        col = f"sum{H}_trast_raw_norm"
        if col not in df.columns:
            raise ValueError(f"{col} not found. Increase computed max harmonic.")
        ax.plot(
            x,
            df[col].values,
            marker=markers[i % len(markers)],
            label=rf"Raw FFT-TRAST: $\sum_{{h=1}}^{{{H}}}|c_h|$"
        )

    if include_ls_trast:
        ls_markers = ["s", "^", "v", "D", "P", "X", "<", ">", "*", "h"]
        for i, H in enumerate(main_fft_max_harmonics):
            col = f"sum{H}_trast_ls_raw_norm"
            if col not in df.columns:
                raise ValueError(f"{col} not found. Increase computed max harmonic.")
            ax.plot(
                x,
                df[col].values,
                linestyle="--",
                marker=ls_markers[i % len(ls_markers)],
                label=rf"Least-squares TRAST: $\sum_{{h=1}}^{{{H}}}A_h^{{LS}}$"
            )

    ax.set_xlabel(xlabel)
    ax.set_ylabel("Normalized observable")
    ax.set_title("Raw DC-TRAST and raw FFT/LS-TRAST-like observables")
    ax.grid(True, alpha=0.3)
    ax.set_xscale("log")
    ax.legend()
    fig.tight_layout()
    plt.show(block=False)
    plt.pause(0.1)


def plot_raw_harmonic_ratio_curves(df, x_axis: str, diagnostic_harmonics):
    x, xlabel = get_x(df, x_axis)
    fig, ax = plt.subplots(figsize=(10, 6))

    for h in diagnostic_harmonics:
        col = f"c{h}_over_c0_raw"
        if col in df.columns:
            ax.plot(x, df[col].values, marker="o", label=rf"$|c_{{{h}}}(F)|/|c_0(F)|$")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(r"Normalized harmonic magnitude $|c_h|/|c_0|$")
    ax.set_title("Raw harmonic magnitude diagnostics vs pulse width")
    ax.grid(True, alpha=0.3)
    ax.set_xscale("log")
    ax.legend()
    fig.tight_layout()
    plt.show(block=False)
    plt.pause(0.1)