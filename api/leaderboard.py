import aiohttp

import router
import typing as t

from server import Hades, render_template
from fastapi import Request, responses


class Leaderboard(router.Blueprint):
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

    @staticmethod
    def extract_username(request: Request):
        login_info = request.session.get('info')
        if login_info is not None:
            login_info = login_info['username']
        return login_info

    @router.endpoint(
        "/leaderboard",
        endpoint_name="General Leaderboard",
        description="Displays the a minified version of both server and members leaderboards.",
        methods=["GET"],
    )
    async def leaderboard_general(self, request: Request):
        template = await render_template(
            'development.html',
            login=self.extract_username(request)
        )
        return responses.HTMLResponse(content=template)

    @router.endpoint(
        "/leaderboard/about",
        endpoint_name="About Leaderboard",
        description="Displays the about page of the leaderboard and seasons system",
        methods=["GET"],
    )
    async def leaderboard_about(self, request: Request):
        template = await render_template(
            'lb_about.html',
            login=self.extract_username(request)
        )
        return responses.HTMLResponse(content=template)

    @router.endpoint(
        "/leaderboard/rewards",
        endpoint_name="Rewards Leaderboard",
        description="Displays the rewards of the seasons system",
        methods=["GET"],
    )
    async def leaderboard_rewards(self, request: Request):
        template = await render_template(
            'lb_rewards.html',
            login=self.extract_username(request)
        )
        return responses.HTMLResponse(content=template)

    @router.endpoint(
        "/leaderboard/members",
        endpoint_name="Global Members Leaderboard",
        description="Displays the global members leaderboard",
        methods=["GET"],
    )
    async def leaderboard_member(self, request: Request):
        template = await render_template(
            'development.html',
            login=self.extract_username(request)
        )
        return responses.HTMLResponse(content=template)

    @router.endpoint(
        "/leaderboard/servers",
        endpoint_name="Global Servers Leaderboard",
        description="Displays the global servers leaderboard",
        methods=["GET"],
    )
    async def leaderboard_guild(self, request: Request):
        template = await render_template(
            'development.html',
            login=self.extract_username(request)
        )
        return responses.HTMLResponse(content=template)


def setup(app):
    app.add_blueprint(Leaderboard(app))
