from __future__ import annotations

import pandas as pd

from app.core.settings import DATA_DIR

DESCRIPTIONS = {
    "image_name": "Nom du fichier image analyse",
    "object_type": "Classe metier detectee",
    "raw_class": "Classe native du modele IA",
    "confidence": "Score de confiance de detection",
    "x1": "Coordonnee gauche bbox",
    "y1": "Coordonnee haute bbox",
    "x2": "Coordonnee droite bbox",
    "y2": "Coordonnee basse bbox",
    "area": "Surface de la boite",
    "detected_count": "Nombre detecte",
    "expected_count": "Nombre attendu",
    "delta": "Ecart detecte-attendu",
    "compliance_rate": "Taux de conformite inventaire",
    "score": "Classroom Health Score de 0 a 100",
    "grade": "Grade synthetique du score",
    "risk_level": "Niveau de risque operationnel",
    "recommendations": "Recommandations generees par le moteur de score",
    "expected_students": "Nombre d'eleves attendus selon la contrainte du jour",
    "detected_students": "Nombre d'eleves detectes par la vision",
}

QUALITY = {
    "confidence": "0 <= confidence <= 1 ; seuil recommande >= 0.25",
    "object_type": "Non nul, normalise en minuscules",
    "score": "Entre 0 et 100",
    "detected_count": "Entier positif",
    "expected_count": "Entier positif ou nul",
    "risk_level": "Valeurs controlees: Low, Medium, High, Critical",
}


def build_data_catalog(datasets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Build and persist the data catalog from available datasets."""
    rows = []
    for name, df in datasets.items():
        for col in df.columns:
            rows.append(
                {
                    "dataset": name,
                    "colonne": col,
                    "type": str(df[col].dtype),
                    "description": DESCRIPTIONS.get(col, "Champ analytique genere par ClassVision AI"),
                    "source": "Pipeline medaillon local / Streamlit / IA Vision",
                    "regles qualite": QUALITY.get(col, "Completude, unicite et coherence metier controlees"),
                }
            )
    cat = pd.DataFrame(rows)
    cat.to_csv(DATA_DIR / "catalog" / "data_catalog.csv", index=False)
    return cat
