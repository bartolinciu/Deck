
import http.server, ssl
import asyncio
import websockets
import threading
import sys
import signal

from Deck.DeckDevice import DeckDevice

class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
	def __init__(self, *args, **kwargs):
		super(HTTPRequestHandler, self).__init__(*args, directory = "web", **kwargs)

class DeckServer:
	def __init__(self, interfaces = ["0.0.0.0"], port = 8080):
		self.devices = []
		self.onConnectListeners = []
		self.interfaces = interfaces
		self.threads = []
		self.servers = []
		self.restart = False
		self.stopped = False
		for i,interface in enumerate(interfaces):
			server_address = (interface, port)
			httpd = http.server.ThreadingHTTPServer( server_address, HTTPRequestHandler )
			httpd.timeout = 1
			def handle_timeout():
				pass
			httpd.handle_timeout = handle_timeout
			http_thread = threading.Thread( target = self.serve, args = [i] )
			self.servers.append(httpd)
			self.threads.append(http_thread)
			#httpd.socket = ssl.wrap_socket( httpd.socket, server_side = True, certfile = 'localhost.pem', ssl_version=ssl.PROTOCOL_TLS )


	def addOnConnectListener( self, listener, priority ):
		self.onConnectListeners.append( (priority, listener) )
		self.onConnectListeners.sort( key = lambda x: x[0] )

	def serve(self, i):
		print("starting http server at interface:", self.interfaces[i])
		while self.server_running:
			self.servers[i].handle_request()
		print("stopping http server at interface:", self.interfaces[i])


	def run(self):
		self.server_running = True
		for thread in self.threads:
			thread.start()

		try:
			asyncio.run( self.serve_websocket() ) 
		except KeyboardInterrupt:
			self.server_running = False
		for thread in self.threads:
			thread.join()
		print("http server stopped")
		self.stopped = True

	async def serve_websocket(self):
		print("starting websocket server")
		async with websockets.serve(self.on_connect, self.interfaces, 8765):
			while self.server_running:
				await asyncio.sleep(1)
		print("websocket server stopped")


	async def on_connect(self, websocket):
		print("New websocket connection")
		device = DeckDevice( websocket, self )

		async for message in websocket:
			await device.on_message(message, websocket)
			if str(message).startswith("identify") and device.ready:
				existing_device = None
				duplicate = False
				for tmpDevice in self.devices:
					if tmpDevice.get_uuid() == device.get_uuid():
						existing_device = tmpDevice
				if existing_device:
					existing_device.add_websocket( websocket )
					duplicate = True
					device = existing_device
				else:
					self.devices.append(device)
				for priority, listener in self.onConnectListeners:
					if await listener.on_connect( device, duplicate ):
						break
								


		print( "Closing websocket connection" )
		if not device.remove_websocket(websocket) and device in self.devices:
			self.devices.remove(device)	
			device.on_disconnect()

	def stop(self, reconnect = False):
		if reconnect:
			for device in self.devices:
				device.disconnect(reconnect = True)
		self.server_running = False

	def has_stopped(self):
		return self.stopped