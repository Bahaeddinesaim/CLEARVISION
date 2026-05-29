from __future__ import annotations

from datetime import datetime
import numpy as np
import pandas as pd

from app.core.settings import DATA_DIR
from app.utils.io import prepend_csv, safe_read_csv, write_csv

EXPECTED = {
    "table": 6,
    "chaise": 12,
    "tableau": 1,
    "porte": 1,
    "fenetre": 2,
    "poubelle": 1,
    "bureau": 1,
    "tv": 1,
    "pc": 5,
    "projecteur": 1,
}

DEFAULT_CLASSROOM_RULES = {
    "classroom_id": "Salle principale",
    "expected_students": 11,
    "expected_teacher": 1,
    "min_confidence": 0.25,
    "tv_required": True,
    "projector_required": True,
    "window_should_be_closed": True,
    "max_objects_per_student": 4.2,
}

SEVERITY_WEIGHT = {"low": 4, "medium": 9, "high": 16, "critical": 25}


def raw_to_bronze(raw: pd.DataFrame) -> pd.DataFrame:
    """Add ingestion metadata to raw detections."""
    df = raw.copy()
    df["ingestion_timestamp"] = datetime.now().isoformat(timespec="seconds")
    df["source_system"] = "streamlit_upload_or_demo"
    df["record_hash"] = pd.util.hash_pandas_object(df.astype(str), index=False).astype(str)
    return df


def bronze_to_silver(bronze: pd.DataFrame, min_confidence: float = 0.0) -> pd.DataFrame:
    """Clean labels, normalize numeric fields and deduplicate detections."""
    df = bronze.copy()
    for col in ["object_type", "image_name"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower().str.strip()
    if "confidence" in df.columns:
        df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0).clip(0, 1)
        df = df[df["confidence"] >= min_confidence]
    subset = [c for c in ["analysis_id", "image_name", "object_type", "x1", "y1", "x2", "y2"] if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset, keep="first")
    return df


def silver_to_gold(silver: pd.DataFrame, rules: dict | None = None) -> dict[str, pd.DataFrame]:
    """Build gold inventory, anomaly and score datasets."""
    active_rules = {**DEFAULT_CLASSROOM_RULES, **(rules or {})}
    if silver.empty:
        inv = pd.DataFrame(columns=["object_type", "detected_count", "expected_count", "delta", "compliance_rate"])
    else:
        inv = silver.groupby("object_type", as_index=False).agg(
            detected_count=("object_type", "count"),
            avg_confidence=("confidence", "mean"),
            images_count=("image_name", "nunique"),
            total_area=("area", "sum"),
        )
        inv["expected_count"] = inv["object_type"].map(EXPECTED).fillna(0).astype(int)
        inv["delta"] = inv["detected_count"] - inv["expected_count"]
        inv["compliance_rate"] = np.where(
            inv["expected_count"] > 0,
            np.minimum(inv["detected_count"] / inv["expected_count"], 1),
            1,
        )
        inv = inv.sort_values("detected_count", ascending=False)
    anomalies = detect_anomalies(inv, silver, active_rules)
    quality = compute_quality_score(inv, anomalies, silver, active_rules)
    return {"gold_inventory": inv, "gold_anomalies": anomalies, "gold_quality_score": quality}


def build_photo_gold(raw: pd.DataFrame, rules: dict | None = None) -> dict[str, pd.DataFrame]:
    """Build GOLD outputs scoped to one photo or one analysis batch."""
    active_rules = {**DEFAULT_CLASSROOM_RULES, **(rules or {})}
    bronze = raw_to_bronze(raw.copy())
    silver = bronze_to_silver(bronze, min_confidence=float(active_rules["min_confidence"]))
    return silver_to_gold(silver, active_rules)


def _count_object(silver: pd.DataFrame, *names: str) -> int:
    if silver.empty or "object_type" not in silver:
        return 0
    return int(silver["object_type"].isin([n.lower() for n in names]).sum())


def _add_anomaly(rows: list[dict], anomaly_type: str, object_type: str, severity: str, description: str, confidence: float) -> None:
    rows.append(
        {
            "anomaly_type": anomaly_type,
            "object_type": object_type,
            "severity": severity,
            "description": description,
            "confidence": round(float(confidence), 2),
        }
    )


