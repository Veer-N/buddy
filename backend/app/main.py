# backend/app/main.py
import json
import time
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# memory / LLM modules
from .memory import Memory
from .llm_handler import generate_reply, summarize_memories

# emotion modules
from .emotion import detect_emotion_scores
from .emotion_memory import EmotionMemory
from .tts_handler import VoiceBuddy

# ----------------- FastAPI app -----------------
app = FastAPI()

# Allow CORS for Expo app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Initialize memory -----------------
mem = Memory()
emotion_mem = EmotionMemory(window_seconds=3600, max_items=200)
voice_buddy = VoiceBuddy()

# ----------------- Emotion → TTS mapping -----------------
# Keep same voice, different speed/pitch for emotions
EMOTION_MAP = {
    "joy": {"speed": 1.12, "pitch": 1.05, "voice": "alloy"},
    "calm": {"speed": 1.0, "pitch": 1.0, "voice": "alloy"},
    "anger": {"speed": 1.2, "pitch": 0.95, "voice": "alloy"},
    "sadness": {"speed": 0.98, "pitch": 0.95, "voice": "alloy"},
    "fear": {"speed": 1.1, "pitch": 1.1, "voice": "alloy"},
    "surprise": {"speed": 1.15, "pitch": 1.2, "voice": "alloy"},
    "neutral": {"speed": 1.0, "pitch": 1.0, "voice": "alloy"},
}

# ----------------- Emotion → Expression mapping -----------------
EXPRESSION_MAP = {
    "joy": "smile",
    "calm": "neutral",
    "anger": "angry",
    "sadness": "sad",
    "fear": "fearful",
    "surprise": "surprised",
    "neutral": "neutral",
}

# ----------------- WebSocket handler -----------------
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    while True:
        data = await ws.receive_text()

        # Parse input (text or future voice)
        try:
            payload = json.loads(data)
            text = payload.get("text", "")
            speaker = payload.get("speaker", "user")
        except Exception:
            text = data
            speaker = "user"

        ts = time.time()

        # --- 1) Detect user emotion ---
        user_scores = detect_emotion_scores(text)
        emotion_mem.add(ts, "user", text, user_scores)

        # --- 2) Store user input ---
        mem.add(text=text, speaker=speaker, ts=ts)

        # --- 3) Retrieve relevant memories ---
        retrieved = mem.search(text, top_k=3)
        mem_summary = summarize_memories(retrieved, concise=True)

        # --- 4) Compute blended emotion ---
        current_emotion, blended_scores = emotion_mem.blended_emotion()

        # --- 5) Generate Buddy reply ---
        context_str = f"User_emotion:{current_emotion}"
        reply_text = generate_reply(
            user_text=text,
            memories_summary=mem_summary + "\n" + context_str
        )

        # --- 6) Detect emotion for Buddy reply ---
        bot_scores = detect_emotion_scores(reply_text)
        emotion_mem.add(time.time(), "buddy", reply_text, bot_scores)
        mem.add(text=reply_text, speaker="buddy", ts=time.time())

        # --- 7) Generate expressive audio with constant voice ---
        emotion_profile = EMOTION_MAP.get(current_emotion, EMOTION_MAP["neutral"])
        audio_result = voice_buddy.generate_mp3_base64(reply_text, emotion_profile)

        # --- 8) Map emotion → expression ---
        expression = EXPRESSION_MAP.get(current_emotion, "neutral")

        # --- 9) Send JSON back to Expo ---
        out = {
            "text": reply_text,
            "emotion": current_emotion,
            "expression": expression,
            "blended_scores": blended_scores,
            "audio_b64": audio_result["b64"],
            "audio_name": audio_result["filename"],
            "audio_index": audio_result["index"]
        }
        await ws.send_text(json.dumps(out))
