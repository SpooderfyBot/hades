import sqlite3
from typing import Optional


conn = sqlite3.connect("rooms.db")
conn.execute(
    """CREATE TABLE IF NOT EXISTS rooms(
        room_id TEXT UNIQUE PRIMARY KEY,
        live_server_id TEXT,
        webhook_url TEXT,
        owner_id TEXT,
        owner_name TEXT,
        stream_name TEXT        
    )"""
)
conn.commit()


class Room:
    def __init__(
        self,
        room_id: str,
        live_server_id: str,
        webhook_url: str,
        owner_id: str,
        owner_name: str,
        stream_name: str,
    ):
        self.room_id = room_id
        self.live_server_id = live_server_id
        self.webhook_url = webhook_url
        self.owner_id = int(owner_id)
        self.owner_name = owner_name
        self.stream_name = stream_name


def get_room(room_id: str) -> Optional[Room]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
    maybe_room = cur.fetchone()
    cur.close()
    if maybe_room is None:
        return None
    return Room(*maybe_room)


def set_room(
    room_id: str,
    live_server_id: str,
    webhook: str,
    owner_id: int,
    owner_name: str,
    stream_name: str,
):
    owner_id = int(owner_id)

    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO rooms(
                room_id, 
                live_server_id, 
                webhook_url,
                owner_id,
                owner_name,
                stream_name
            ) VALUES (?, ?, ?, ?, ?, ?)""",
            (
                room_id,
                live_server_id,
                webhook,
                owner_id,
                owner_name,
                stream_name,
            )
        )
    except:
        cur.execute(
            """UPDATE rooms 
            SET 
            live_server_id = ?, 
            webhook_url = ?,
            owner_id = ?,
            owner_name = ?,
            stream_name = ?
            WHERE room_id = ?
            """,
            (
                live_server_id,
                webhook,
                owner_id,
                owner_name,
                stream_name,
                room_id,
            )
        )
    cur.close()
    conn.commit()


def delete_room(room_id: str):
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM rooms WHERE room_id = ?",
        (room_id,)
    )
    cur.close()
    conn.commit()

