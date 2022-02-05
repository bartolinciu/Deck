#!/usr/bin/env python3
import http.server, ssl
import asyncio
import websockets
import threading
import json
import time
#import win32gui, win32process, psutil


from pynput.keyboard import Key, Controller as KeyboardController

keyboard = KeyboardController()

print("starting http server")

def loadLayout(file):
	with open( file ) as f:
		data = f.read()
		data = json.loads(data)
		return data


keymapping = {}

for i in Key:
	keymapping[i.name] = i

layout = {}
macros = {}

def loadMacros( file ):
	global macros
	with open(file) as f:
		data = f.read()
		macros = json.loads(data)



async def executeMacro( websocket, macro_name ):
	macro = macros[macro_name]
	for step in macro:
		print(step)
		if step["action"] in ["press", "release"]:
			key = step["key"]
			if len(key) > 1:
				key = keymapping[key]
			if step["action"] == "press":
				keyboard.press(key)
			else:
				keyboard.release(key)
		elif step["action"] == "delay":
			time.sleep( step["time"] )
			



async def switchWindow( websocket ):
	keyboard.press( Key.alt_l )
	keyboard.press( Key.tab )
	keyboard.release( Key.tab)
	keyboard.release( Key.alt_l )

async def updateLayout( websocket, l ):
	global layout
	"""
	name = ""
	try:
		pid = win32process.GetWindowThreadProcessId( win32gui.GetForegroundWindow() )
		name = psutil.Process( pid[-1] ).name()
		print(name)
		print(win32gui.GetForegroundWindow())
	except:
		pass
	"""
	layout = loadLayout(l)
	msg = []
	for button, content in enumerate( layout ):
		msg.append( layout[content]["name"])
	await websocket.send(json.dumps(msg))


actions = { "switchWindow": switchWindow, "switch": updateLayout, "macro":executeMacro }
require_parameter = {"switchWindow":False, "switch": True, "macro":True}

server_running = True

def startHTTP():
	server_address = ('0.0.0.0', 8080)
	httpd = http.server.HTTPServer( server_address, http.server.SimpleHTTPRequestHandler )
	httpd.timeout = 1
	def handle_timeout():
		pass
	httpd.handle_timeout = handle_timeout
	#httpd.socket = ssl.wrap_socket( httpd.socket, server_side = True, certfile = 'localhost.pem', ssl_version=ssl.PROTOCOL_TLS )
	while server_running:
		print("handling request")
		httpd.handle_request()
http_thread = threading.Thread( target = startHTTP )
http_thread.start()
async def echo(websocket):
	global layout
	async for message in websocket:
		if message == "get":
			await updateLayout(websocket, "layout.json")
		else:
			action = None
			parameter = None
			try:
				action = actions[layout[message]["action"]]
			except KeyError:
				continue
			
			if require_parameter[layout[message]["action"]]:
				try: 
					parameter = layout[message]["parameter"]
				except KeyError:
					continue
				await action( websocket, parameter )
			else:
				await action(websocket)



async def main():
	loadMacros( "macros.json" )
	global server_running
	async with websockets.serve(echo, "0.0.0.0", 8765):
		await asyncio.Future()


print("starting WebSocket server")
try:
	asyncio.run(main())
except KeyboardInterrupt:
	server_running = False
print( "websocket server stopped" )
http_thread.join()

