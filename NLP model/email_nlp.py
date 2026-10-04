import os
import re
import joblib


# MODEL PATHS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "trained_model",
    "email_threat_model.pkl"
)

VECTORIZER_PATH = os.path.join(
    BASE_DIR,
    "trained_model",
    "tfidf_vectorizer.pkl"
)


# LOAD MODEL

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)


# CLEAN TEXT

def clean_text(text):
    text = str(text)
    text = text.lower()

    # REPLACE URLS
    text = re.sub(r"http\S+|www\S+", " URL ", text)

    # REPLACE EMAILS
    text = re.sub(r"\S+@\S+", " EMAIL ", text)

    # REPLACE NUMBERS
    text = re.sub(r"\d+", " NUMBER ", text)

    # REMOVE EXTRA SPACES
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ANALYZE EMAIL

def analyze_email(sender, subject, body):

    text = (
        "sender: " + clean_text(sender) +
        " subject: " + clean_text(subject) +
        " body: " + clean_text(body)
    )

    # CONVERT TEXT TO TF-IDF
    text_vector = vectorizer.transform([text])

    # GET PREDICTION
    prediction = model.predict(text_vector)[0]

    # GET CONFIDENCE
    probabilities = model.predict_proba(text_vector)[0]
    confidence = max(probabilities) * 100

    # SET THREAT LEVEL

    if prediction == 1:
        threat = "THREAT"
        risk = "HIGH"
    else:
        threat = "LEGITIMATE"
        risk = "LOW"

    return {
        "threat": threat,
        "confidence": round(confidence, 2),
        "risk": risk
    }