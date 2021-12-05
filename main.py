#!/usr/bin/env python3
import http.server, ssl
import asyncio
import websockets
import threading

from pynput.keyboard import Key, Controller as KeyboardController

keyboard = KeyboardController()

print("starting http server")

def startHTTP():
	server_address = ('0.0.0.0', 8080)
	httpd = http.server.HTTPServer( server_address, http.server.SimpleHTTPRequestHandler )
	#httpd.socket = ssl.wrap_socket( httpd.socket, server_side = True, certfile = 'localhost.pem', ssl_version=ssl.PROTOCOL_TLS )
	httpd.serve_forever()

http_thread = threading.Thread( target = startHTTP )
http_thread.start()

async def echo(websocket):
	async for message in websocket:
		print(message)
		keyboard.press( Key.alt_l )
		keyboard.press( Key.tab )
		keyboard.release( Key.tab)
		keyboard.release( Key.alt_l )

		await websocket.send(message)

async def main():
	print("started")
	async with websockets.serve(echo, "0.0.0.0", 8765):
		await asyncio.Future()

print("starting WebSocket server")
asyncio.run(main())


