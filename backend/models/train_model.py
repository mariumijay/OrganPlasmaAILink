import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from geopy.distance import geodesic
import random
from pathlib import Path

# ------------------------------------------------------------
# 1. Load preprocessed data (use Excel files)
# ------------------------------------------------------------
donors = pd.read_excel(r"C:\Users\nasee\Downloads\opalai-simple\dataset\FINAL_MERGED_ALL_ENCODED.xlsx")
recipients = pd.read_excel(r"C:\Users\nasee\Downloads\opalai-simple\dataset\recipient_preprocessed_FINAL(opal ai).xlsx")

print(f"Donors loaded: {len(donors)} rows")
print(f"Recipients loaded: {len(recipients)} rows")

# ------------------------------------------------------------
# 2. Map city names to coordinates (approximate)
# ------------------------------------------------------------
city_coords = {
    "Karachi": (24.8607, 67.0011), "Lahore": (31.5497, 74.3436),
    "Islamabad": (33.6844, 73.0479), "Rawalpindi": (33.5651, 73.0169),
    "Faisalabad": (31.4504, 73.1350), "Multan": (30.1575, 71.5249),
    "Peshawar": (34.0151, 71.5249), "Quetta": (30.1798, 66.9750),
    "Gujranwala": (32.1612, 74.1883), "Sialkot": (32.4945, 74.5229),
    "Bahawalpur": (29.3956, 71.6836), "Hyderabad": (25.3960, 68.3578),
    "Sargodha": (32.0740, 72.6860), "Abbottabad": (34.1497, 73.1996),
    "Mardan": (34.1989, 72.0400), "Mirpur AK": (33.1489, 73.7519),
    "Jhelum": (32.9420, 73.7250), "Sahiwal": (30.6600, 73.1000),
    "Okara": (30.8100, 73.4500), "Dera Ghazi Khan": (30.0500, 70.6300),
}

def get_city_coords(row):
    for col in row.index:
        if col.startswith("City_") and row[col] == 1:
            city = col.replace("City_", "")
            return city_coords.get(city, (31.5204, 74.3587))
    return (31.5204, 74.3587)

donors["city_lat"] = donors.apply(get_city_coords, axis=1).apply(lambda x: x[0])
donors["city_lon"] = donors.apply(get_city_coords, axis=1).apply(lambda x: x[1])

recipients["city_lat"] = recipients.apply(get_city_coords, axis=1).apply(lambda x: x[0])
recipients["city_lon"] = recipients.apply(get_city_coords, axis=1).apply(lambda x: x[1])

# ------------------------------------------------------------
# 3. Blood type compatibility score
# ------------------------------------------------------------
blood_types = ["A+","A-","B+","B-","AB+","AB-","O+","O-"]
def compat_score(donor_row, recipient_row):
    donor_bt = None
    recip_bt = None
    for bt in blood_types:
        if donor_row.get(f"blood_{bt}", 0) == 1:
            donor_bt = bt
        if recipient_row.get(f"blood_{bt}", 0) == 1:
            recip_bt = bt
    if donor_bt is None or recip_bt is None:
        return 0
    compat_matrix = {
        "O-": ["O-"], "O+": ["O+", "O-"],
        "A-": ["A-", "O-"], "A+": ["A+", "A-", "O+", "O-"],
        "B-": ["B-", "O-"], "B+": ["B+", "B-", "O+", "O-"],
        "AB-": ["AB-", "A-", "B-", "O-"], "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"]
    }
    if recip_bt in compat_matrix.get(donor_bt, []):
        if donor_bt == recip_bt:
            return 100.0
        elif donor_bt == "O-":
            return 95.0
        else:
            return 85.0
    return 0.0

# ------------------------------------------------------------
# 4. Generate synthetic donor-recipient pairs
# ------------------------------------------------------------
pairs = []
for _ in range(10000):
    donor = donors.sample(1).iloc[0]
    recipient = recipients.sample(1).iloc[0]
    
    comp = compat_score(donor, recipient)
    if comp == 0:
        continue
    
    d_lat, d_lon = donor["city_lat"], donor["city_lon"]
    r_lat, r_lon = recipient["city_lat"], recipient["city_lon"]
    dist_km = geodesic((d_lat, d_lon), (r_lat, r_lon)).km
    if dist_km > 200:
        continue
    distance_score = max(0, 100 - (dist_km / 20) * 100)
    
    urgency_level = random.choice(["low", "medium", "critical"])
    urgency_score = {"critical": 100, "medium": 75, "low": 50}[urgency_level]
    
    target = (comp * 0.5) + (distance_score * 0.3) + (urgency_score * 0.2)
    
    features = {}
    features["donor_age"] = donor["age"]
    for cond in ["Condition_Diabetes", "Condition_Hypertension", "Condition_Heart_Disease", "Condition_Asthma"]:
        features[f"donor_{cond}"] = donor.get(cond, 0)
    features["recipient_age"] = recipient["age"]
    for cond in ["Condition_Diabetes", "Condition_Hypertension", "Condition_Heart_Disease", "Condition_Asthma", "Condition_Liver_Disease", "Condition_Kidney_Disease"]:
        features[f"recipient_{cond}"] = recipient.get(cond, 0)
    for bt in blood_types:
        features[f"donor_blood_{bt}"] = donor.get(f"blood_{bt}", 0)
    for organ in ["Organ_Heart", "Organ_Kidney", "Organ_Liver", "Organ_Lung", "Organ_Pancreas", "Organ_Cornea"]:
        features[f"recipient_{organ}"] = recipient.get(organ, 0)
    for lev in ["low", "medium", "critical"]:
        features[f"urgency_{lev}"] = 1 if urgency_level == lev else 0
    features["distance_km"] = dist_km
    features["target"] = target
    pairs.append(features)

df = pd.DataFrame(pairs)
print(f"Generated {len(df)} valid pairs")

# ------------------------------------------------------------
# 5. Train XGBoost model
# ------------------------------------------------------------
X = df.drop("target", axis=1)
y = df["target"]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
model.fit(X_train, y_train)

from sklearn.metrics import mean_absolute_error
y_pred = model.predict(X_test)
print(f"MAE: {mean_absolute_error(y_test, y_pred):.2f}")

# ------------------------------------------------------------
# 6. Save model and feature names
# ------------------------------------------------------------
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)
joblib.dump({"model": model, "features": list(X.columns)}, model_dir / "match_ranker_v2.joblib")
print("Model saved to models/match_ranker_v2.joblib")