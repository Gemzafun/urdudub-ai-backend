
import os
import io
import edge_tts

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="UrduDub AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SpeechRequest(BaseModel):
    text: str
    voice: str = "ur-PK-UzmaNeural"


@app.get("/")
def home():
    return {
        "app": "UrduDub AI",
        "status": "Backend online",
        "message": "Urdu speech service is ready"
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/speech")
async def generate_speech(request: SpeechRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Please enter text to speak."
        )

    if len(text) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Please use 2000 characters or fewer."
        )

    allowed_voices = {
        "ur-PK-UzmaNeural",
        "ur-PK-AsadNeural",
    }

    if request.voice not in allowed_voices:
        raise HTTPException(
            status_code=400,
            detail="Unsupported Urdu voice."
        )

    try:
        audio = io.BytesIO()

        communicate = edge_tts.Communicate(
            text,
            request.voice
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])

        if audio.tell() == 0:
            raise RuntimeError("No audio was generated.")

        audio.seek(0)

        return StreamingResponse(
            audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition":
                'attachment; filename="urdu-speech.mp3"'
            }
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Speech generation failed. Please try again."
        ) from exc
