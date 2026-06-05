import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

DATASETS = {
    "heart": ("heart.csv", "target"),
    "diabetes": ("diabetes.csv", "diabetes"),
    "liver": ("liver.csv", "Dataset")
}

SYMPTOMS = [
    'fever','fatigue','cough','shortnessOfBreath',
    'dizziness','nausea','excessiveThirst','blurredVision'
]

HISTORY = [
    'asthma','hypertension','diabetesInFamily',
    'heartDisease','liverCondition','smokingHistory'
]

def train_and_save(name, file_name, target_col):

    print(f"Training {name} model...")

    df = pd.read_csv(f"datasets/{file_name}")

    # Drop rows with missing values
    df = df.dropna()
    
    # convert categorical → numeric (convert ALL string/object columns to numeric)
    object_cols = [col for col in df.columns if df[col].dtype in ('object', 'str', 'string')]
    
    for col in object_cols:
        # Use factorize to convert strings to integers
        codes, uniques = pd.factorize(df[col])
        df[col] = codes

    # add missing columns
    for col in SYMPTOMS + HISTORY:
        if col not in df.columns:
            df[col] = 0

    X = df.drop(columns=[target_col])
    y = df[target_col]

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        random_state=42
    )

    model.fit(X, y)

    os.makedirs("models", exist_ok=True)

    joblib.dump({
        "model": model,
        "features": list(X.columns)
    }, f"models/{name}_model.joblib")

    print(f"{name} model saved")


if __name__ == "__main__":

    os.makedirs("models", exist_ok=True)

    train_and_save("heart", "heart.csv", "target")
    train_and_save("diabetes", "diabetes.csv", "diabetes")
    train_and_save("liver", "liver.csv", "Dataset")