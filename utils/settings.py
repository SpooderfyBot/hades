import os

from json import load, dump
from pydantic import BaseModel


class ServerSettings(BaseModel):
    # Changeable
    serve_static: bool = False

    # Authorization and cookies
    secure_key: str
    bot_auth: str
    live_server_auth: str

    client_id: int
    client_secret: str

    # Target urls
    gateway_url: str
    redirect_uri: str

    # Target domains
    spooderfy_domain: str = "spooderfy.com"
    gateway_domain: str = "gateway.spooderfy.com"


def load_settings(path: str) -> ServerSettings:
    if not os.path.exists(path):
        payload = {
            "serve_static": False,

            "secure_key": "",
            "bot_auth": "",
            "live_server_auth": "",
            "client_id": "",
            "client_secret": "",

            "gateway_url": "",
            "redirect_uri": "",

            "spooderfy_domain": "spooderfy.com",
            "gateway_domain": "gateway.spooderfy.com",
        }

        with open(path, "w+", encoding="UTF-8") as file:
            dump(payload, file, indent=4)

        raise RuntimeError(
            "No settings file has been found, one has been made and is"
            " required to be filled in."
        )

    with open(path, encoding="UTF-8") as file:
        raw = load(file)

    return ServerSettings(**raw)
