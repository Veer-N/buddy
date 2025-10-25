from transformers import pipeline

# Initialize emotion detection model
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base", return_all_scores=False)

# Sample inputs
texts = [
    "I'm so happy today!",
    "I'm really sad right now.",
    "That made me so angry!",
    "I'm feeling a bit anxious.",
    "This is amazing news!"
]

for text in texts:
    result = emotion_classifier(text)[0]
    print(f"Text: {text}")
    print(f"Emotion: {result['label']} | Score: {result['score']:.2f}\n")
