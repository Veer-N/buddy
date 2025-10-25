# emotion.py
# simple sentiment -> emotion mapper using transformers pipeline
from transformers import pipeline
sentiment = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")


def detect_emotion(text: str) -> str:
    res = sentiment(text[:512])[0]  # truncate to safe length
    label = res["label"].lower()
    score = res["score"]
    # map to small set of emotions
    if label == "positive" and score > 0.85:
        return "joy"
    if label == "positive":
        return "calm"
    if label == "negative" and score > 0.85:
        return "anger"
    if label == "negative":
        return "sadness"
    return "neutral"

EMOTION_LABELS = ["joy", "calm", "anger", "sadness", "fear", "neutral", "surprise"]

def detect_emotion_scores(text: str):
    """
    Returns a dict of normalized scores for all EMOTION_LABELS.
    Uses your existing `sentiment` pipeline which returns single label+score.
    """
    # ensure we have a pipeline variable named `sentiment` in this file
    res = sentiment(text[:512])[0]  # existing pipeline call
    # initialize low smoothing value for all labels
    base = {label: 0.01 for label in EMOTION_LABELS}
    label = res.get("label")
    score = float(res.get("score", 0.0))
    if label in base:
        base[label] = score
    # normalize to sum=1
    s = sum(base.values()) or 1.0
    return {k: v / s for k, v in base.items()}