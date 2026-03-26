import numpy as np

from trast_master.analysis.preprocessing import clean_finite_time_signal


def complex_fourier_coefficient(time_s: np.ndarray, signal: np.ndarray, freq_hz: float):
    time_s, signal = clean_finite_time_signal(time_s, signal)

    t_obs = time_s[-1] - time_s[0]
    if t_obs <= 0:
        return np.nan + 1j * np.nan

    tau = time_s - time_s[0]
    kernel = np.exp(-1j * 2.0 * np.pi * freq_hz * tau)
    return np.trapezoid(signal * kernel, tau) / t_obs


def all_fourier_coefficients(time_s: np.ndarray, signal: np.ndarray, f0_hz: float, max_h: int):
    return [complex_fourier_coefficient(time_s, signal, h * f0_hz) for h in range(max_h + 1)]


def build_harmonic_design_matrix(time_s: np.ndarray, f0_hz: float, max_h: int):
    time_s = np.asarray(time_s, dtype=float).ravel()
    tau = time_s - time_s[0]

    cols = [np.ones_like(tau)]
    for h in range(1, max_h + 1):
        omega_t = 2.0 * np.pi * h * f0_hz * tau
        cols.append(np.cos(omega_t))
        cols.append(np.sin(omega_t))

    return np.column_stack(cols)


def least_squares_harmonic_amplitudes(
    time_s: np.ndarray,
    signal: np.ndarray,
    f0_hz: float,
    max_h: int,
    ridge_lambda: float = 1e-8,
):
    time_s, signal = clean_finite_time_signal(time_s, signal)

    X = build_harmonic_design_matrix(time_s, f0_hz, max_h)

    finite_rows = np.all(np.isfinite(X), axis=1) & np.isfinite(signal)
    X = X[finite_rows]
    y = signal[finite_rows]

    if X.shape[0] <= X.shape[1]:
        XtX = X.T @ X
        reg = ridge_lambda * np.eye(X.shape[1])
        coef = np.linalg.solve(XtX + reg, X.T @ y)
    else:
        try:
            coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        except np.linalg.LinAlgError:
            XtX = X.T @ X
            reg = ridge_lambda * np.eye(X.shape[1])
            coef = np.linalg.solve(XtX + reg, X.T @ y)

    beta0 = float(coef[0])

    amps = []
    idx = 1
    for _h in range(1, max_h + 1):
        a_h = float(coef[idx])
        b_h = float(coef[idx + 1])
        amps.append(np.sqrt(a_h * a_h + b_h * b_h))
        idx += 2

    return np.asarray(amps, dtype=float), beta0