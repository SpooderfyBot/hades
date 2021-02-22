import aiohttp
import router
import requests
import typing as t

from fastapi import Request, responses
from pydantic import BaseModel

from server import Hades, render_template
from rooms import get_room, set_room, delete_room
from utils import login_required


class RoomCreationInfo(BaseModel):
    room_id: str
    preferred_stream_id: str = None
    webhook_url: str
    owner_id: int
    owner_name: str
    stream_name: str


with open('./templates/404.html', encoding="utf-8") as file:
    not_found_html = file.read()


room_html = requests.get("https://spooderfy.com/static/templates/room.html").content


class RoomEndpoints(router.Blueprint):
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
        "/room/{room_id}",
        endpoint_name="Movie Room",
        description="Get the room of a given id.",
        methods=["GET"],
    )
    @login_required
    async def room(self, request: Request, room_id: str):
        if get_room(room_id) is None:
            return responses.HTMLResponse(content=not_found_html, status_code=404)

        request.session['expect_requests'] = True

        html = await render_template('room.html')
        return responses.HTMLResponse(content=html, status_code=200)

    @router.endpoint(
        "/api/room/{room_id}/webhook",
        endpoint_name="Movie Room Webhook",
        description="Requests the room's webhook.",
        methods=["GET"],
    )
    @login_required
    async def get_webhook(self, request: Request, room_id: str):
        if not request.session['expect_requests']:
            return responses.ORJSONResponse({
                "status": 403,
                "data": "unauthorized"
            }, status_code=403)

        room = get_room(room_id)
        if room is None:
            return responses.ORJSONResponse(
                {
                    "status": 404,
                    "data": "No room with this id"
                },
                status_code=404
            )

        payload = {"url": room.webhook_url}
        return responses.ORJSONResponse(payload, status_code=200)

    @router.endpoint(
        "/api/room/{room_id}/info",
        endpoint_name="Movie Room Info",
        description="Requests the room's info like owner and title.",
        methods=["GET"],
    )
    @login_required
    async def get_info(self, request: Request, room_id: str):
        if not request.session['expect_requests']:
            return responses.ORJSONResponse({
                "status": 403,
                "data": "unauthorized"
            }, status_code=403)

        room = get_room(room_id)
        if room is None:
            return responses.ORJSONResponse(
                {
                    "status": 404,
                    "data": "No room with this id"
                },
                status_code=404
            )

        payload = {
            "owner_name": room.owner_name,
            "stream_name": room.stream_name,
        }
        return responses.ORJSONResponse(payload, status_code=200)

    @router.endpoint(
        "/api/room/{room_id}/stats",
        endpoint_name="Room Stats",
        description="Get's the stats of a given room.",
        methods=["GET"],
    )
    async def get_stats(self, request: Request, room_id: str):
        if get_room(room_id) is None:
            return responses.ORJSONResponse(
                {'status': 404, 'data': 'this room does not exist'},
                status_code=404
            )

        async with self.session.get(
                f"{self.app.gateway_url}/stats/{room_id}",
        ) as resp:
            resp.raise_for_status()

            return responses.ORJSONResponse(
                {
                    'status': 200,
                    'data': {
                        **(await resp.json())
                    }
                }
            )

    @router.endpoint(
        "/api/create/room",
        endpoint_name="Create Room",
        description="Creates a movie room with a given id",
        methods=["POST"],
    )
    async def create_room(self, request: Request, info: RoomCreationInfo):
        if request.headers.get("Authorization") != self.app.bot_token:
            return responses.ORJSONResponse(
                {'status': 403, 'data': 'not authorized'},
                status_code=403
            )

        server = self.app.live_server.get(sub_domain=info.preferred_stream_id)
        url = f"{server.control}/control/get" \
              f"?room={info.room_id}" \
              f"&authorization={self.app.worker_token}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            stream_info = await resp.json()

        url = f"{self.app.gateway_url}/add/{info.room_id}" \
              f"?live_server={server.control}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()

        set_room(
            info.room_id,
            server.id,
            info.webhook_url,
            info.owner_id,
            info.owner_name,
            info.stream_name,
        )
        return responses.ORJSONResponse(
            {
                'status': 200,
                'data': {
                    'url': f"https://{self.app.spooderfy_domain}/room/{info.room_id}",
                    'rtmp': server.rtmp,
                    'region': server.id,
                    'stream_key': stream_info['data'],
                }
            }
        )

    @router.endpoint(
        "/api/room/{room_id}/delete",
        endpoint_name="Delete Room",
        description="Deletes the room",
        methods=["DELETE"],
    )
    async def delete_room(self, request: Request, room_id: str):
        if request.headers.get("Authorization") != self.app.bot_token:
            return responses.ORJSONResponse(
                {'status': 403, 'data': 'not authorized'},
                status_code=403
            )

        room = get_room(room_id)
        if room is None:
            return responses.ORJSONResponse(
                {'status': 404, 'data': 'this room does not exist'},
                status_code=404
            )
        live_server = self.app.live_server.get(room.live_server_id)
        url = f"{live_server.control}/control/delete" \
              f"?room={room.room_id}" \
              f"&authorization={self.app.worker_token}"
        async with self.session.get(url) as resp:
            resp.raise_for_status()

        async with self.session.get(
            f"{self.app.gateway_url}/remove/{room_id}",
        ) as resp:
            resp.raise_for_status()

        delete_room(room_id)

        return responses.ORJSONResponse(
            {'status': 200, 'data': 'room deleted'},
            status_code=200
        )


def setup(app):
    app.add_blueprint(RoomEndpoints(app))
