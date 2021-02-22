import os
import typing as t
import aiohttp
import router
import urllib.parse

from typing import Optional
from fastapi import responses, Request
from server import Hades, SETTINGS
from utils import login_required

CLIENT_ID = SETTINGS.client_id
CLIENT_SECRET = SETTINGS.client_secret

ADD_SESSION = "http://spooderfy_gateway:8000/api/sessions/add"
REDIRECT_URI = SETTINGS.redirect_uri  # ""

DISCORD_BASE_URL = "https://discord.com/api"
DISCORD_OAUTH2_AUTH = "/oauth2/authorize"
DISCORD_OAUTH2_USER = "/users/@me"
DISCORD_OAUTH2_TOKEN = "/oauth2/token"

DISCORD_AVATAR = "https://images.discordapp.net/avatars/" \
                 "{user_id}/{avatar}.png?size=512"


def make_redirect_url() -> str:
    return (
            DISCORD_BASE_URL +
            DISCORD_OAUTH2_AUTH +
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI, safe='')}"
            "&response_type=code"
            "&scope=identify"
    )


def to_avatar_url(user_id: int, avatar_hash: str) -> str:
    return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"


class Authorization(router.Blueprint):
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
        "/api/@me",
        endpoint_name="Discord Info",
        description="Get the identification of the user session cookie.",
        methods=["GET"],
    )
    @login_required
    async def who_am_i(self, request: Request):
        data = request.session['info']
        return {
            "username": data['username'],
            "avatar": to_avatar_url(data['id'], data['avatar']),
        }

    @router.endpoint(
        "/authorized",
        endpoint_name="Discord Authorized",
        description="The successful login callback from discord.",
        methods=["GET"],
    )
    async def authorized(self, request: Request, code: str):
        token = await self.get_token(code)
        user = await self.get_user(token)

        url = request.session.get('redirect_to')
        resp = responses.RedirectResponse(url or "/home")

        request.session['info'] = user
        return resp

    @router.endpoint(
        "/login",
        endpoint_name="Discord Login",
        description="Login via discord.",
        methods=["GET"],
    )
    async def login(self, request: Request, redirect_to: str = "/home"):
        """
        The login api for discord, both logins and redirects are used on this
        endpoint, if code is None it means it is a standard login not  a
        redirect from discord, if it is just being spoofed then good job but
        its a invalid token.

        If the code is None the system redirects the user to the Oauth2 endpoint
        for discord's login, with a redirect_to cookie set for when the response
        comes back allowing us to seamlessly login and redirect users.

        Otherwise the code is extracted from the parameters and a POST request
        is made to discord to get the relevant data, a session id is produced
        and saved.
        """
        if request.session.get('info') is not None:
            return responses.RedirectResponse(redirect_to)

        request.session['redirect_to'] = redirect_to
        return responses.RedirectResponse(make_redirect_url())

    async def get_token(self, code: str) -> Optional[str]:
        data = {
            'client_id': int(CLIENT_ID),
            'client_secret': CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': REDIRECT_URI,
            'scope': 'identify'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        async with self.session.post(
            DISCORD_BASE_URL + DISCORD_OAUTH2_TOKEN,
            data=data,
            headers=headers,
        ) as resp:
            if resp.status >= 400:
                return None

            return (await resp.json())['access_token']

    async def get_user(self, token: str) -> Optional[dict]:
        async with self.session.get(
            DISCORD_BASE_URL + DISCORD_OAUTH2_USER,
            headers={"Authorization": f"Bearer {token}"}
        ) as resp:
            resp.raise_for_status()

            return await resp.json()


def setup(app):
    app.add_blueprint(Authorization(app))
