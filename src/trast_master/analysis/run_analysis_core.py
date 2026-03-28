from __future__ import annotations

from trast_master.analysis.loader import find_npz_files, build_acquisition_summary
from trast_master.analysis.trast_metrics import compute_raw_diagnostics
from trast_master.plotting.trast_curves import (
    plot_main_trast_overlay,
    plot_raw_harmonic_ratio_curves,
)
from trast_master.plotting.spectra import plot_raw_normalized_spectra


def compute_analysis_results(config, logger=print):
    files = find_npz_files(config.folder)
    logger(f"Found {len(files)} file(s).")
    if not files:
        raise RuntimeError("No .npz files found.")

    acq_df = build_acquisition_summary(
        files,
        default_duty_fraction=config.default_duty_fraction,
        acquisition_periods=getattr(config, "num_periods_to_capture", 20.0),
    )

    logger("Building acquisition summary...")
    acq_df = build_acquisition_summary(
        files,
        default_duty_fraction=config.default_duty_fraction,
        acquisition_periods=getattr(config, "num_periods_to_capture", 20.0),
    )

    logger("Computing FFT/TRAST diagnostics...")
    df = compute_raw_diagnostics(
        files=files,
        max_h=config.max_harmonic,
        default_duty_fraction=config.default_duty_fraction,
        logger=logger,
    )
    logger("Diagnostics completed.")

    preview_cols = ["pulse_width_ns", "dc_trast_raw_norm"]
    preview_cols += [
        f"sum{H}_trast_raw_norm"
        for H in config.main_fft_max_harmonics
        if f"sum{H}_trast_raw_norm" in df.columns
    ]

    if config.include_ls_trast:
        preview_cols += [
            f"sum{H}_trast_ls_raw_norm"
            for H in config.main_fft_max_harmonics
            if f"sum{H}_trast_ls_raw_norm" in df.columns
        ]

    preview_df = df[preview_cols].copy()

    return {
        "files": files,
        "acq_df": acq_df,
        "df": df,
        "preview_df": preview_df,
    }


def render_analysis_plots(config, df):
    plot_main_trast_overlay(
        df,
        x_axis=config.x_axis,
        main_fft_max_harmonics=config.main_fft_max_harmonics,
        include_ls_trast=config.include_ls_trast,
    )

    plot_raw_harmonic_ratio_curves(
        df,
        x_axis=config.x_axis,
        diagnostic_harmonics=config.diagnostic_harmonics,
    )

    plot_raw_normalized_spectra(
        df,
        n_spectrum_pulsewidths=config.n_spectrum_pw,
        max_h=config.max_harmonic,
    )