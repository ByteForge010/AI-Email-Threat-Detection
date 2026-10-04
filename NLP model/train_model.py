import os
import re
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ==========================================
# 1. SETTINGS
# ==========================================

DATASET = os.path.join("NLP model", "CEAS_08.csv")
MODEL_FOLDER = os.path.join("NLP model", "trained_model")

os.makedirs(MODEL_FOLDER, exist_ok=True)

#CLEAN TEXT FUNCTION
def clean_text(text):
    text = str(text)

    # Convert to lowercase
    text = text.lower()

    # Replace URLs
    text = re.sub(r"http\S+|www\S+", " URL ", text)

    # Replace email addresses
    text = re.sub(r"\S+@\S+", " EMAIL ", text)

    # Replace numbers
    text = re.sub(r"\d+", " NUMBER ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

#LOAD DATASET

print("Loading dataset...")

df = pd.read_csv(DATASET)

print("\nDataset loaded successfully.")
print("Rows:", len(df))
print("Columns:", list(df.columns))

#CHECK REQUIRED COLUMNS

required_columns = ["subject", "body", "label"]

for column in required_columns:
    if column not in df.columns:
        raise ValueError(
            f"Column '{column}' was not found in the dataset."
        )

#HANDLE MISSING VALUES

df["subject"] = df["subject"].fillna("")
df["body"] = df["body"].fillna("")

if "sender" in df.columns:
    df["sender"] = df["sender"].fillna("")
else:
    df["sender"] = ""

#COMBINE EMAIL INFORMATION

print("\nPreparing email text...")

df["text"] = (
    "sender: " + df["sender"].apply(clean_text) +
    " subject: " + df["subject"].apply(clean_text) +
    " body: " + df["body"].apply(clean_text)
)

#LABELS

# CEAS labels:
# 0 = legitimate
# 1 = spam/threat

X = df["text"]
y = df["label"].astype(int)


print("\nLabel distribution:")
print(y.value_counts())


# TRAIN / TEST SPLIT

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining emails:", len(X_train))
print("Testing emails:", len(X_test))

# TF-IDF

print("\nCreating TF-IDF features...")

vectorizer = TfidfVectorizer(
    max_features=100000,
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.98,
    sublinear_tf=True
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

print("TF-IDF features:", X_train_tfidf.shape[1])

#TRAIN LOGISTIC REGRESSION

print("\nTraining Logistic Regression...")

model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
    solver="liblinear"
)

model.fit(X_train_tfidf, y_train)

print("Training completed.")



# TEST MODEL

print("\nTesting model...")

y_pred = model.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, y_pred)

print("\n================================")
print("MODEL ACCURACY")
print("================================")

print(f"{accuracy * 100:.2f}%")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["LEGITIMATE", "THREAT"]
    )
)

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

#SAVE MODEL

print("\nSaving model...")

model_path = os.path.join(
    MODEL_FOLDER,
    "email_threat_model.pkl"
)

vectorizer_path = os.path.join(
    MODEL_FOLDER,
    "tfidf_vectorizer.pkl"
)

joblib.dump(model, model_path)
joblib.dump(vectorizer, vectorizer_path)

#FINISHED

print("\n================================")
print("TRAINING COMPLETE")
print("================================")

print("\nSaved files:")

print(model_path)
print(vectorizer_path)