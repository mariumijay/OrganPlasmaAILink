import joblib
import os
import xgboost as xgb
from pathlib import Path

def repair_model():
    base_dir = Path(__file__).resolve().parent
    model_path = base_dir / "backend" / "models" / "match_ranker_v2.joblib"
    
    if not model_path.exists():
        # Check alternative path if running from backend dir
        model_path = base_dir / "models" / "match_ranker_v2.joblib"
        if not model_path.exists():
            print(f"Model not found at {model_path}")
            return

    print(f"Loading model from {model_path}...")
    try:
        model_data = joblib.load(model_path)
        
        # If it's a dictionary containing the model
        if isinstance(model_data, dict) and "model" in model_data:
            model = model_data["model"]
            print("Detected dictionary-wrapped model. Re-saving...")
        else:
            model = model_data
            print("Detected direct model object. Re-saving...")

        # Re-save using joblib in current environment to silence pickle warnings
        joblib.dump(model_data, model_path)
        print(f"Successfully re-saved model to {model_path}. The warning should now be gone.")
        
    except Exception as e:
        print(f"Error during repair: {e}")

if __name__ == "__main__":
    repair_model()
