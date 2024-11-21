from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
from redis.asyncio import Redis
from contextlib import asynccontextmanager
import json

app = FastAPI()

# Declare Redis globally
redis: Redis = None

CHANNEL_PREFIX = "vehicle:"

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis
    redis = Redis.from_url(
        "rediss://red-cnte32f79t8c73ad3l2g:sEpnZvTSGJjHkYNNn8biheFQ6OrHEMd3@singapore-redis.render.com:6379"
    )
    try:
        yield
    finally:
        await redis.close()

app.router.lifespan_context = lifespan

@app.websocket("/send/{vehicle_number}")
async def send_message(websocket: WebSocket, vehicle_number: str):
    """WebSocket route to send a message to a specific vehicle's Redis channel."""
    print(vehicle_number)
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            print(data)
            channel = f"{CHANNEL_PREFIX}{vehicle_number}"
            await redis.publish(channel, json.dumps(data))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for vehicle {vehicle_number}")
    finally:
        await websocket.close()

@app.websocket("/receive/{vehicle_number}")
async def receive_message(websocket: WebSocket, vehicle_number: str):
    """WebSocket route to receive messages from a specific vehicle's Redis channel."""
    await websocket.accept()
    channel = f"{CHANNEL_PREFIX}{vehicle_number}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and "data" in message:
                # Ensure message is properly sent
                await websocket.send_text(message["data"].decode("utf-8"))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for vehicle {vehicle_number}")
    finally:
        await pubsub.unsubscribe(channel)
        await websocket.close()
