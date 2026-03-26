from dataclasses import dataclass
from typing import List, Optional


ACQUISITION_PERIODS = 20.0


@dataclass
class Config:
    mode: str = "gui"   # "acquire", "analyze", "both", "gui"

    # analysis settings
    folder: str = r"C:\Users\slour\OneDrive\Desktop\Master Thesis\LabMain\20260325_fftTRAST\Test6"
    x_axis: str = "pulse_width_us"
    default_duty_fraction: float = 0.01
    max_harmonic: int = 200
    main_fft_max_harmonics: List[int] = None
    diagnostic_harmonics: List[int] = None
    n_spectrum_pw: int = 5
    save_csv: bool = False
    include_ls_trast: bool = False

    # acquisition settings
    moku_ip: str = ""
    platform_id: int = 4
    mokucli_exe: str = r"C:\Program Files\Liquid Instruments\Moku CLI\mokucli.exe"
    output_folder: str = "data/raw"

    pulsewidths_us: List[float] = None
    duty_percent: float = 1.0
    amplitude_vpp: float = 1.0
    offset_v: float = 0.5
    num_frames_per_width: int = 1
    num_periods_to_capture: float = 20.0
    settle_time_s: float = 0.0

    frontend_channel: int = 3
    frontend_impedance: str = "50Ohm"
    frontend_coupling: str = "DC"
    frontend_attenuation: str = "0dB"
    output_gain_db: str = "14dB"

    trigger_source: str = "ChannelA"
    trigger_level_v: float = 0.2
    trigger_edge: str = "Rising"
    acquisition_mode: str = "Normal"

    plot_raw_traces: bool = False
    save_figures: bool = True
    keep_li_files: bool = True
    keep_npy_files: bool = True

    def __post_init__(self):
        if self.main_fft_max_harmonics is None:
            self.main_fft_max_harmonics = [1, 5, 10, 20]
        if self.diagnostic_harmonics is None:
            self.diagnostic_harmonics = [1, 2, 3, 5, 10, 20]
        if self.pulsewidths_us is None:
            self.pulsewidths_us = [1, 2, 5, 10, 20]


@dataclass
class AcquisitionRecord:
    file: str
    pulse_width_s: Optional[float] = None
    pulse_width_ns: Optional[float] = None
    duty_cycle_fraction: Optional[float] = None
    fundamental_frequency_hz: Optional[float] = None
    modulation_period_s: Optional[float] = None
    t_obs_s: Optional[float] = None
    dt_s: Optional[float] = None
    fs_hz: Optional[float] = None
    nyquist_hz: Optional[float] = None
    n_samples: Optional[int] = None
    samples_per_period: Optional[float] = None
    periods_observed: Optional[float] = None
    expected_t_obs_s: Optional[float] = None
    t_obs_vs_expected_relerr: Optional[float] = None
    periods_expected: Optional[float] = None