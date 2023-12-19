import websockets
import asyncio
import json
from Deck import DeviceManager
from Deck.AuthorizationManager import manager as AuthorizationManager
from Deck.ImageManager import manager as ImageManager
import time


class DeckDevice:
	def __init__(self, websocket, server):
		self.server = server
		self.websockets = [ websocket ]
		self.onMessageListeners = []
		self.config = None
		self.loop = asyncio.get_running_loop()
		self.handler = None
		self.defunct = False
		self.ready = False
		#ImageManager.add_image_update_listener( self, 1 )
		self.layout = None
		self.waiting_for_pascode = False
		self.passcode = ""

	def set_layout(self, layout_name, layout):
		self.loop.create_task(self.set_layout_async(layout_name, layout)  )

	def merge(self, target_uuid):
		if not self.ready:
			return
		self.send_message("merge:"+target_uuid)
		self.forget()
		self.disconnect(reconnect = True)

	async def set_layout_async(self, layout_name, layout):
		if not self.ready:
			return
		if self.config.get_layout == layout_name and self.layout == layout:
			return
			
		self.config.set_layout(layout_name)
		self.layout = layout

		def get_image(button):
			if "image" in button:
				definition = ImageManager.get_image_definition( button["image"] )
				if definition:
					return definition["hostingPath"]
			return None

		await self._send_message( json.dumps( 
					[ 
						{"name": layout[button]["name"], "image": get_image(layout[button]) } for button in layout 
					] 
				) 
			)

	def disconnect(self, reconnect = False):
		self.loop.create_task( self.disconnect_async(reconnect) ) 

	async def disconnect_async(self, reconnect):
		for socket in self.websockets:
			if reconnect:
				await socket.send("reconnect")
			await socket.close()

	def send_message(self, message):
		self.loop.create_task( self._send_message(message) ) 

		
	async def _send_message(self, message):
		for socket in self.websockets:
			await socket.send(message)
		

	def addOnMessageListener( self, listener, priority ):
		self.onMessageListeners.append( (priority, listener) )
		self.onMessageListeners.sort( key = lambda x: x[0])

	def rename_layout(self, new_name):
		if not self.ready:
			return
		self.config.set_layout(new_name)

	def get_layout_id(self):
		if not self.ready:
			return ""
		return self.config.get_layout()

	def get_name(self):
		if not self.ready:
			return ""
		return self.config.get_name()

	def set_name(self, name):
		if not self.ready:
			return
		self.config.set_name(name)

	def set_event_handler(self, handler):
		self.handler = handler

	def get_uuid(self):
		if not self.ready:
			return ""
		return self.config.get_uuid()

	def forget(self):
		if not self.ready:
			return
		self.defunct = True
		DeviceManager.device_manager.delete_device(self.config)

	def get_configuration(self):
		return self.config

	def request_passcode(self):
		self.send_message("authorize")
		self.waiting_for_pascode = True
		while self.waiting_for_pascode:
			time.sleep(0.01)

		return self.passcode

	def grant_access(self):
		self.config = DeviceManager.device_manager.new_device()
		self.send_message( "accept:" + self.config.get_uuid() )
		self.ready = True

	def reject_access(self):
		self.send_message("reject")

	async def on_message(self, message, websocket):
		if self.defunct:
			return
		if message == "ping":
			await websocket.send("pong")
			return

		message_str = str(message)
		command = ""
		argument = ""
		print(message_str)

		if ":" in message_str:
			command, argument = message_str.split(":")

		if command == "request":
			AuthorizationManager.request_authorization(self)
			return

		elif  command == "identify":
			uuid = argument
			print( "connections list:", self.websockets )
			try:
				self.config = DeviceManager.device_manager.get_config( uuid )
				self.ready = True
			except KeyError:
				print("device configuration not found")
				AuthorizationManager.request_authorization(self)
			
			return

		elif command == "passcode":
			self.passcode = argument
			self.waiting_for_pascode = False
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