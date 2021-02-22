import uvicorn
import typing as t
import router
import asyncio
import multiprocessing as mp


from fastapi import responses
from server import Hades
from utils import load_settings


APP_FILES = [
    "api.auth",
    "api.rooms",
    "api.leaderboard",
    "api.quick_links"
]


with open('./templates/404.html', encoding="utf-8") as file:
    not_found_html = file.read()


def import_callback(app_: Hades, endpoint: t.Union[router.Endpoint, router.Websocket]):
    if isinstance(endpoint, router.Endpoint):
        app_.add_api_route(
            endpoint.route,
            endpoint.callback,
            name=endpoint.name,
            methods=endpoint.methods,
            **endpoint.extra)
    else:
        raise NotImplementedError


async def on_404(_req, _exec):
    return responses.HTMLResponse(status_code=404, content=not_found_html)

app = Hades(
    title="Spooderfy",
    description="The Discord bot for all your movie needs.",
    docs_url=None,
    redoc_url="/api/docs",
    openapi_url="/api/openapi.json",
    exception_handlers={404: on_404},
)


router = router.Router(app, APP_FILES, import_callback)

if __name__ == '__main__':
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        # workers=mp.cpu_count()
    )
