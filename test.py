import asyncio
import websockets


async def echo(websocket):
	async for message in websocket:
		await websocket.send(message)



async def main():
	print("started")
	async with websockets.serve(echo, "0.0.0.0", 8765):
		await asyncio.Future()

asyncio.run(main())