def detect_anomalies(inv: pd.DataFrame, silver: pd.DataFrame, rules: dict | None = None) -> pd.DataFrame:
    """Detect business anomalies from inventory, occupancy and classroom rules."""
    active_rules = {**DEFAULT_CLASSROOM_RULES, **(rules or {})}
    rows: list[dict] = []

    for obj, exp in EXPECTED.items():
        detected = int(inv.loc[inv.object_type.eq(obj), "detected_count"].sum()) if not inv.empty and "object_type" in inv else 0
        if detected < exp:
            missing = exp - detected
            severity = "critical" if missing >= 5 else "high" if missing >= 3 else "medium"
            _add_anomaly(rows, "missing object", obj, severity, f"{obj}: {detected}/{exp} detecte(s)", 0.9)

    students = _count_object(silver, "eleve", "student", "person")
    teachers = _count_object(silver, "professeur", "teacher", "enseignant")
    expected_students = int(active_rules["expected_students"])
    expected_teacher = int(active_rules["expected_teacher"])

    if students < expected_students:
        missing = expected_students - students
        severity = "critical" if missing >= 4 else "high" if missing >= 2 else "medium"
        _add_anomaly(rows, "attendance gap", "eleve", severity, f"{missing} absent(s) possible(s): {students}/{expected_students} eleves detectes", 0.88)
    elif students > expected_students + 2:
        _add_anomaly(rows, "overcrowding", "eleve", "high", f"Occupation au-dessus du seuil: {students}/{expected_students} eleves", 0.82)

    if expected_teacher and teachers < expected_teacher:
        _add_anomaly(rows, "teacher missing", "teacher", "medium", "Aucun enseignant detecte dans la scene", 0.72)

    if active_rules["tv_required"] and _count_object(silver, "tv") == 0:
        _add_anomaly(rows, "equipment unavailable", "tv", "high", "TV attendue mais non detectee", 0.86)
    if active_rules["projector_required"] and _count_object(silver, "projecteur", "projector") == 0:
        _add_anomaly(rows, "equipment unavailable", "projecteur", "medium", "Projecteur attendu mais non detecte", 0.8)

    if _count_object(silver, "fenetre ouverte", "open window") > 0 and active_rules["window_should_be_closed"]:
        _add_anomaly(rows, "open window", "fenetre", "medium", "Fenetre ouverte detectee alors que la salle devrait etre fermee", 0.76)

    if _count_object(silver, "tv allumee", "tv on") > 0:
        _add_anomaly(rows, "tv left on", "tv", "low", "TV allumee detectee", 0.7)

    object_count = len(silver) if not silver.empty else 0
    density_limit = max(18, int(max(students, expected_students, 1) * float(active_rules["max_objects_per_student"])))
    if object_count > density_limit:
        _add_anomaly(rows, "object density", "global", "medium", f"Densite elevee: {object_count} objets pour un seuil de {density_limit}", 0.74)

    if _count_object(silver, "chaise renversee") > 0:
        _add_anomaly(rows, "layout inconsistency", "chaise", "high", "Chaise renversee ou mobilier deplace detecte", 0.86)
    if _count_object(silver, "objet abandonne", "abandoned object") > 0:
        _add_anomaly(rows, "abandoned object", "autre", "medium", "Objet abandonne detecte dans la salle", 0.78)
    if _count_object(silver, "objet inattendu") > 0:
        _add_anomaly(rows, "unexpected equipment", "autre", "medium", "Equipement ou objet non attendu detecte", 0.78)

    df = pd.DataFrame(rows)
    if not df.empty:
        df.insert(0, "generated_at", datetime.now().isoformat(timespec="seconds"))
        if "analysis_id" in silver.columns and not silver.empty:
            df.insert(1, "analysis_id", str(silver["analysis_id"].iloc[0]))
        if "image_name" in silver.columns and not silver.empty:
            df.insert(2, "image_name", str(silver["image_name"].iloc[0]))
    return df


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"


def _risk_level(score: float, anomalies: pd.DataFrame) -> str:
    if not anomalies.empty and anomalies["severity"].eq("critical").any():
        return "Critical"
    if score < 60:
        return "High"
    if score < 78:
        return "Medium"
    return "Low"


def _recommendations(score: float, anomalies: pd.DataFrame) -> str:
    if anomalies.empty and score >= 85:
        return "Classe conforme. Continuer le suivi historique et la verification ponctuelle."
    recs = []
    if not anomalies.empty:
        top = anomalies["anomaly_type"].head(3).tolist()
        recs.append("Traiter en priorite: " + ", ".join(top))
    if score < 75:
        recs.append("Verifier la qualite photo, l'eclairage et refaire une analyse apres correction.")
    recs.append("Comparer avec l'historique avant decision operationnelle.")
    return " ".join(recs)


