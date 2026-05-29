CREATE TABLE IF NOT EXISTS raw (
  image_name TEXT,
  object_type TEXT,
  raw_class TEXT,
  confidence REAL,
  x1 REAL, y1 REAL, x2 REAL, y2 REAL,
  area REAL
);
CREATE TABLE IF NOT EXISTS gold_inventory (
  object_type TEXT PRIMARY KEY,
  detected_count INTEGER,
  avg_confidence REAL,
  expected_count INTEGER,
  delta INTEGER,
  compliance_rate REAL
);
CREATE TABLE IF NOT EXISTS gold_anomalies (
  anomaly_type TEXT,
  object_type TEXT,
  severity TEXT,
  description TEXT,
  confidence REAL
);
CREATE TABLE IF NOT EXISTS data_catalog (
  dataset TEXT,
  colonne TEXT,
  type TEXT,
  description TEXT,
  source TEXT,
  regles_qualite TEXT
);
