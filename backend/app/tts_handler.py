# backend/app/tts_handler.py
import io
import base64
from threading import Lock
from pathlib import Path
from pydub import AudioSegment
from gtts import gTTS

MAX_CACHE = 5

class VoiceBuddy:
    def __init__(self):
        self.counter = 0
        self.lock = Lock()
        self.audio_dir = Path("./audio_cache")
        self.audio_dir.mkdir(exist_ok=True)
    
    def _make_filename(self, idx):
        return self.audio_dir / f"msg_{idx}.mp3"
    
    def _apply_speed_and_pitch(self, audio_segment: AudioSegment, speed=1.0, pitch_shift=1.0):
        # change speed
        new_frame_rate = int(audio_segment.frame_rate * speed)
        audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={"frame_rate": new_frame_rate})
        audio_segment = audio_segment.set_frame_rate(44100)
        # change pitch (simplified)
        octaves = pitch_shift - 1.0
        new_sample_rate = int(audio_segment.frame_rate * (2.0 ** octaves))
        audio_segment = audio_segment._spawn(audio_segment.raw_data, overrides={"frame_rate": new_sample_rate})
        audio_segment = audio_segment.set_frame_rate(44100)
        return audio_segment

    def generate_mp3_base64(self, text: str, emotion_profile: dict) -> dict:
        """
        Generate expressive MP3 for given text.
        Voice remains constant.
        Speed & pitch vary with emotion_profile.
        """
        with self.lock:
            idx = self.counter % MAX_CACHE
            out_path = self._make_filename(idx)

            # 1) TTS generation - same voice
            tts = gTTS(text=text, lang="en")  # fixed voice
            tmp_bytes = io.BytesIO()
            tts.write_to_fp(tmp_bytes)
            tmp_bytes.seek(0)

            # 2) Load into AudioSegment
            audio = AudioSegment.from_file(tmp_bytes, format="mp3")

            # 3) Apply emotion-based expressiveness (speed + pitch)
            speed = float(emotion_profile.get("speed", 1.0))
            pitch = float(emotion_profile.get("pitch", 1.0))
            processed = self._apply_speed_and_pitch(audio, speed=speed, pitch_shift=pitch)

            # 4) Export MP3
            processed.export(out_path.as_posix(), format="mp3", bitrate="64k")

            # 5) Base64 encode
            with open(out_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")

            self.counter = (self.counter + 1) % MAX_CACHE

            return {"b64": b64, "filename": out_path.name, "index": idx}
