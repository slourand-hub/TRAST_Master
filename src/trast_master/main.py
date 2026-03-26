from trast_master.config import Config
from trast_master.acquisition.moku_runner import run_acquisition


def run_analysis(config: Config, logger=print, block_on_plots: bool = True):
    import os
    import matplotlib.pyplot as plt

    from trast_master.analysis.loader import find_npz_files, build_acquisition_summary
    from trast_master.analysis.trast_metrics import compute_raw_diagnostics
    from trast_master.plotting.trast_curves import (
        plot_main_trast_overlay,
        plot_raw_harmonic_ratio_curves,
    )
    from trast_master.plotting.spectra import plot_raw_normalized_spectra

    plt.close("all")
    plt.ion()

    files = find_npz_files(config.folder)
    logger(f"Found {len(files)} file(s).")
    if not files:
        raise RuntimeError("No .npz files found.")

    acq_df = build_acquisition_summary(
        files,
        default_duty_fraction=config.default_duty_fraction,
        acquisition_periods=config.num_periods_to_capture,
    )

    logger("\nAcquisition comparability summary:\n")
    logger(
        acq_df[
            [
                "pulse_width_ns",
                "duty_cycle_fraction",
                "fundamental_frequency_hz",
                "dt_s",
                "fs_hz",
                "nyquist_hz",
                "n_samples",
                "t_obs_s",
                "modulation_period_s",
                "samples_per_period",
                "periods_observed",
                "periods_expected",
                "expected_t_obs_s",
                "t_obs_vs_expected_relerr",
            ]
        ].to_string(index=False)
    )

    df = compute_raw_diagnostics(
        files=files,
        max_h=config.max_harmonic,
        default_duty_fraction=config.default_duty_fraction,
    )

    preview_cols = ["pulse_width_ns", "dc_trast_raw_norm"]
    preview_cols += [f"sum{H}_trast_raw_norm" for H in config.main_fft_max_harmonics]
    if config.include_ls_trast:
        preview_cols += [f"sum{H}_trast_ls_raw_norm" for H in config.main_fft_max_harmonics]

    logger("\nRaw TRAST summary:\n")
    logger(df[preview_cols].to_string(index=False))

    if config.include_ls_trast and "ls_ok" in df.columns:
        n_fail = int((~df["ls_ok"]).sum())
        if n_fail > 0:
            logger(f"\nLeast-squares warning: LS fit failed on {n_fail} trace(s); those values were set to NaN.")

    if config.save_csv:
        out_csv = os.path.join(config.folder, "trast_output_raw.csv")
        df.to_csv(out_csv, index=False)
        logger(f"Saved CSV: {out_csv}")

        out_csv_acq = os.path.join(config.folder, "acquisition_summary.csv")
        acq_df.to_csv(out_csv_acq, index=False)
        logger(f"Saved CSV: {out_csv_acq}")

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

    logger("\nAll figures opened.")
    plt.ioff()
    plt.show(block=block_on_plots)


def main():
    config = Config()

    if config.mode == "acquire":
        run_acquisition(config)
    elif config.mode == "analyze":
        run_analysis(config)
    elif config.mode == "both":
        run_acquisition(config)
        config.folder = config.output_folder
        run_analysis(config)
    elif config.mode == "gui":
        from trast_master.gui.app import launch_gui
        launch_gui()
    else:
        raise ValueError(f"Unknown mode: {config.mode}")


if __name__ == "__main__":
    main()
