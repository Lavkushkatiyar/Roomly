from fastapi import Request

from app.providers.gnani.stt import GnaniSTT


def get_gnani_stt(request: Request) -> GnaniSTT:
    return request.app.state.gnani_stt
