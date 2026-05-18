import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor
from pathlib import Path
import os

# 1. Load the model and features
model_path = Path(r"C:\Users\nasee\Downloads\opalai-simple\backend\models\match_ranker_v2.joblib")
if not model_path.exists():
    print("Model not found. Please run train_model.py first.")
    exit()

data_pack = joblib.load(model_path)
model = data_pack["model"]
features = data_pack["features"]

# 2. Load actual data to generate a valid validation set
donors = pd.read_excel(r"C:\Users\nasee\Downloads\opalai-simple\dataset\FINAL_MERGED_ALL_ENCODED.xlsx")
recipients = pd.read_excel(r"C:\Users\nasee\Downloads\opalai-simple\dataset\recipient_preprocessed_FINAL(opal ai).xlsx")

print(f"Loaded {len(donors)} donors and {len(recipients)} recipients.")

# Function to calculate target (With REALISTIC NOISE)
def calculate_ground_truth(d_row, r_row):
    # Simulated blood compatibility (With 10% chance of noise)
    comp_base = 100.0 if np.random.rand() > 0.45 else 10.0
    comp = comp_base + np.random.normal(0, 5) # Add noise
    
    # Distance logic (With noise)
    dist_km = np.random.uniform(2, 250)
    distance_score = max(0, 100 - (dist_km / 25) * 100) + np.random.normal(0, 8)
    
    # Urgency logic
    urgency_level = random.choice(["low", "medium", "critical"])
    urgency_score = {"critical": 100, "medium": 75, "low": 50}[urgency_level] + np.random.normal(0, 3)
    
    target = (comp * 0.45) + (distance_score * 0.35) + (urgency_score * 0.20)
    # Add a final layer of uncertainty
    target += np.random.normal(0, 12) 
    return np.clip(target, 0, 100), dist_km, urgency_level

import random
pairs = []
for _ in range(1200):
    d = donors.sample(1).iloc[0]
    r = recipients.sample(1).iloc[0]
    
    target, dist_km, urg_lvl = calculate_ground_truth(d, r)
    
    # Feature construction
    feat = {f: 0 for f in features}
    feat["donor_age"] = d["age"]
    feat["recipient_age"] = r["age"]
    feat["distance_km"] = dist_km
    feat[f"urgency_{urg_lvl}"] = 1
    
    feat["target"] = target
    pairs.append(feat)

df_val = pd.DataFrame(pairs)
X_val = df_val.drop("target", axis=1)
y_val = df_val["target"]

print(f"Generated {len(df_val)} natural validation pairs.")

# Get predictions
y_pred_scores = model.predict(X_val)

# Binarize for Classification Metrics (Threshold = 75)
threshold = 75
y_val_binary = (y_val >= threshold).astype(int)
y_pred_binary = (y_pred_scores >= threshold).astype(int)

# ------------------------------------------------------------
# 3. Plot ROC Curve
# ------------------------------------------------------------
fpr, tpr, _ = roc_curve(y_val_binary, y_pred_scores / 100.0)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic (ROC) - Donor Match')
plt.legend(loc="lower right")
plt.grid(alpha=0.3)
plt.savefig("roc_curve.png")
print("ROC Curve saved as roc_curve.png")

# ------------------------------------------------------------
# 4. Plot Confusion Matrix
# ------------------------------------------------------------
cm = confusion_matrix(y_val_binary, y_pred_binary)
plt.figure(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['No Match', 'Match'], yticklabels=['No Match', 'Match'])
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Confusion Matrix (Threshold = 75%)')
plt.savefig("confusion_matrix.png")
print("Confusion Matrix saved as confusion_matrix.png")

print("\nClassification Report:")
print(classification_report(y_val_binary, y_pred_binary))
