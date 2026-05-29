from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
import json

import pandas as pd


KREMLIN_BICETRE = {
    "name": "Le Kremlin-Bicetre",
    "latitude": 48.8147,
    "longitude": 2.3619,
    "timezone": "Europe/Paris",
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _weather_code_label(code: int | float | None) -> str:
    labels = {
        0: "Ciel clair",
        1: "Principalement clair",
        2: "Partiellement nuageux",
        3: "Couvert",
        45: "Brouillard",
        48: "Brouillard givrant",
        51: "Bruine faible",
        53: "Bruine moderee",
        55: "Bruine dense",
        61: "Pluie faible",
        63: "Pluie moderee",
        65: "Pluie forte",
        71: "Neige faible",
        73: "Neige moderee",
        75: "Neige forte",
        80: "Averses faibles",
        81: "Averses moderees",
        82: "Averses fortes",
        95: "Orage",
        96: "Orage avec grele",
        99: "Orage violent avec grele",
    }
    try:
        return labels.get(int(code), "Meteo variable")
    except (TypeError, ValueError):
        return "Meteo inconnue"


def fetch_kremlin_bicetre_forecast(timeout: int = 12) -> dict[str, Any]:
    """Fetch 7-day hourly and daily forecast from Open-Meteo."""
    params = {
        "latitude": KREMLIN_BICETRE["latitude"],
        "longitude": KREMLIN_BICETRE["longitude"],
        "timezone": KREMLIN_BICETRE["timezone"],
        "forecast_days": 7,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,weather_code",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,precipitation,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,weather_code",
    }
    url = f"{OPEN_METEO_URL}?{urlencode(params)}"
    with urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def hvac_decision(apparent_temperature: float | int | None, humidity: float | int | None = None) -> tuple[str, str]:
    """Return classroom HVAC action and operational detail."""
    feels_like = float(apparent_temperature) if apparent_temperature is not None else 20.0
    rel_humidity = float(humidity) if humidity is not None else 50.0
    if feels_like >= 27:
        return "Climatisation", "Allumer la climatisation et aerer avant l'arrivee si possible."
    if feels_like >= 25 and rel_humidity >= 65:
        return "Climatisation", "Ressenti humide: privilegier climatisation douce ou ventilation."
    if feels_like <= 17:
        return "Chauffage", "Allumer le chauffage pour stabiliser la salle avant le cours."
    return "Rien", "Aucune action thermique prioritaire."


def hydration_alert(apparent_temperature: float | int | None, humidity: float | int | None) -> tuple[str, str]:
    """Return hydration alert level and message."""
    feels_like = float(apparent_temperature) if apparent_temperature is not None else 20.0
    rel_humidity = float(humidity) if humidity is not None else 50.0
    if feels_like >= 30 or (feels_like >= 27 and rel_humidity >= 60):
        return "Haute", "Alerte hydratation: rappeler aux eleves de boire et limiter les efforts."
    if feels_like >= 25:
        return "Moderee", "Prevoir une pause hydratation et surveiller les signes de fatigue."
    return "Normale", "Pas d'alerte hydratation particuliere."


def hourly_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert Open-Meteo hourly payload to enriched dataframe."""
    hourly = payload.get("hourly", {})
    df = pd.DataFrame(hourly)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    df["weather_label"] = df["weather_code"].map(_weather_code_label)
    decisions = df.apply(
        lambda row: hvac_decision(row.get("apparent_temperature"), row.get("relative_humidity_2m")),
        axis=1,
        result_type="expand",
    )
    df["hvac_action"] = decisions[0]
    df["hvac_detail"] = decisions[1]
    hydration = df.apply(
        lambda row: hydration_alert(row.get("apparent_temperature"), row.get("relative_humidity_2m")),
        axis=1,
        result_type="expand",
    )
    df["hydration_level"] = hydration[0]
    df["hydration_message"] = hydration[1]
    return df


def daily_dataframe(payload: dict[str, Any]) -> pd.DataFrame:
    """Convert Open-Meteo daily payload to enriched dataframe."""
    daily = payload.get("daily", {})
    df = pd.DataFrame(daily)
    if df.empty:
        return df
    df["time"] = pd.to_datetime(df["time"])
    df["weather_label"] = df["weather_code"].map(_weather_code_label)
    decisions = df.apply(lambda row: hvac_decision(row.get("apparent_temperature_max")), axis=1, result_type="expand")
    df["hvac_action"] = decisions[0]
    df["hvac_detail"] = decisions[1]
    hydration = df.apply(lambda row: hydration_alert(row.get("apparent_temperature_max"), 55), axis=1, result_type="expand")
    df["hydration_level"] = hydration[0]
    df["hydration_message"] = hydration[1]
    return df


def prediction_targets(hourly_df: pd.DataFrame, daily_df: pd.DataFrame) -> pd.DataFrame:
    """Build H+1, H+5, J+1 and J+7 decision targets."""
    rows: list[pd.Series] = []
    if not hourly_df.empty:
        for label, idx in [("H+1", 1), ("H+5", 5)]:
            if len(hourly_df) > idx:
                row = hourly_df.iloc[idx].copy()
                row["horizon"] = label
                rows.append(row)
    if not daily_df.empty:
        for label, idx in [("J+1", 1), ("J+7", min(6, len(daily_df) - 1))]:
            if len(daily_df) > idx:
                row = daily_df.iloc[idx].copy()
                row["horizon"] = label
                rows.append(row)
    return pd.DataFrame(rows)


def current_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return current weather enriched with decisions."""
    current = payload.get("current", {})
    action, detail = hvac_decision(current.get("apparent_temperature"), current.get("relative_humidity_2m"))
    hydration, hydration_message = hydration_alert(current.get("apparent_temperature"), current.get("relative_humidity_2m"))
    return {
        **current,
        "weather_label": _weather_code_label(current.get("weather_code")),
        "hvac_action": action,
        "hvac_detail": detail,
        "hydration_level": hydration,
        "hydration_message": hydration_message,
        "location": KREMLIN_BICETRE["name"],
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
