import aiohttp

import router
import typing as t

from server import Hades, render_template
from fastapi import responses, Request


BOT_INVITE = ""
BOT_SUPPORT_SERVER = ""


class QuickLinks(router.Blueprint):
    def __init__(self, app: Hades):
        self.app = app

        self.app.on_event("startup")(self.init_session)
        self.app.on_event("shutdown")(self.close)

        self.session: t.Optional[aiohttp.ClientSession] = None

    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session is not None:
            await self.session.close()

    @router.endpoint(
        "/",
        endpoint_name="Index",
        description="The index page",
        methods=["GET"],
    )
    async def index(self):
        return responses.RedirectResponse("/home")

    @router.endpoint(
        "/home",
        endpoint_name="Home",
        description="The home page",
        methods=["GET"],
    )
    async def home(self, request: Request, render_nav: bool = True):
        login_info = request.session.get('info')
        if login_info is not None:
            login_info = login_info['username']

        template = await render_template(
            'home.html',
            render_nav=render_nav,
            login=login_info,
        )
        return responses.HTMLResponse(content=template)

    @router.endpoint(
        "/invite",
        endpoint_name="Home",
        description="The home page",
        methods=["GET"],
    )
    async def invite(self):
        return responses.RedirectResponse(BOT_INVITE)

    @router.endpoint(
        "/discord",
        endpoint_name="Home",
        description="The home page",
        methods=["GET"],
    )
    async def discord(self):
        return responses.RedirectResponse(BOT_SUPPORT_SERVER)


def setup(app):
    app.add_blueprint(QuickLinks(app))
