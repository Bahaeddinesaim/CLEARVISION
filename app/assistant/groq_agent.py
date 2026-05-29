from __future__ import annotations

from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
import json

import pandas as pd


GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "llama-3.1-8b-instant"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _compact_records(df: pd.DataFrame, limit: int = 6) -> list[dict[str, Any]]:
    """Return a small JSON-safe sample from a dataframe."""
    if df.empty:
        return []
    sample = df.head(limit).copy()
    return json.loads(sample.to_json(orient="records", force_ascii=False, date_format="iso"))


def build_classvision_context(
    datasets: dict[str, pd.DataFrame],
    rules: dict[str, Any],
    score: float,
    profile: dict[str, str],
    weather: dict[str, Any] | None = None,
) -> str:
    """Build a concise app context for the assistant."""
    inv = datasets.get("gold_inventory", pd.DataFrame())
    anom = datasets.get("gold_anomalies", pd.DataFrame())
    quality = datasets.get("gold_quality_score", pd.DataFrame())
    raw = datasets.get("raw", pd.DataFrame())

    context = {
        "application": "ClassVision AI",
        "purpose": "Analyse de salle de classe: objets, presence, anomalies, qualite data, bruit audio et meteo.",
        "current_score": score,
        "score_profile": profile,
        "rules": rules,
        "counts": {
            "raw_rows": int(len(raw)),
            "unique_photo_analyses": int(raw["analysis_id"].nunique()) if not raw.empty and "analysis_id" in raw else 0,
            "inventory_rows": int(len(inv)),
            "anomaly_rows": int(len(anom)),
        },
        "latest_quality": _compact_records(quality, 1),
        "latest_inventory": _compact_records(inv, 12),
        "latest_anomalies": _compact_records(anom, 12),
        "weather": weather or {},
    }
    return json.dumps(context, ensure_ascii=False, indent=2)


def answer_locally(question: str, app_context: str) -> str:
    """Answer common ClassVision questions without an external LLM."""
    context = json.loads(app_context)
    lower_question = question.lower()
    score = float(context.get("current_score", 0) or 0)
    profile = context.get("score_profile", {})
    counts = context.get("counts", {})
    anomalies = context.get("latest_anomalies", [])
    inventory = context.get("latest_inventory", [])
    quality = context.get("latest_quality", [])
    weather = context.get("weather", {})

    if "anomal" in lower_question:
        if not anomalies:
            return "Je ne vois pas d'anomalie dans la derniere analyse disponible."
        severe = sorted(anomalies, key=lambda row: str(row.get("severity", "")), reverse=True)[:5]
        lines = ["Anomalies les plus importantes detectees:"]
        for row in severe:
            anomaly_type = str(row.get("anomaly_type", "anomalie")).replace("_", " ")
            object_type = row.get("object_type", "global")
            severity = row.get("severity", "N/A")
            description = row.get("description", "Pas de description.")
            lines.append(f"- {severity}: {anomaly_type} sur {object_type}. {description}")
        lines.append("Priorite: traiter d'abord les anomalies high/critical, puis relancer une analyse photo.")
        return "\n".join(lines)

    if "clim" in lower_question or "chauffage" in lower_question or "meteo" in lower_question:
        if not weather or weather.get("status"):
            return "La meteo n'est pas disponible dans le contexte actuel."
        return (
            f"Decision meteo actuelle: {weather.get('hvac_action', 'Rien')}.\n"
            f"Temperature: {weather.get('temperature_2m', 'N/A')} C, ressenti: {weather.get('apparent_temperature', 'N/A')} C.\n"
            f"Hydratation: {weather.get('hydration_level', 'N/A')}. {weather.get('hydration_message', '')}\n"
            f"Detail: {weather.get('hvac_detail', '')}"
        )

    if "action" in lower_question or "priorit" in lower_question or "recommande" in lower_question:
        actions = []
        if score < 50:
            actions.append("Revoir les anomalies de la derniere photo, car le score global est bas.")
        if anomalies:
            actions.append("Traiter les anomalies listees dans Anomaly Center.")
        if weather.get("hydration_level") in {"Haute", "Moderee"}:
            actions.append(weather.get("hydration_message", "Prevoir une alerte hydratation."))
        if weather.get("hvac_action") in {"Climatisation", "Chauffage"}:
            actions.append(f"Action thermique: {weather.get('hvac_action')}.")
        if not actions:
            actions.append("Aucune action urgente detectee. Continuer la surveillance.")
        return "Actions prioritaires:\n- " + "\n- ".join(actions)

    detected_students = "N/A"
    if quality:
        detected_students = quality[0].get("detected_students", "N/A")
    top_inventory = ", ".join(
        f"{row.get('object_type', 'objet')}: {row.get('detected_count', 0)}" for row in inventory[:5]
    )
    return (
        f"Situation actuelle: score {score:.0f}/100, grade {profile.get('grade', 'N/A')}, "
        f"risque {profile.get('risk_level', 'N/A')}.\n"
        f"Analyses photo: {counts.get('unique_photo_analyses', 0)}. "
        f"Anomalies de la derniere photo: {counts.get('anomaly_rows', 0)}.\n"
        f"Eleves detectes: {detected_students}.\n"
        f"Inventaire principal: {top_inventory or 'aucun inventaire disponible'}.\n"
        f"Recommendation: {profile.get('recommendations', 'Aucune recommandation disponible.')}"
    )


