from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import wave

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NoiseAnalysis:
    """Structured result for one audio noise analysis."""

    filename: str
    sample_rate: int
    duration_seconds: float
    rms_dbfs: float
    peak_dbfs: float
    zero_crossing_rate: float
    high_frequency_ratio: float
    spectral_centroid_hz: float
    noise_score: float
    noise_level: str
    noise_detected: bool
    recommendation: str


def _pcm_to_float(raw: bytes, sample_width: int, channels: int) -> np.ndarray:
    """Convert PCM WAV bytes to mono float samples in [-1, 1]."""
    if sample_width == 1:
        data = np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
        data = (data - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError("Format WAV non supporte. Utilise un fichier PCM 8, 16 ou 32 bits.")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data


def read_wav_bytes(content: bytes) -> tuple[np.ndarray, int, float]:
    """Read an in-memory WAV file and return mono samples, sample rate and duration."""
    with wave.open(BytesIO(content), "rb") as wav:
        channels = wav.getnchannels()
        sample_rate = wav.getframerate()
        sample_width = wav.getsampwidth()
        frames = wav.getnframes()
        raw = wav.readframes(frames)
    samples = _pcm_to_float(raw, sample_width, channels)
    duration = len(samples) / sample_rate if sample_rate else 0.0
    return samples, sample_rate, duration


def analyze_noise(content: bytes, filename: str) -> NoiseAnalysis:
    """Analyze classroom background noise from a WAV audio sample."""
    samples, sample_rate, duration = read_wav_bytes(content)
    if samples.size == 0 or sample_rate <= 0:
        raise ValueError("Audio vide ou invalide.")

    samples = samples[np.isfinite(samples)]
    if samples.size == 0:
        raise ValueError("Audio sans echantillons exploitables.")

    rms = float(np.sqrt(np.mean(samples**2)))
    peak = float(np.max(np.abs(samples)))
    rms_dbfs = float(20 * np.log10(max(rms, 1e-8)))
    peak_dbfs = float(20 * np.log10(max(peak, 1e-8)))
    zero_crossing_rate = float(np.mean(np.abs(np.diff(np.signbit(samples)))))

    window = samples[: min(samples.size, sample_rate * 30)]
    spectrum = np.abs(np.fft.rfft(window))
    freqs = np.fft.rfftfreq(window.size, d=1 / sample_rate)
    total_energy = float(np.sum(spectrum) + 1e-8)
    high_frequency_ratio = float(np.sum(spectrum[freqs >= 2000]) / total_energy)
    spectral_centroid_hz = float(np.sum(freqs * spectrum) / total_energy)

    loudness_component = np.interp(rms_dbfs, [-55, -16], [0, 60])
    texture_component = np.interp(high_frequency_ratio, [0.08, 0.42], [0, 25])
    zcr_component = np.interp(zero_crossing_rate, [0.03, 0.20], [0, 15])
    noise_score = round(float(np.clip(loudness_component + texture_component + zcr_component, 0, 100)), 2)

    if noise_score >= 72:
        noise_level = "High"
        recommendation = "Bruit important detecte. Verifier discussions, fenetres ouvertes, ventilateurs ou materiel audio."
    elif noise_score >= 45:
        noise_level = "Medium"
        recommendation = "Bruit modere detecte. Surveiller la classe et comparer avec un nouvel enregistrement."
    else:
        noise_level = "Low"
        recommendation = "Niveau sonore acceptable pour une salle de classe."

    return NoiseAnalysis(
        filename=filename,
        sample_rate=sample_rate,
        duration_seconds=round(duration, 2),
        rms_dbfs=round(rms_dbfs, 2),
        peak_dbfs=round(peak_dbfs, 2),
        zero_crossing_rate=round(zero_crossing_rate, 4),
        high_frequency_ratio=round(high_frequency_ratio, 4),
        spectral_centroid_hz=round(spectral_centroid_hz, 2),
        noise_score=noise_score,
        noise_level=noise_level,
        noise_detected=noise_score >= 45,
        recommendation=recommendation,
    )


def analysis_to_dataframe(result: NoiseAnalysis) -> pd.DataFrame:
    """Convert a noise analysis result to a dataframe for display/export."""
    return pd.DataFrame([result.__dict__])


def waveform_preview(content: bytes, max_points: int = 900) -> pd.DataFrame:
    """Return a downsampled waveform dataframe."""
    samples, sample_rate, _ = read_wav_bytes(content)
    if samples.size > max_points:
        idx = np.linspace(0, samples.size - 1, max_points).astype(int)
        samples = samples[idx]
    time_axis = np.arange(samples.size) / sample_rate
    return pd.DataFrame({"time_seconds": time_axis, "amplitude": samples})
