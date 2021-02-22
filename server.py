from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jinja2 import Environment, FileSystemLoader

from distribution import LiveServerManager, LiveServer
from sessions import SessionCollection
from utils.settings import load_settings


SETTINGS = load_settings("./settings.json")


templates = Environment(
    loader=FileSystemLoader("./templates"),
    enable_async=True,
)


async def render_template(template: str, *args, **kwargs):
    t = templates.get_template(template)
    if t is None:
        raise ValueError(f"template {template!r} does not exist")

    return await t.render_async(*args, **kwargs)


server = LiveServer(
    'us-1',
    'us1.spooderfy.com',
    'us-live-1.spooderfy.com',
)

server2 = LiveServer(
    'us-2',
    'us2.spooderfy.com',
    'us-live-2.spooderfy.com',
)


class Hades(FastAPI):
    def __init__(
            self,
            **extra,
    ):
        super().__init__(**extra)

        if SETTINGS.serve_static:
            self.mount("/static", StaticFiles(directory="static"), name="static")

        self.secure_key = SETTINGS.secure_key
        self.bot_token = SETTINGS.bot_auth
        self.worker_token = SETTINGS.live_server_auth
        self.spooderfy_domain = SETTINGS.spooderfy_domain
        self.gateway_domain = SETTINGS.gateway_domain

        self.live_server = LiveServerManager(server)
        self.live_server.add_server(server2)

        self.gateway_url = SETTINGS.gateway_url

        self.sessions = SessionCollection()
        self.sessions.mount_middleware(self)