def answer_with_groq(
    api_key: str,
    question: str,
    app_context: str,
    history: list[dict[str, str]] | None = None,
    model: str = DEFAULT_MODEL,
    timeout: int = 30,
) -> str:
    """Ask Groq's OpenAI-compatible chat completions API."""
    clean_key = api_key.strip()
    if not clean_key:
        raise ValueError("Cle API Groq manquante.")

    system_prompt = (
        "Tu es l'agent IA de ClassVision AI. Reponds en francais, avec des phrases courtes et utiles. "
        "Tu aides un responsable de classe a comprendre l'application, les analyses photo, anomalies, "
        "inventaire, score qualite, meteo, climatisation/chauffage et alertes hydratation. "
        "Base-toi seulement sur le contexte fourni. Si une donnee manque, dis-le clairement."
    )
    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Contexte applicatif actuel:\n{app_context}"},
    ]
    if history:
        messages.extend(history[-8:])
    messages.append({"role": "user", "content": question})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 700,
    }
    request = Request(
        GROQ_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {clean_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ClassVisionAI/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 401 or "invalid_api_key" in detail:
            raise ValueError(
                "Cle API Groq invalide. Cree une nouvelle cle dans console.groq.com/keys, remplace GROQ_API_KEY dans .env, puis redemarre Streamlit."
            ) from exc
        if exc.code == 403:
            raise ValueError(
                "Groq refuse la requete. Verifie que la cle API est active, qu'elle vient bien de console.groq.com, "
                "que le modele est autorise dans Project/Organization limits, et regenere la cle si elle a ete exposee."
            ) from exc
        raise ValueError(f"Erreur Groq HTTP {exc.code}: {detail[:500]}") from exc
    return str(result["choices"][0]["message"]["content"]).strip()


def answer_with_gemini(
    api_key: str,
    question: str,
    app_context: str,
    history: list[dict[str, str]] | None = None,
    model: str = DEFAULT_GEMINI_MODEL,
    timeout: int = 30,
) -> str:
    """Ask Google Gemini's generateContent REST API."""
    clean_key = api_key.strip()
    if not clean_key:
        raise ValueError("Cle API Gemini manquante.")

    system_prompt = (
        "Tu es l'agent IA de ClassVision AI. Reponds en francais, avec des phrases courtes et utiles. "
        "Base-toi seulement sur le contexte fourni. Si une donnee manque, dis-le clairement."
    )
    history_text = ""
    if history:
        history_text = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history[-8:])
    prompt = (
        f"{system_prompt}\n\n"
        f"Contexte applicatif actuel:\n{app_context}\n\n"
        f"Historique recent:\n{history_text}\n\n"
        f"Question utilisateur:\n{question}"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
    }
    model_name = (model or DEFAULT_GEMINI_MODEL).strip()
    if model_name.startswith("models/"):
        model_name = model_name.split("/", 1)[1]
    url = GEMINI_API_URL.format(model=quote(model_name, safe="")) + f"?key={quote(clean_key, safe='')}"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ClassVisionAI/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 404:
            raise ValueError(
                "Modele Gemini indisponible. Utilise GEMINI_MODEL=gemini-2.5-flash dans .env, puis redemarre Streamlit."
            ) from exc
        if exc.code in {400, 401, 403}:
            raise ValueError(
                "Gemini refuse la requete. Verifie GEMINI_API_KEY, le modele choisi et les restrictions de cle dans Google AI Studio."
            ) from exc
        raise ValueError(f"Erreur Gemini HTTP {exc.code}: {detail[:500]}") from exc

    candidates = result.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini n'a retourne aucune reponse.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "\n".join(str(part.get("text", "")).strip() for part in parts if part.get("text"))
    if not text:
        raise ValueError("Gemini a retourne une reponse vide.")
    return text.strip()
