import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline, FeatureUnion
import joblib
import os

def train_model():
    # 1. Load dataset
    data_path = os.path.join(os.path.dirname(__file__), 'dataset', 'phishing_email.csv')
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        return
        
    df = pd.read_csv(data_path)
    
    # 1.5 Data Cleaning
    print(f"Original dataset size: {len(df)}")
    df = df.dropna(subset=['text_combined', 'label'])
    df = df.drop_duplicates(subset=['text_combined'])
    
    # Remove extremely short texts which might be noise
    df = df[df['text_combined'].str.len() > 15]
    print(f"Cleaned dataset size: {len(df)}")
    
    # Use text_combined and label columns
    X = df["text_combined"]
    y = df["label"]
    
    # 2. Normalize labels
    # 0 -> safe, 1 -> dangerous
    df["label"] = df["label"].replace({
        0: "safe",
        1: "dangerous"
    })
    y = df["label"]
    
    # 3. Split dataset
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # 4. Create and train pipeline with more powerful features
    # Combining Word (n-grams) and Char (n-grams) for robustness
    word_vectorizer = TfidfVectorizer(
        analyzer='word',
        stop_words='english',
        ngram_range=(1, 2),
        max_features=10000,
        min_df=5,
        max_df=0.8
    )
    
    char_vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(3, 5),
        max_features=10000,
        min_df=5,
        max_df=0.8
    )
    
    features = FeatureUnion([
        ('word', word_vectorizer),
        ('char', char_vectorizer)
    ])
    
    # Using Logistic Regression with balanced weights for better accuracy
    pipeline = Pipeline([
        ('features', features),
        ('clf', LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            C=1.0,
            random_state=42
        ))
    ])
    
    print("Training the model... this may take a moment.")
    pipeline.fit(X_train, y_train)
    
    # 5. Evaluation
    y_pred = pipeline.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred)}")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # 6. Save model
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)
        
    model_path = os.path.join(model_dir, 'email_classifier.joblib')
    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