def compute_quality_score(inv: pd.DataFrame, anomalies: pd.DataFrame, silver: pd.DataFrame, rules: dict | None = None) -> pd.DataFrame:
    """Compute the professional Classroom Health Score."""
    active_rules = {**DEFAULT_CLASSROOM_RULES, **(rules or {})}
    avg_conf = float(silver["confidence"].mean()) if not silver.empty and "confidence" in silver else 0.0
    compliance = float(inv["compliance_rate"].mean()) if not inv.empty and "compliance_rate" in inv else 0.0
    students = _count_object(silver, "eleve", "student", "person")
    expected_students = max(1, int(active_rules["expected_students"]))
    occupancy_consistency = max(0.0, 1.0 - abs(students - expected_students) / expected_students)
    equipment_objects = ["tv", "pc", "projecteur", "tableau"]
    equipment_available = float(inv[inv["object_type"].isin(equipment_objects)]["compliance_rate"].mean()) if not inv.empty else 0.0
    severity_penalty = min(42, sum(SEVERITY_WEIGHT.get(str(s).lower(), 8) for s in anomalies.get("severity", [])))

    base = (
        compliance * 30
        + avg_conf * 20
        + equipment_available * 18
        + occupancy_consistency * 22
        + 10
    )
    score = round(max(0, min(100, base - severity_penalty)), 2)
    return pd.DataFrame(
        [
            {
                "metric": "Classroom Health Score",
                "analysis_id": str(silver["analysis_id"].iloc[0]) if "analysis_id" in silver.columns and not silver.empty else "",
                "image_name": str(silver["image_name"].iloc[0]) if "image_name" in silver.columns and not silver.empty else "",
                "score": score,
                "grade": _grade(score),
                "risk_level": _risk_level(score, anomalies),
                "recommendations": _recommendations(score, anomalies),
                "avg_detection_confidence": round(avg_conf, 3),
                "inventory_compliance": round(compliance, 3),
                "equipment_availability": round(equipment_available, 3),
                "occupancy_consistency": round(occupancy_consistency, 3),
                "expected_students": expected_students,
                "detected_students": students,
                "anomaly_count": len(anomalies),
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            }
        ]
    )


def run_medallion_pipeline(raw: pd.DataFrame, append: bool = True, rules: dict | None = None) -> dict[str, pd.DataFrame]:
    """Run RAW to GOLD pipeline.

    RAW, BRONZE and SILVER stay historical. GOLD anomaly and score outputs are
    intentionally scoped to the current photo so one old scan cannot pollute the
    anomaly diagnosis of a new image.
    """
    active_rules = {**DEFAULT_CLASSROOM_RULES, **(rules or {})}
    raw_path = DATA_DIR / "raw" / "raw_detections.csv"
    if append:
        raw_full = prepend_csv(raw, raw_path, dedupe_subset=["analysis_id", "image_name", "object_type", "x1", "y1", "x2", "y2"])
    else:
        raw_full = raw.copy()
        write_csv(raw_full, raw_path)

    bronze = raw_to_bronze(raw_full)
    silver = bronze_to_silver(bronze, min_confidence=float(active_rules["min_confidence"]))

    gold_source = raw.copy() if append else raw_full.copy()
    gold = build_photo_gold(gold_source, active_rules)

    write_csv(bronze, DATA_DIR / "bronze" / "bronze_detections.csv")
    write_csv(silver, DATA_DIR / "silver" / "silver_cleaned_inventory.csv")
    for name, df in gold.items():
        write_csv(df, DATA_DIR / "gold" / f"{name}.csv")
    return {"raw": raw_full, "bronze": bronze, "silver": silver, **gold}


def load_current_datasets() -> dict[str, pd.DataFrame]:
    """Load all persisted CSV datasets."""
    return {
        "raw": safe_read_csv(DATA_DIR / "raw" / "raw_detections.csv"),
        "bronze": safe_read_csv(DATA_DIR / "bronze" / "bronze_detections.csv"),
        "silver": safe_read_csv(DATA_DIR / "silver" / "silver_cleaned_inventory.csv"),
        "gold_inventory": safe_read_csv(DATA_DIR / "gold" / "gold_inventory.csv"),
        "gold_anomalies": safe_read_csv(DATA_DIR / "gold" / "gold_anomalies.csv"),
        "gold_quality_score": safe_read_csv(DATA_DIR / "gold" / "gold_quality_score.csv"),
    }
