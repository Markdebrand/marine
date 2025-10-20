import asyncio
import socketio


async def main():
    sio = socketio.AsyncClient()

    @sio.event
    async def connect():
        print("connected")

    @sio.on("ais_update")
    async def on_ais_update(data):  # noqa: ANN001
        print("ais_update:", len(data.get("vessels", [])))
        await sio.disconnect()

    await sio.connect("http://localhost:8000", socketio_path="/socket.io")
    await sio.wait()


if __name__ == "__main__":
    asyncio.run(main())
