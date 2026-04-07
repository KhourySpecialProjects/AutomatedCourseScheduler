from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # schedule_id → { websocket: user_id }
        self.connections: dict[int, dict[WebSocket, int]] = {}

    async def connect(self, schedule_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if schedule_id not in self.connections:
            self.connections[schedule_id] = {}
        self.connections[schedule_id][websocket] = user_id

    def disconnect(self, schedule_id: int, websocket: WebSocket):
        schedule_conns = self.connections.get(schedule_id, {})
        user_id = schedule_conns.pop(websocket, None)
        if not schedule_conns:
            self.connections.pop(schedule_id, None)
        return user_id

    async def broadcast(self, schedule_id: int, message: dict):
        dead = []
        for connection in list(self.connections.get(schedule_id, {}).keys()):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.connections.get(schedule_id, {}).pop(connection, None)


manager = ConnectionManager()
