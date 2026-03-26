import glob
import os
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from trast_master.config import AcquisitionRecord
from trast_master.utils.paths import parse_pulsewidth_from_filename


def safe_scalar(x: Any) -> Any:
    arr = np.asarray(x)
    if arr.shape == ():
        return arr.item()
    return x


def find_npz_files(target: str) -> List[str]:
    if not target:
        raise ValueError("Analysis target is empty.")

    if os.path.isfile(target):
        if not target.lower().endswith(".npz"):
            raise ValueError(f"Selected file is not a .npz file: {target}")
        return [target]

    if os.path.isdir(target):
        pattern = os.path.join(target, "*.npz")
        files = sorted(glob.glob(pattern))
        detector_files = [f for f in files if os.path.basename(f).startswith("detector_pw_")]
        return detector_files if detector_files else files

    raise ValueError(f"Analysis target does not exist: {target}")


def load_detector_npz(path: str):
    meta: Dict[str, Any] = {
        "pulse_width_s": None,
        "duty_fraction": None,
        "frequency_hz": None,
        "num_periods_to_capture": None,
    }

    data = np.load(path, allow_pickle=False)

    if all(k in data.files for k in ("time", "detector")):
        time_s = np.asarray(data["time"], dtype=float).ravel()
        detector = np.asarray(data["detector"], dtype=float).ravel()

        if "pulse_width" in data.files:
            meta["pulse_width_s"] = float(safe_scalar(data["pulse_width"]))
        if "duty" in data.files:
            meta["duty_fraction"] = float(safe_scalar(data["duty"])) / 100.0
        if "frequency" in data.files:
            meta["frequency_hz"] = float(safe_scalar(data["frequency"]))
        if "num_periods_to_capture" in data.files:
            meta["num_periods_to_capture"] = float(safe_scalar(data["num_periods_to_capture"]))

        return time_s, detector, meta

    if ("Time (s)" in data.files and "Channel B (V)" in data.files):
        time_s = np.asarray(data["Time (s)"], dtype=float).ravel()
        detector = np.asarray(data["Channel B (V)"], dtype=float).ravel()
        return time_s, detector, meta

    if len(data.files) == 1:
        key = data.files[0]
        arr = data[key]
        if getattr(arr, "dtype", None) is not None and getattr(arr.dtype, "names", None):
            names = arr.dtype.names
            if ("Time (s)" in names and "Channel B (V)" in names):
                time_s = np.asarray(arr["Time (s)"], dtype=float).ravel()
                detector = np.asarray(arr["Channel B (V)"], dtype=float).ravel()
                return time_s, detector, meta

    raise ValueError(
        f"File {os.path.basename(path)} doesn't contain recognized detector fields. "
        f"Available keys: {list(data.files)}"
    )


def infer_pw_duty_f0(meta: Dict[str, Any], path: str, default_duty_fraction: float = 0.01):
    pw = meta.get("pulse_width_s")
    if pw is None:
        parsed = parse_pulsewidth_from_filename(path)
        if isinstance(parsed, tuple):
            pw = parsed[0]
        else:
            pw = parsed

    duty = meta.get("duty_fraction")
    if duty is None:
        duty = default_duty_fraction

    f0 = meta.get("frequency_hz")
    if f0 is None and pw is not None and duty > 0:
        f0 = duty / pw

    return pw, duty, f0


def derive_acquisition_record(
    path: str,
    default_duty_fraction: float = 0.01,
    acquisition_periods: float = 20.0,
) -> AcquisitionRecord:
    time_s, _detector, meta = load_detector_npz(path)
    pw, duty, f0 = infer_pw_duty_f0(meta, path, default_duty_fraction=default_duty_fraction)

    time_s = np.asarray(time_s, dtype=float).ravel()
    time_s = time_s[np.isfinite(time_s)]

    n_samples = int(len(time_s)) if len(time_s) > 0 else None

    if len(time_s) >= 2:
        dt_s = float(np.mean(np.diff(time_s)))
        t_obs_s = float(time_s[-1] - time_s[0])
    else:
        dt_s = np.nan
        t_obs_s = np.nan

    fs_hz = (1.0 / dt_s) if np.isfinite(dt_s) and dt_s != 0 else np.nan
    nyquist_hz = fs_hz / 2.0 if np.isfinite(fs_hz) else np.nan

    T0 = (1.0 / f0) if f0 not in (None, 0) else None
    samples_per_period = (T0 / dt_s) if (T0 not in (None, 0) and np.isfinite(dt_s) and dt_s != 0) else np.nan
    periods_observed = (t_obs_s / T0) if (T0 not in (None, 0) and np.isfinite(t_obs_s)) else np.nan

    periods_from_file = meta.get("num_periods_to_capture")
    if periods_from_file is None:
        periods_from_file = acquisition_periods

    expected_t_obs = periods_from_file * T0 if T0 is not None else None
    relerr = (
        (t_obs_s - expected_t_obs) / expected_t_obs
        if (expected_t_obs not in (None, 0) and np.isfinite(t_obs_s))
        else np.nan
    )

    return AcquisitionRecord(
        file=os.path.basename(path),
        pulse_width_s=pw,
        pulse_width_ns=(pw * 1e9) if pw is not None else None,
        duty_cycle_fraction=duty,
        fundamental_frequency_hz=f0,
        modulation_period_s=T0,
        t_obs_s=t_obs_s,
        dt_s=dt_s,
        fs_hz=fs_hz,
        nyquist_hz=nyquist_hz,
        n_samples=n_samples,
        samples_per_period=samples_per_period,
        periods_observed=periods_observed,
        expected_t_obs_s=expected_t_obs,
        t_obs_vs_expected_relerr=relerr,
        periods_expected=periods_from_file,
    )


def build_acquisition_summary(
    files: List[str],
    default_duty_fraction: float = 0.01,
    acquisition_periods: float = 20.0,
) -> pd.DataFrame:
    records = [
        asdict(
            derive_acquisition_record(
                path=f,
                default_duty_fraction=default_duty_fraction,
                acquisition_periods=acquisition_periods,
            )
        )
        for f in files
    ]
    return pd.DataFrame(records).sort_values("pulse_width_s").reset_index(drop=True)