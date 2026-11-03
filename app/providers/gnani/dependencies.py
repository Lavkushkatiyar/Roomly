from fastapi import Request

from app.providers.gnani.stt import GnaniSTT
from app.providers.gnani.text_to_speech import GnaniTTS


def get_gnani_stt(request: Request) -> GnaniSTT:
    return request.app.state.gnani_stt


def get_gnani_tts(request: Request) -> GnaniTTS:
    return request.app.state.gnani_tts
