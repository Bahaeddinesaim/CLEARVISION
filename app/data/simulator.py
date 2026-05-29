from __future__ import annotations
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker
from app.core.settings import DATA_DIR

fake = Faker("fr_FR")
OBJECTS = ["table","chaise","bureau","tableau","tv","pc","laptop","projecteur","porte","fenetre","poubelle","armoire","eleve","enseignant"]
ANOMALIES = ["chaise renversée","table déplacée","objet manquant","zone encombrée","désordre","équipement absent","occupation anormale","objet inattendu"]


def generate_demo_data(n_rooms: int = 100, days: int = 60) -> dict[str, pd.DataFrame]:
    random.seed(42); np.random.seed(42)
    rooms, inventory, anomalies, history = [], [], [], []
    base_date = datetime.now() - timedelta(days=days)
    for i in range(1, n_rooms + 1):
        room_id = f"CLS-{i:03d}"
        capacity = random.choice([20,24,28,30,32,36])
        rooms.append({"room_id": room_id, "building": random.choice(["A","B","C","D"]), "floor": random.randint(0,4), "capacity": capacity, "surface_m2": random.randint(35,90), "owner_department": random.choice(["Informatique","Sciences","Langues","Management"]), "criticality": random.choice(["low","medium","high"])})
        expected = {"table": capacity//2, "chaise": capacity, "tableau":1,"porte":1,"fenetre":random.randint(1,4),"poubelle":1,"bureau":1,"pc":random.randint(0,18),"tv":random.choice([0,1]),"projecteur":random.choice([0,1])}
        for obj, exp in expected.items():
            detected = max(0, int(np.random.normal(exp, max(1, exp*.15))))
            inventory.append({"room_id":room_id,"object_type":obj,"expected_count":exp,"detected_count":detected,"delta":detected-exp,"compliance_rate":round(min(detected/exp,1),2) if exp else 1.0})
        for d in range(days):
            date = base_date + timedelta(days=d)
            anomaly_count = np.random.poisson(1.2 if random.random()<.25 else .4)
            score = max(25, min(100, 94 - anomaly_count*9 - random.randint(0,8)))
            history.append({"room_id":room_id,"date":date.date().isoformat(),"detections":random.randint(15,55),"anomalies":int(anomaly_count),"classroom_health_score":int(score),"data_quality_score":round(random.uniform(.86,.99),3)})
            for _ in range(int(anomaly_count)):
                anomalies.append({"room_id":room_id,"date":date.date().isoformat(),"anomaly_type":random.choice(ANOMALIES),"severity":random.choice(["low","medium","high"]),"status":random.choice(["open","closed","in_progress"]),"confidence":round(random.uniform(.55,.96),2),"business_impact":random.choice(["sécurité","maintenance","qualité pédagogique","inventaire"])})
    dfs = {"rooms":pd.DataFrame(rooms),"demo_inventory":pd.DataFrame(inventory),"demo_anomalies":pd.DataFrame(anomalies),"demo_history":pd.DataFrame(history)}
    for name, df in dfs.items(): df.to_csv(DATA_DIR/"demo"/f"{name}.csv", index=False)
    return dfs
