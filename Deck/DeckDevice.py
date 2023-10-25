import websockets
import asyncio
import json
from Deck import DeviceManager
from Deck import AuthorizationManager

class DeckDevice:
	def __init__(self, websocket, server):
		self.server = server
		self.websockets = [ websocket ]
		self.onMessageListeners = []
		self.config = DeviceManager.DeviceConfig("0000000000000000")
		self.loop = asyncio.get_running_loop()
		self.handler = None
		self.defunct = False
		self.ready = False

	def set_layout(self, layout_name, layout):
		self.loop.create_task(self.set_layout_async(layout_name, layout)  )

	async def set_layout_async(self, layout_name, layout):
		self.config.set_layout(layout_name)
		await self._send_message( json.dumps( [ layout[button]["name"] for button in layout ] ) )

	def disconnect(self, reconnect = False):
		self.loop.create_task( self.disconnect_async(reconnect) ) 

	async def disconnect_async(self, reconnect):
		for socket in self.websockets:
			if reconnect:
				await socket.send("reconnect")
			await socket.close()
		
	async def _send_message(self, message):
		for socket in self.websockets:
			await socket.send(message)
		

	def addOnMessageListener( self, listener, priority ):
		self.onMessageListeners.append( (priority, listener) )
		self.onMessageListeners.sort( key = lambda x: x[0])

	def get_layout_id(self):
		return self.config.get_layout()

	def get_name(self):
		return self.config.get_name()

	def set_name(self, name):
		self.config.set_name(name)

	def set_event_handler(self, handler):
		self.handler = handler

	def get_uuid(self):
		return self.config.get_uuid()

	def forget(self):
		self.defunct = True
		DeviceManager.device_manager.delete_device(self.config)

	async def on_message(self, message, websocket):
		if self.defunct:
			return
		if message == "ping":
			await websocket.send("pong")
			return

		message_str = str(message)
		command = ""
		argument = ""

		if ":" in message_str:
			command, argument = message_str.split(":")

		if command == "authorize":
			self.config = DeviceManager.device_manager.new_device()
			if AuthorizationManager.AuthorizationManager.is_passcode_valid(argument):
				await self._send_message( "accept:" + self.config.get_uuid() )
				self.ready = True
			else:
				await self._send_message("reject")
			return


		if  command == "identify":
			uuid = argument
			print( "connections list:", self.websockets )
			try:
				self.config = DeviceManager.device_manager.get_config( uuid )
				self.ready = True
			except KeyError:
				print("device configuration not found")
				await self._send_message("reject")
			
			return



		for priority, listener in self.onMessageListeners:
			await listener.on_message(self, message)

	def add_websocket(self, websocket):
		self.websockets.append(websocket)

	def on_disconnect(self):
		if self.handler:
			self.handler.refresh()

	def remove_websocket(self, websocket):
		try:
			self.websockets.remove(websocket)
		except ValueError:
			pass

		return bool(self.websockets)