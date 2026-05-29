from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import shutil
from uuid import uuid4

import pandas as pd
from PIL import Image
import plotly.express as px
import streamlit as st

from app.core.settings import DATA_DIR, ensure_directories, load_env_file
from app.audio.noise import analysis_to_dataframe, analyze_noise, waveform_preview
from app.assistant.groq_agent import DEFAULT_GEMINI_MODEL, answer_locally, answer_with_gemini, build_classvision_context
from app.dashboards.charts import anomalies_pie, data_quality_bar, history_line, inventory_bar, score_gauge
from app.data.database import init_db, persist_all
from app.data.pipeline import DEFAULT_CLASSROOM_RULES, build_photo_gold, load_current_datasets, run_medallion_pipeline
from app.data.simulator import generate_demo_data
from app.governance.catalog import build_data_catalog
from app.ui.components import anomaly_cards, card, detected_objects_panel, health_panel, hero, horizontal_nav, kpi, pipeline_panel, section, severity_badge
from app.ui.styles import DARK_CSS, PREMIUM_CSS
from app.utils.io import prepend_csv, safe_read_csv
from app.vision.detector import detect_objects
from app.weather.prediction import current_summary, daily_dataframe, fetch_kremlin_bicetre_forecast, hourly_dataframe, prediction_targets

PAGES = [
    "Executive Dashboard",
    "Detection Studio",
    "Audio Noise Detection",
    "Prediction Meteo",
    "Assistant IA",
    "Inventory Analytics",
    "Anomaly Center",
    "Governance Center",
    "Data Catalog",
    "Historical Analyses",
    "Data Quality",
    "Settings",
]

st.set_page_config(page_title="ClassVision AI", page_icon="CV", layout="wide", initial_sidebar_state="expanded")
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
load_env_file()
ensure_directories()
init_db()


def bootstrap_state() -> None:
    """Initialize app session state and persisted demo data."""
    if "demo" not in st.session_state:
        st.session_state["demo"] = generate_demo_data(100, 60)
    if "rules" not in st.session_state:
        st.session_state["rules"] = DEFAULT_CLASSROOM_RULES.copy()
    if "datasets" not in st.session_state:
        current = load_datasets_with_photo_gold(st.session_state["rules"])
        if current["raw"].empty:
            sample_raw = pd.DataFrame(
                [
                    {
                        "analysis_id": "demo-bootstrap",
                        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
                        "image_name": "demo_room.jpg",
                        "image_path": "demo",
                        "annotated_image_path": "demo",
                        "object_type": obj,
                        "raw_class": "demo",
                        "confidence": 0.88,
                        "x1": 0,
                        "y1": 0,
                        "x2": 10,
                        "y2": 10,
                        "area": 100,
                    }
                    for obj in ["table"] * 6
                    + ["chaise"] * 12
                    + ["eleve"] * 9
                    + ["tableau", "porte", "fenetre", "poubelle", "bureau", "pc", "pc", "projecteur"]
                ]
            )
            st.session_state["datasets"] = run_medallion_pipeline(sample_raw, append=False, rules=st.session_state["rules"])
        else:
            st.session_state["datasets"] = current
        st.session_state["catalog"] = build_data_catalog(st.session_state["datasets"])
        persist_all({**st.session_state["datasets"], "data_catalog": st.session_state["catalog"]})


def save_uploaded_file(file, default_ext: str = ".jpg") -> tuple[str, Path]:
    """Persist the uploaded image/camera capture and return its analysis identifier."""
    filename = getattr(file, "name", "") or f"capture{default_ext}"
    ext = Path(filename).suffix.lower() or default_ext
    analysis_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:8]
    image_path = DATA_DIR / "raw" / "uploads" / f"{analysis_id}{ext}"
    image_path.write_bytes(file.getbuffer())
    return analysis_id, image_path


def audio_mime(filename: str) -> str:
    """Return a browser audio MIME type from a filename."""
    suffix = Path(filename).suffix.lower()
    return {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".wav": "audio/wav",
    }.get(suffix, "audio/wav")


@st.cache_data(ttl=900, show_spinner=False)
def cached_weather_forecast() -> dict:
    """Cache weather data briefly to avoid excessive Open-Meteo calls."""
    return fetch_kremlin_bicetre_forecast()


