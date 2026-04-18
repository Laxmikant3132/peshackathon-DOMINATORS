import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Targets
EMAIL_MODEL_PATH = os.path.join(MODELS_DIR, "email_classifier.joblib")
NETWORK_MODEL_PATH = os.path.join(MODELS_DIR, "network_threat_model.joblib")

def ensure_dirs():
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)

def train_email_model():
    print("\n[STEP 1] Training Email Phishing Model...")
    csv_path = os.path.join(DATASET_DIR, "phishing_email.csv")
    
    if not os.path.exists(csv_path):
        print(f"!! Phishing dataset not found at {csv_path}")
        return

    # Load data
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=['text_combined', 'label'])
    
    # Normalize labels
    # 0 -> safe, 1 -> dangerous
    df["label"] = df["label"].replace({0: "safe", 1: "dangerous"})
    
    X = df["text_combined"]
    y = df["label"]

    # Simple but effective Pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, stop_words='english')),
        ('clf', LogisticRegression(max_iter=1000, class_weight='balanced'))
    ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    pipeline.fit(X_train, y_train)
    acc = accuracy_score(y_test, pipeline.predict(X_test))
    
    print(f"-> Email Model Trained. Accuracy: {acc:.4f}")
    joblib.dump(pipeline, EMAIL_MODEL_PATH)
    print(f"-> Saved: {EMAIL_MODEL_PATH}")

def train_network_model():
    print("\n[STEP 2] Training Network Intrusion Model...")
    csv_path = os.path.join(DATASET_DIR, "Dataset_resumido.csv")
    
    if not os.path.exists(csv_path):
        print(f"!! Network dataset not found at {csv_path}")
        return

    # Load data
    # High chance of mixed types in ports (sport/dsport), we handle by errors='coerce'
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return

    print(f"-> Loaded {len(df)} network records.")

    # Feature Engineering for real-time consistency
    # We select features we can actually get from psutil live: sports, dports, proto
    # and some aggregated ones like bytes/duration if available in dataset.
    
    # Clean port data
    df['sport'] = pd.to_numeric(df['sport'], errors='coerce').fillna(0)
    df['dsport'] = pd.to_numeric(df['dsport'], errors='coerce').fillna(0)
    
    # Encode proto
    le_proto = LabelEncoder()
    df['proto_enc'] = le_proto.fit_transform(df['proto'].astype(str))
    
    # Target: Label (0 = Normal, 1 = Attack)
    # The dataset might have multi-class (Attack_cat), but we want binary for core logic
    if 'Label' in df.columns:
        y = df['Label']
    elif 'label' in df.columns:
        y = df['label']
    else:
        print("!! Target label not found in CSV.")
        return

    # Select Features
    # Note: We prioritize features that match psutil live data
    features = ['sport', 'dsport', 'proto_enc']
    # If dataset has numeric bytes/dur, we use them too
    for col in ['sbytes', 'dbytes', 'dur']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            features.append(col)

    X = df[features]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # RandomForest is robust for multi-modal features
    model = RandomForestClassifier(n_estimators=50, max_depth=10, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)
    
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"-> Network Model Trained. Accuracy: {acc:.4f}")
    
    # Save model and the encoder for Proto
    joblib.dump({
        'model': model,
        'features': features,
        'le_proto': le_proto
    }, NETWORK_MODEL_PATH)
    print(f"-> Saved: {NETWORK_MODEL_PATH}")

if __name__ == "__main__":
    ensure_dirs()
    # To save time and avoid OOM, checking if models already exist or train selectively
    train_email_model()
    train_network_model()
    print("\n[DONE] System intelligence updated.")
