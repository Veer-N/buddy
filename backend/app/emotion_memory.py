# backend/app/emotion_memory.py
from collections import deque
import time, math

EMOTION_LABELS = ["joy", "calm", "anger", "sadness", "fear", "neutral", "surprise"]

class EmotionMemory:
    def __init__(self, window_seconds: int = 300, max_items: int = 50):
        self.window_seconds = window_seconds
        self.max_items = max_items
        self.recent = deque()  # (ts, speaker, text, emotion_scores)

    def add(self, ts: float, speaker: str, text: str, emotion_scores: dict):
        self.recent.append((ts, speaker, text, emotion_scores))
        self._purge()

    def _purge(self):
        now = time.time()
        # remove old items
        while self.recent and now - self.recent[0][0] > self.window_seconds:
            self.recent.popleft()
        # limit queue size
        while len(self.recent) > self.max_items:
            self.recent.popleft()

    def blended_emotion(self, decay: float = 0.9):
        now = time.time()
        agg = {l: 0.0 for l in EMOTION_LABELS}
        total_w = 0.0

        for ts, speaker, text, scores in reversed(list(self.recent)):
            age = now - ts
            weight = math.exp(-age / 60)  # decays per minute
            if speaker == "user":
                weight *= 1.2
            for l in EMOTION_LABELS:
                agg[l] += scores.get(l, 0.0) * weight
            total_w += weight

        if total_w == 0:
            return "neutral", {l: 0.0 for l in EMOTION_LABELS}

        normalized = {k: v / total_w for k, v in agg.items()}
        top = max(normalized, key=normalized.get)
        return top, normalized
