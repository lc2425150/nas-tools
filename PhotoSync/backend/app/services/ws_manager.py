from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept(); self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict):
        dead = set()
        for c in self.active:
            try: await c.send_json(message)
            except: dead.add(c)
        self.active -= dead

ws_manager = ConnectionManager()