def register_image(analysis_id: str, image_path: Path, annotated_path: str, detections_count: int) -> pd.DataFrame:
    """Append the image analysis registry without overwriting history."""
    row = pd.DataFrame(
        [
            {
                "analysis_id": analysis_id,
                "analyzed_at": datetime.now().isoformat(timespec="seconds"),
                "original_filename": image_path.name,
                "image_path": str(image_path),
                "annotated_image_path": str(annotated_path),
                "detections_count": detections_count,
            }
        ]
    )
    return prepend_csv(row, DATA_DIR / "raw" / "image_registry.csv", dedupe_subset=["analysis_id"])


def load_datasets_with_photo_gold(rules: dict) -> dict[str, pd.DataFrame]:
    """Load historical datasets and recompute GOLD for the latest photo only."""
    current = load_current_datasets()
    raw_df = current.get("raw", pd.DataFrame())
    if not raw_df.empty and "analysis_id" in raw_df.columns:
        latest_id = str(raw_df["analysis_id"].iloc[0])
        latest_raw = raw_df[raw_df["analysis_id"].astype(str).eq(latest_id)].copy()
        current.update(build_photo_gold(latest_raw, rules))
    return current


def current_score(datasets: dict[str, pd.DataFrame]) -> float:
    """Return the latest health score."""
    q = datasets.get("gold_quality_score", pd.DataFrame())
    return float(q["score"].iloc[0]) if not q.empty and "score" in q else 0.0


def score_profile(datasets: dict[str, pd.DataFrame]) -> dict[str, str]:
    """Return score metadata for compact UI rendering."""
    q = datasets.get("gold_quality_score", pd.DataFrame())
    if q.empty:
        return {"grade": "N/A", "risk_level": "N/A", "recommendations": "Aucune recommandation disponible."}
    row = q.iloc[0]
    return {
        "grade": str(row.get("grade", "N/A")),
        "risk_level": str(row.get("risk_level", "N/A")),
        "recommendations": str(row.get("recommendations", "Aucune recommandation disponible.")),
    }


