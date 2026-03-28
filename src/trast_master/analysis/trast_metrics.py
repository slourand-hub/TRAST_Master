import os
from typing import List

import numpy as np
import pandas as pd

from trast_master.analysis.loader import load_detector_npz, infer_pw_duty_f0
from trast_master.analysis.preprocessing import clean_finite_time_signal
from trast_master.analysis.fft_tools import (
    all_fourier_coefficients,
    least_squares_harmonic_amplitudes,
)


def get_x(df: pd.DataFrame, mode: str):
    if mode == "pulse_width_ns":
        return df["pulse_width_ns"].values, "Pulse width (ns)"
    if mode == "pulse_width_us":
        return df["pulse_width_us"].values, "Pulse width (µs)"
    if mode == "pulse_width_ms":
        return df["pulse_width_ms"].values, "Pulse width (ms)"
    if mode == "log_pw_s":
        return df["pulse_width_s"].values, "Pulse width (s)"
    raise ValueError(f"Unknown X_AXIS mode: {mode}")


def choose_representative_indices(n_total: int, n_pick: int):
    if n_total <= n_pick:
        return list(range(n_total))
    idx = np.linspace(0, n_total - 1, n_pick)
    idx = np.round(idx).astype(int)
    idx = np.unique(idx)
    return list(idx)

def compute_raw_diagnostics(
            files: List[str],
            max_h: int,
            default_duty_fraction: float = 0.01,
            logger=None,
    ) -> pd.DataFrame:
        rows = []

        for i, path in enumerate(files, start=1):
            if logger is not None:
                logger(f"[{i}/{len(files)}] Processing {os.path.basename(path)}")

            time_s, detector, meta = load_detector_npz(path)
            pw, duty, f0 = infer_pw_duty_f0(
                meta,
                path,
                default_duty_fraction=default_duty_fraction,
            )

            if pw is None:
                continue

            time_s, detector = clean_finite_time_signal(time_s, detector)

            t_obs = time_s[-1] - time_s[0]
            if t_obs <= 0:
                continue

            coeffs_raw = all_fourier_coefficients(time_s, detector, f0, max_h)
            abs_raw = [float(np.abs(c)) for c in coeffs_raw]
            abs_c0_raw = abs_raw[0]

            try:
                ls_amps_raw, ls_intercept_raw = least_squares_harmonic_amplitudes(
                    time_s=time_s,
                    signal=detector,
                    f0_hz=f0,
                    max_h=max_h,
                )
                ls_ok = True
            except Exception:
                ls_amps_raw = np.full(max_h, np.nan)
                ls_intercept_raw = np.nan
                ls_ok = False

            row = {
                "file": os.path.basename(path),
                "pulse_width_s": pw,
                "pulse_width_ns": pw * 1e9,
                "pulse_width_us": pw * 1e6,
                "pulse_width_ms": pw * 1e3,
                "duty_fraction": duty,
                "f0_hz": f0,
                "t_obs_s": t_obs,
                "n_samples": len(time_s),
                "dt_mean_s": np.mean(np.diff(time_s)) if len(time_s) > 1 else np.nan,
                "c0_abs_raw": abs_c0_raw,
                "ls_intercept_raw": ls_intercept_raw,
                "ls_ok": ls_ok,
            }

            for h in range(0, max_h + 1):
                row[f"c{h}_abs_raw"] = abs_raw[h]
                row[f"c{h}_over_c0_raw"] = abs_raw[h] / abs_c0_raw if abs_c0_raw > 0 else np.nan

            for H in range(1, max_h + 1):
                row[f"sum{H}_abs_raw"] = float(np.sum(abs_raw[1:H + 1]))
                row[f"sum{H}_abs_ls_raw"] = (
                    float(np.sum(ls_amps_raw[:H]))
                    if np.all(np.isfinite(ls_amps_raw[:H]))
                    else np.nan
                )

            rows.append(row)

        if not rows:
            raise RuntimeError("No usable detector traces found.")

        df = pd.DataFrame(rows).sort_values("pulse_width_s").reset_index(drop=True)

        ref_c0_raw = df.loc[0, "c0_abs_raw"]
        df["dc_trast_raw_norm"] = df["c0_abs_raw"] / ref_c0_raw

        sum_norm_cols = {}
        for H in range(1, max_h + 1):
            ref_sumH_raw = df.loc[0, f"sum{H}_abs_raw"]
            ref_sumH_ls_raw = df.loc[0, f"sum{H}_abs_ls_raw"]

            if ref_sumH_raw != 0:
                sum_norm_cols[f"sum{H}_trast_raw_norm"] = df[f"sum{H}_abs_raw"] / ref_sumH_raw
            else:
                sum_norm_cols[f"sum{H}_trast_raw_norm"] = np.nan

            if np.isfinite(ref_sumH_ls_raw) and ref_sumH_ls_raw != 0:
                sum_norm_cols[f"sum{H}_trast_ls_raw_norm"] = df[f"sum{H}_abs_ls_raw"] / ref_sumH_ls_raw
            else:
                sum_norm_cols[f"sum{H}_trast_ls_raw_norm"] = np.nan

        df = pd.concat([df, pd.DataFrame(sum_norm_cols, index=df.index)], axis=1)
        return df