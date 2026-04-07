# ============================================================
# TruthSeeker — Misinformation Detection Model Training
# Run this entire script in a single Google Colab cell.
# ============================================================

# --- Step 0: Install dependencies (Colab already has most of these) ---
# !pip install pandas scikit-learn joblib

# --- Step 1: Upload the dataset ---
# In Google Colab, run this cell first to upload your CSV:
#   from google.colab import files
#   uploaded = files.upload()   # pick "Truth_Seeker_Model_Dataset.csv"

# --- Step 2: Imports ---
import pandas as pd
import numpy as np
import re
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# ============================================================
# CONFIG
# ============================================================
DATASET_PATH = "Truth_Seeker_Model_Dataset.csv"  # adjust if you renamed it
TEXT_COLS = ["statement", "tweet"]                # columns to combine
LABEL_COL = "BinaryNumTarget"                    # 1 = True, 0 = Fake
TEST_SIZE = 0.20
RANDOM_STATE = 42

# ============================================================
# 1. LOAD & INSPECT
# ============================================================
print("━" * 60)
print("📂  Loading dataset …")
df = pd.read_csv(DATASET_PATH)
print(f"   Rows : {len(df):,}")
print(f"   Cols : {list(df.columns)}")

# ============================================================
# 2. CLEAN
# ============================================================
print("\n🧹  Cleaning …")

# Drop rows where text or label is missing
df = df.dropna(subset=[LABEL_COL])
for col in TEXT_COLS:
    df[col] = df[col].fillna("")

# Convert label to int (the CSV stores 1.0 / 0.0)
df[LABEL_COL] = df[LABEL_COL].astype(int)

# Combine text columns into a single feature
def clean_text(text: str) -> str:
    """Lowercase, strip URLs, mentions, hashtags, and excess whitespace."""
    text = text.lower()
    text = re.sub(r"http\S+|www\.\S+", "", text)          # URLs
    text = re.sub(r"@\w+", "", text)                       # @mentions
    text = re.sub(r"#\w+", "", text)                       # #hashtags
    text = re.sub(r"[^a-z0-9\s.,!?']", " ", text)         # non-alpha
    text = re.sub(r"\s+", " ", text).strip()               # whitespace
    return text

df["combined_text"] = df[TEXT_COLS].apply(
    lambda row: clean_text(" ".join(row.values)), axis=1
)

# Drop empty rows after cleaning
df = df[df["combined_text"].str.len() > 0]

print(f"   Rows after cleaning : {len(df):,}")
print(f"   Label distribution  :\n{df[LABEL_COL].value_counts().to_string()}")

# ============================================================
# 3. SPLIT
# ============================================================
X = df["combined_text"]
y = df[LABEL_COL]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
print(f"\n📊  Train : {len(X_train):,}  |  Test : {len(X_test):,}")

# ============================================================
# 4. VECTORIZE  (TF-IDF)
# ============================================================
print("\n🔠  Fitting TF-IDF Vectorizer …")
tfidf = TfidfVectorizer(
    max_df=0.7,            # ignore terms appearing in >70 % of docs
    max_features=50_000,   # vocabulary cap
    ngram_range=(1, 2),    # unigrams + bigrams
    stop_words="english",
    sublinear_tf=True,     # apply log normalization
)
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf  = tfidf.transform(X_test)
print(f"   Vocabulary size : {len(tfidf.vocabulary_):,}")

# ============================================================
# 5. TRAIN  (Passive-Aggressive Classifier)
# ============================================================
print("\n🧠  Training Passive-Aggressive Classifier …")
pac = PassiveAggressiveClassifier(
    max_iter=100,
    C=1.0,                 # regularization
    random_state=RANDOM_STATE,
    class_weight="balanced",
    n_jobs=-1,
)
pac.fit(X_train_tfidf, y_train)

# ============================================================
# 6. EVALUATE
# ============================================================
y_pred = pac.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, y_pred)
print(f"\n✅  Accuracy : {accuracy:.4f}  ({accuracy*100:.2f} %)")
print("\n📋  Classification Report:\n")
print(classification_report(y_test, y_pred, target_names=["Fake (0)", "Real (1)"]))
print("🔢  Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# ============================================================
# 7. SAVE MODEL & VECTORIZER
# ============================================================
MODEL_FILE      = "truthseeker_model.joblib"
VECTORIZER_FILE = "truthseeker_vectorizer.joblib"

joblib.dump(pac,  MODEL_FILE)
joblib.dump(tfidf, VECTORIZER_FILE)
print(f"\n💾  Saved  →  {MODEL_FILE}  ({__import__('os').path.getsize(MODEL_FILE)/1024:.1f} KB)")
print(f"💾  Saved  →  {VECTORIZER_FILE}  ({__import__('os').path.getsize(VECTORIZER_FILE)/1024:.1f} KB)")

# ============================================================
# 8. DOWNLOAD (uncomment in Colab)
# ============================================================
# from google.colab import files
# files.download(MODEL_FILE)
# files.download(VECTORIZER_FILE)

print("\n🎉  Done! Download the two .joblib files to your local machine.")