def pct(value: object) -> float:
    """Convert ratio-like values to a percentage for UI widgets."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number * 100 if number <= 1 else number


def inventory_cards(inv_df: pd.DataFrame) -> list[dict]:
    """Convert inventory rows into premium object list items."""
    tones = ["blue", "violet", "green", "amber"]
    rows: list[dict] = []
    if inv_df.empty:
        return rows
    for idx, row in inv_df.head(7).reset_index(drop=True).iterrows():
        expected = int(row.get("expected_count", 0) or 0)
        detected = int(row.get("detected_count", 0) or 0)
        avg_conf = pct(row.get("avg_confidence", 0))
        label = str(row.get("object_type", "object")).title()
        sub = f"Expected {expected}" if expected else "Observed only"
        rows.append({"name": label, "count": detected, "sub": sub, "confidence": avg_conf, "tone": tones[idx % len(tones)]})
    return rows


def anomaly_card_rows(anom_df: pd.DataFrame) -> list[dict]:
    """Convert anomaly rows into visual cards."""
    if anom_df.empty:
        return []
    rows: list[dict] = []
    for _, row in anom_df.head(6).iterrows():
        rows.append(
            {
                "severity": str(row.get("severity", "low")),
                "title": str(row.get("anomaly_type", "anomaly")).replace("_", " ").title(),
                "description": str(row.get("description", "")),
                "meta": f"{row.get('object_type', 'global')} · confidence {pct(row.get('confidence', 0)):.0f}%",
            }
        )
    return rows


def update_rules_from_sidebar(confidence: float) -> dict:
    """Synchronize classroom rules from interactive controls."""
    rules = st.session_state["rules"].copy()
    rules["min_confidence"] = confidence
    st.session_state["rules"] = rules
    return rules


bootstrap_state()

query_page = st.query_params.get("page", "Executive Dashboard")
if query_page not in PAGES:
    query_page = "Executive Dashboard"

with st.sidebar:
    st.markdown("### ClassVision AI")
    st.caption("Vision · Attendance · Governance")
    page = st.radio("Navigation", PAGES, index=PAGES.index(query_page), label_visibility="collapsed")
    st.divider()
    mode = st.toggle("Dark mode", value=False)
    conf = st.slider("Seuil confiance IA", 0.05, 0.95, float(st.session_state["rules"]["min_confidence"]), 0.05)
    expected_students = st.number_input("Eleves attendus aujourd'hui", min_value=0, max_value=60, value=int(st.session_state["rules"]["expected_students"]))
    expected_teacher = st.number_input("Enseignants attendus", min_value=0, max_value=5, value=int(st.session_state["rules"]["expected_teacher"]))
    tv_required = st.toggle("TV obligatoire", value=bool(st.session_state["rules"]["tv_required"]))
    projector_required = st.toggle("Projecteur obligatoire", value=bool(st.session_state["rules"]["projector_required"]))
    window_closed = st.toggle("Fenetre doit etre fermee", value=bool(st.session_state["rules"]["window_should_be_closed"]))
    st.session_state["rules"].update(
        {
            "expected_students": int(expected_students),
            "expected_teacher": int(expected_teacher),
            "tv_required": bool(tv_required),
            "projector_required": bool(projector_required),
            "window_should_be_closed": bool(window_closed),
        }
    )
    st.caption("Les nouvelles analyses sont ajoutees en haut des CSV.")
    if st.button("Recharger depuis CSV"):
        st.session_state["datasets"] = load_datasets_with_photo_gold(st.session_state["rules"])
        st.session_state["catalog"] = build_data_catalog(st.session_state["datasets"])
        st.success("Donnees rechargees.")

if mode:
    st.markdown(DARK_CSS, unsafe_allow_html=True)

rules = update_rules_from_sidebar(conf)
datasets = st.session_state["datasets"]
demo = st.session_state["demo"]
inv = datasets.get("gold_inventory", pd.DataFrame())
anom = datasets.get("gold_anomalies", pd.DataFrame())
quality = datasets.get("gold_quality_score", pd.DataFrame())
raw = datasets.get("raw", pd.DataFrame())
score = current_score(datasets)
profile = score_profile(datasets)
image_registry = safe_read_csv(DATA_DIR / "raw" / "image_registry.csv")
analysis_count = raw.get("analysis_id", pd.Series(dtype=str)).nunique() if not raw.empty else 0

hero(score=score, analyses=int(analysis_count), anomalies=len(anom))
horizontal_nav(page, PAGES)

if page == "Executive Dashboard":
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Health Score", f"{score:.0f}/100", f"Grade {profile['grade']} · Risk {profile['risk_level']}", "S")
    with c2:
        kpi("Presence", f"{quality.get('detected_students', pd.Series([0])).iloc[0] if not quality.empty else 0}/{rules['expected_students']}", "photo courante", "P")
    with c3:
        kpi("Objets", int(inv.get("detected_count", pd.Series([0])).sum()), "photo courante", "O")
    with c4:
        kpi("Anomalies", len(anom), "sur la derniere photo", "!")

    qrow = quality.iloc[0] if not quality.empty else {}
    left, mid, right = st.columns([0.92, 1.08, 1.0])
    with left:
        health_panel(
            score=score,
            grade=profile["grade"],
            risk=profile["risk_level"],
            inventory=pct(qrow.get("inventory_compliance", 0)),
            conformity=pct(qrow.get("equipment_availability", 0)),
            confidence=pct(qrow.get("avg_detection_confidence", 0)),
            occupancy=pct(qrow.get("occupancy_consistency", 0)),
        )
    with mid:
        detected_objects_panel(inventory_cards(inv), int(inv.get("detected_count", pd.Series([0])).sum()))
    with right:
        pipeline_panel(
            len(datasets.get("raw", pd.DataFrame())),
            len(datasets.get("bronze", pd.DataFrame())),
            len(datasets.get("silver", pd.DataFrame())),
            len(inv) + len(anom) + len(quality),
        )
    anomaly_cards(anomaly_card_rows(anom))
    section("Vue operationnelle", "Inventaire, risque et qualite de detection de la derniere photo analysee.")
    chart_left, chart_right = st.columns([1, 1])
    with chart_left:
        st.plotly_chart(inventory_bar(inv), use_container_width=True)
    with chart_right:
        st.plotly_chart(history_line(demo["demo_history"].head(700)), use_container_width=True)
    card("Recommendation IA", profile["recommendations"])

elif page == "Detection Studio":
    section("Detection Studio", "Importe une photo, applique les contraintes du jour et conserve l'historique complet.")
    r1, r2, r3 = st.columns(3)
    with r1:
        kpi("Eleves attendus", rules["expected_students"], "contrainte du jour", "11")
    with r2:
        kpi("Seuil IA", f"{rules['min_confidence']:.2f}", "filtrage confiance", "%")
    with r3:
        kpi("Equipements requis", ("TV + Projecteur" if rules["tv_required"] and rules["projector_required"] else "Personnalise"), "regles salle", "OK")

    upload_tab, camera_tab = st.tabs(["Importer", "Camera"])
    with upload_tab:
        uploaded_photo = st.file_uploader("Photo de salle de classe", type=["jpg", "jpeg", "png", "webp"])
    with camera_tab:
        captured_photo = st.camera_input("Prendre une photo avec l'appareil photo")

    image_file = captured_photo or uploaded_photo
    if image_file:
        analysis_id, image_path = save_uploaded_file(image_file)
        with st.spinner("Analyse IA, anomalies et pipeline data en cours..."):
            new_raw, annotated_path = detect_objects(image_path, float(rules["min_confidence"]))
            annotated_target = DATA_DIR / "raw" / "annotated" / f"annotated_{image_path.name}"
            try:
                shutil.copyfile(annotated_path, annotated_target)
                annotated_path = str(annotated_target)
            except Exception:
                annotated_path = str(annotated_path)

            analyzed_at = datetime.now().isoformat(timespec="seconds")
            new_raw.insert(0, "analysis_id", analysis_id)
            new_raw.insert(1, "analyzed_at", analyzed_at)
            new_raw["image_path"] = str(image_path)
            new_raw["annotated_image_path"] = annotated_path

            results = run_medallion_pipeline(new_raw, append=True, rules=rules)
            catalog = build_data_catalog(results)
            persist_all({**results, "data_catalog": catalog})
            register_image(analysis_id, image_path, annotated_path, len(new_raw))
            st.session_state["datasets"] = results
            st.session_state["catalog"] = catalog

        st.success(f"Analyse sauvegardee: {len(new_raw)} objets detectes. Les anomalies ci-dessous concernent uniquement cette photo.")
        m1, m2, m3 = st.columns(3)
        with m1:
            kpi("Analyse ID", analysis_id[-8:], "reference unique", "#")
        with m2:
            kpi("Detections", len(new_raw), "objets trouves", "O")
        with m3:
            kpi("CSV total", len(results.get("raw", pd.DataFrame())), "lignes historiques", "N")
        col1, col2 = st.columns(2)
        with col1:
            st.image(Image.open(image_path), caption="Image originale sauvegardee", use_container_width=True)
        with col2:
            st.image(annotated_path, caption="Detection IA annotee sauvegardee", use_container_width=True)
        section("Nouvelles detections")
        st.dataframe(new_raw, use_container_width=True)
        latest_anom = results.get("gold_anomalies", pd.DataFrame())
        section("Anomalies de cette photo", "Diagnostic calcule uniquement sur l'image que tu viens d'importer.")
        if latest_anom.empty:
            st.success("Aucune anomalie detectee sur cette photo.")
        else:
            display = latest_anom.copy()
            display["severity_badge"] = display["severity"].map(severity_badge)
            st.markdown(
                "<div class='anomaly-table'>"
                + display[["anomaly_type", "object_type", "severity_badge", "description", "confidence"]].to_html(escape=False, index=False)
                + "</div>",
                unsafe_allow_html=True,
            )
        st.download_button("Telecharger raw_detections.csv", results["raw"].to_csv(index=False).encode("utf-8"), "raw_detections.csv")
    else:
        card("Pret pour l'analyse", "Importe une photo ou prends une capture camera. L'image originale, l'image annotee, les CSV, SQLite et le catalogue seront mis a jour sans supprimer l'historique.")

elif page == "Audio Noise Detection":
    section("Audio Noise Detection", "Analyse du bruit ambiant par traitement du signal. Le fichier audio est traite en memoire et n'est pas sauvegarde.")
    a1, a2, a3 = st.columns(3)
    with a1:
        kpi("Formats", "WAV/MP3+", "upload ou micro", "A")
    with a2:
        kpi("Mode", "In-memory", "aucune sauvegarde audio", "M")
    with a3:
        kpi("Decision", "Low/Medium/High", "score de bruit", "N")

    audio_upload_tab, audio_record_tab = st.tabs(["Importer", "Micro"])
    with audio_upload_tab:
        uploaded_audio = st.file_uploader(
            "Importer un enregistrement audio de la classe",
            type=["wav", "mp3", "m4a", "ogg", "flac"],
        )
    with audio_record_tab:
        recorded_audio = st.audio_input("Enregistrer avec le micro")

    audio_file = recorded_audio or uploaded_audio
    if audio_file:
        audio_bytes = audio_file.getvalue()
        audio_name = getattr(audio_file, "name", "") or "microphone.wav"
        st.audio(audio_bytes, format=audio_mime(audio_name))
        try:
            result = analyze_noise(audio_bytes, audio_name)
            result_df = analysis_to_dataframe(result)
            n1, n2, n3, n4 = st.columns(4)
            with n1:
                kpi("Noise Score", f"{result.noise_score:.0f}/100", f"niveau {result.noise_level}", "S")
            with n2:
                kpi("Bruit detecte", "Oui" if result.noise_detected else "Non", "seuil metier >= 45", "D")
            with n3:
                kpi("RMS", f"{result.rms_dbfs:.1f} dBFS", "energie moyenne", "R")
            with n4:
                kpi("Duree", f"{result.duration_seconds:.1f}s", f"{result.sample_rate} Hz", "T")

            card("Recommendation audio", result.recommendation)
            wave_df = waveform_preview(audio_bytes, audio_name)
            fig = px.line(wave_df, x="time_seconds", y="amplitude", title="Waveform preview")
            fig.update_layout(height=320, margin=dict(t=55, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(result_df, use_container_width=True)
            st.download_button(
                "Telecharger noise_analysis.csv",
                result_df.to_csv(index=False).encode("utf-8"),
                "noise_analysis.csv",
            )
        except Exception as exc:
            st.error(f"Analyse audio impossible: {exc}")
            st.info("Pour MP3/M4A/OGG/FLAC, installe les dependances du requirements.txt afin d'activer le decodeur ffmpeg.")
    else:
        card("Comment l'utiliser", "Importe un fichier audio ou enregistre 5 a 30 secondes avec le micro. L'app estime si le bruit ambiant est faible, moyen ou eleve.")

elif page == "Prediction Meteo":
    section("Prediction Meteo", "Decision climatique pour Le Kremlin-Bicetre: climatisation, chauffage, rien et alertes hydratation.")
    st.caption("Source: Open-Meteo, previsions horaires et journalieres sur 7 jours.")
    refresh_col, info_col = st.columns([0.22, 0.78])
    with refresh_col:
        if st.button("Actualiser meteo"):
            cached_weather_forecast.clear()
            st.rerun()
    with info_col:
        st.caption("Les donnees sont mises en cache 15 minutes pour garder l'app fluide.")

    try:
        weather_payload = cached_weather_forecast()
        current_weather = current_summary(weather_payload)
        hourly_weather = hourly_dataframe(weather_payload)
        daily_weather = daily_dataframe(weather_payload)
        targets = prediction_targets(hourly_weather, daily_weather)

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            kpi("Temperature", f"{current_weather.get('temperature_2m', 0):.1f} C", current_weather["weather_label"], "T")
        with p2:
            kpi("Ressenti", f"{current_weather.get('apparent_temperature', 0):.1f} C", "temperature percue", "R")
        with p3:
            kpi("Decision", current_weather["hvac_action"], current_weather["hvac_detail"], "C")
        with p4:
            kpi("Hydratation", current_weather["hydration_level"], current_weather["hydration_message"], "H")

        if not targets.empty:
            section("Alertes par horizon", "Actions recommandees pour H+1, H+5, J+1 et J+7.")
            cols = st.columns(len(targets))
            for col, (_, row) in zip(cols, targets.iterrows()):
                with col:
                    temp = row.get("apparent_temperature", row.get("apparent_temperature_max", 0))
                    label = pd.to_datetime(row.get("time")).strftime("%d/%m %H:%M")
                    kpi(str(row.get("horizon", "")), str(row.get("hvac_action", "Rien")), f"{temp:.1f} C ressenti - {label}", "!")
                    st.caption(str(row.get("hydration_message", "")))

        chart_df = hourly_weather.head(24 * 7).copy()
        if not chart_df.empty:
            chart_df["time_label"] = chart_df["time"].dt.strftime("%d/%m %H:%M")
            fig = px.line(
                chart_df,
                x="time",
                y=["temperature_2m", "apparent_temperature"],
                title="Prevision horaire temperature vs ressenti",
                labels={"value": "C", "time": "Heure", "variable": "Mesure"},
            )
            fig.update_layout(height=360, margin=dict(t=55, b=20, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

        daily_display = daily_weather.copy()
        if not daily_display.empty:
            daily_display["date"] = daily_display["time"].dt.strftime("%d/%m/%Y")
            section("Synthese J+1 a J+7")
            st.dataframe(
                daily_display[
                    [
                        "date",
                        "temperature_2m_min",
                        "temperature_2m_max",
                        "apparent_temperature_max",
                        "precipitation_sum",
                        "weather_label",
                        "hvac_action",
                        "hydration_level",
                        "hydration_message",
                    ]
                ],
                use_container_width=True,
            )

        if not hourly_weather.empty:
            detailed = hourly_weather.head(24 * 7).copy()
            detailed["time"] = detailed["time"].dt.strftime("%d/%m/%Y %H:%M")
            st.download_button(
                "Telecharger forecast_kremlin_bicetre.csv",
                detailed.to_csv(index=False).encode("utf-8"),
                "forecast_kremlin_bicetre.csv",
            )
    except Exception as exc:
        st.error(f"Prediction meteo indisponible: {exc}")
        st.info("Verifie la connexion internet du serveur Streamlit. Open-Meteo ne demande pas de cle API.")

elif page == "Assistant IA":
    section("Assistant IA", "Pose des questions sur l'etat de l'application, les analyses, anomalies, meteo et decisions operationnelles.")
    if "assistant_messages" not in st.session_state:
        st.session_state["assistant_messages"] = [
            {
                "role": "assistant",
                "content": "Bonjour. Je peux resumer la derniere analyse, expliquer les anomalies, lire la meteo et proposer une action.",
            }
        ]

    env_gemini_key = os.getenv("GEMINI_API_KEY", "")
    with st.expander("Configuration Gemini", expanded=not bool(env_gemini_key)):
        typed_gemini_key = st.text_input(
            "Cle API Gemini",
            value="",
            type="password",
            placeholder="Colle ta cle ici si GEMINI_API_KEY n'est pas configuree",
        )
        st.caption("La cle saisie ici reste en memoire de session Streamlit et n'est pas ecrite dans le projet.")

    gemini_key = typed_gemini_key or env_gemini_key
    gemini_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    weather_context = {}
    try:
        weather_context = current_summary(cached_weather_forecast())
    except Exception:
        weather_context = {"status": "meteo indisponible"}
    app_context = build_classvision_context(datasets, rules, score, profile, weather_context)

    quick1, quick2, quick3, quick4 = st.columns(4)
    quick_prompts = {
        "resume": "Resume la derniere situation de la classe.",
        "anomalies": "Quelles anomalies sont les plus importantes ?",
        "meteo": "Dois-je allumer la climatisation ou le chauffage ?",
        "actions": "Quelles actions prioritaires recommandes-tu maintenant ?",
    }
    with quick1:
        if st.button("Resume"):
            st.session_state["assistant_pending"] = quick_prompts["resume"]
    with quick2:
        if st.button("Anomalies"):
            st.session_state["assistant_pending"] = quick_prompts["anomalies"]
    with quick3:
        if st.button("Meteo"):
            st.session_state["assistant_pending"] = quick_prompts["meteo"]
    with quick4:
        if st.button("Actions"):
            st.session_state["assistant_pending"] = quick_prompts["actions"]

    for message in st.session_state["assistant_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Demande quelque chose a propos de ClassVision")
    pending_prompt = st.session_state.pop("assistant_pending", None)
    user_prompt = pending_prompt or prompt
    if user_prompt:
        st.session_state["assistant_messages"].append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)
        if not gemini_key:
            answer = "Ajoute une cle Gemini dans la configuration de cette page ou configure GEMINI_API_KEY dans .env."
        else:
            chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state["assistant_messages"]
                if msg["role"] in {"user", "assistant"}
            ]
            try:
                with st.spinner("L'agent analyse les donnees de l'application..."):
                    answer = answer_with_gemini(gemini_key, user_prompt, app_context, chat_history, model=gemini_model)
            except Exception as exc:
                fallback = answer_locally(user_prompt, app_context)
                answer = f"Gemini est indisponible: {exc}\n\nMode local:\n\n{fallback}"
        st.session_state["assistant_messages"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

elif page == "Inventory Analytics":
    section("Inventory Analytics", "Comptage, conformite et ecarts par objet.")
    st.plotly_chart(inventory_bar(inv), use_container_width=True)
    st.dataframe(inv, use_container_width=True)

elif page == "Anomaly Center":
    section("Anomaly Center", "Diagnostic de la derniere photo analysee, pas du cumul historique.")
    display_anom = anom if not anom.empty else demo["demo_anomalies"].head(50)
    if not display_anom.empty and "severity" in display_anom:
        display = display_anom.copy()
        display["severity_badge"] = display["severity"].map(severity_badge)
        st.markdown(
            "<div class='anomaly-table'>"
            + display[["anomaly_type", "object_type", "severity_badge", "description", "confidence"]].to_html(escape=False, index=False)
            + "</div>",
            unsafe_allow_html=True,
        )
    st.plotly_chart(anomalies_pie(display_anom), use_container_width=True)
    st.dataframe(display_anom, use_container_width=True)

elif page == "Governance Center":
    section("Governance Center", "Suivi du pipeline medaillon, conservation historique et catalogue automatique.")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("RAW", len(datasets.get("raw", pd.DataFrame())), "detections sources", "R")
    with c2:
        kpi("BRONZE", len(datasets.get("bronze", pd.DataFrame())), "ingestion tracee", "B")
    with c3:
        kpi("SILVER", len(datasets.get("silver", pd.DataFrame())), "nettoyage + filtre", "S")
    with c4:
        kpi("GOLD", len(inv) + len(anom) + len(quality), "analytics prets", "G")
    card("Regle critique", "Chaque analyse sauvegarde l'image originale, l'image annotee, ajoute les detections aux datasets, persiste SQLite et regenere le catalogue.")

elif page == "Data Catalog":
    section("Data Catalog", "Dictionnaire des champs genere automatiquement.")
    cat = st.session_state.get("catalog", pd.DataFrame())
    st.dataframe(cat, use_container_width=True)
    st.download_button("Telecharger data_catalog.csv", cat.to_csv(index=False).encode("utf-8"), "data_catalog.csv")

elif page == "Historical Analyses":
    section("Historical Analyses", "Toutes les photos analysees et leurs images annotees.")
    if image_registry.empty:
        st.warning("Aucune photo reelle encore analysee.")
    else:
        st.dataframe(image_registry, use_container_width=True)
        latest = image_registry.iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            if Path(str(latest.get("image_path", ""))).exists():
                st.image(str(latest["image_path"]), caption="Derniere image originale", use_container_width=True)
        with c2:
            if Path(str(latest.get("annotated_image_path", ""))).exists():
                st.image(str(latest["annotated_image_path"]), caption="Derniere image annotee", use_container_width=True)

elif page == "Data Quality":
    section("Data Quality", "Score, confiance, conformite inventaire et coherence d'occupation.")
    st.plotly_chart(data_quality_bar(quality), use_container_width=True)
    st.dataframe(quality, use_container_width=True)
    st.markdown("#### Silver dataset")
    st.dataframe(datasets.get("silver", pd.DataFrame()), use_container_width=True)

elif page == "Settings":
    section("Settings", "Contraintes metier appliquees a la prochaine analyse.")
    st.json(rules)
    all_data = {**datasets, **demo}
    tabs = st.tabs(list(all_data.keys()))
    for tab, (name, df) in zip(tabs, all_data.items()):
        with tab:
            st.caption(name)
            st.dataframe(df.head(800), use_container_width=True)
            st.download_button(f"Telecharger {name}.csv", df.to_csv(index=False).encode("utf-8"), f"{name}.csv", key=f"dl_{name}")
