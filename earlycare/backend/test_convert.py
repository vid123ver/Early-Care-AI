import pandas as pd
import numpy as np

SYMPTOMS = ['fever','fatigue','cough','shortnessOfBreath','dizziness','nausea','excessiveThirst','blurredVision']
HISTORY = ['asthma','hypertension','diabetesInFamily','heartDisease','liverCondition','smokingHistory']

df = pd.read_csv("datasets/diabetes.csv")
df = df.dropna()

print("Original dtypes:")
print(df.dtypes)

# convert categorical → numeric
for col in df.columns:
    if df[col].dtype == 'object':
        print(f"Converting {col}...")
        df[col], _ = pd.factorize(df[col])

print("\nAfter factorize:")
print(df.dtypes)

# add missing columns
for col in SYMPTOMS + HISTORY:
    if col not in df.columns:
        df[col] = 0

print("\nFinal dtypes:")
print(df.dtypes)

X = df.drop(columns=['diabetes'])
y = df['diabetes']

print("\nX shape:", X.shape)
print("y shape:", y.shape)

# Try numpy conversion
print("\nConverting to numpy...")
X_np = np.asarray(X)
print("Success! Shape:", X_np.shape)
