from typing import Optional, Dict, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import base64
import os
from uuid import uuid4

from dotenv import load_dotenv
load_dotenv(override=True)

from agents.question_generator import generate_curriculum_aware_question
from main import MusicTheoryEngine


app = FastAPI(title="MusicTheoryTutor API", version="0.1.0")

# Serve generated media (audio, optional images if needed)
MEDIA_ROOT = os.path.join(os.getcwd(), "media")
MEDIA_AUDIO = os.path.join(MEDIA_ROOT, "audio")
os.makedirs(MEDIA_AUDIO, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")


# In-memory session history (simple prototype)
SESSIONS: Dict[str, list] = {}


class GenerateRequest(BaseModel):
    instrument: str
    grade: int


class GenerateResponse(BaseModel):
    notation_image_base64: Optional[str] = None
    audio_url: Optional[str] = None
    explanation: Optional[str] = None
    question: str
    options: Dict[str, str]
    correct: str


def _file_to_base64(path: str) -> Optional[str]:
    try:
        if not path or not os.path.exists(path):
            return None
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    try:
        # Rotate an exercise type internally (Comprehensive Theory)
        import random
        allowed = [
            "Intervals", "Chords", "Scales", "Rhythm", "Harmony", "Ear Training", "Musical Form",
        ]
        # For lower grades you could add "Note Reading"; keep minimal for API
        ex_type = random.choice(allowed)

        # Ask the generator
        q = generate_curriculum_aware_question(req.instrument, req.grade, ex_type)
        if not isinstance(q, dict) or not q.get("question"):
            return GenerateResponse(question="", options={"A":"","B":"","C":"","D":""}, correct="A")

        question_text = str(q.get("question", "")).strip()
        options = q.get("options", {}) or {}
        correct_letter = str(q.get("correct_answer", "A")).strip().upper()

        # Build notation/audio using engine
        engine = MusicTheoryEngine()
        result = engine.generate_notation(
            question_text,
            instrument=req.instrument,
            exercise_type=ex_type,
            question_data=q,
        )

        notation_b64: Optional[str] = None
        audio_url: Optional[str] = None
        if isinstance(result, dict) and result.get("success"):
            # image → base64
            img = (result.get("image") or {}).get("image_path")
            notation_b64 = _file_to_base64(img)
            # audio → write file → url
            audio = result.get("audio") or {}
            audio_b64 = audio.get("audio_base64")
            audio_path = audio.get("audio_path")
            try:
                audio_bytes = None
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                elif audio_path and os.path.exists(audio_path):
                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()
                if audio_bytes:
                    fname = f"{uuid4().hex}.wav"
                    out_path = os.path.join(MEDIA_AUDIO, fname)
                    with open(out_path, "wb") as f:
                        f.write(audio_bytes)
                    audio_url = f"/media/audio/{fname}"
            except Exception:
                audio_url = None

        return GenerateResponse(
            notation_image_base64=notation_b64,
            audio_url=audio_url,
            explanation=q.get("explanation"),
            question=question_text,
            options={"A": options.get("A", ""), "B": options.get("B", ""), "C": options.get("C", ""), "D": options.get("D", "")},
            correct=correct_letter,
        )

    except Exception as e:
        return GenerateResponse(question="", options={"A":"","B":"","C":"","D":""}, correct="A")


@app.get("/status")
def status():
    import os
    try:
        from dotenv import dotenv_values
        from_dotenv = bool(dotenv_values(".env").get("OPENAI_API_KEY"))
    except Exception:
        from_dotenv = None
    return {
        "has_env": bool(os.getenv("OPENAI_API_KEY")),
        "from_dotenv": from_dotenv,
        "cwd": os.getcwd(),
    }


