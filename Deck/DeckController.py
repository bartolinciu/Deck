from Deck.DeckServer import DeckServer
import asyncio
from collections import namedtuple
from Deck import LayoutManager
from Deck import DeviceManager

DeckAction = namedtuple( "DeckAction", "name label parameter_type parameter_label parameter_values function" )


class DeckController:
	actions = {}
	def __init__(self):
		self.srv = DeckServer( ["0.0.0.0"], 8080 )
		self.srv.addOnConnectListener( self, 1 )
		
		self.device_delegate = None

		LayoutManager.layout_manager.add_layout_update_listener( self, 1 )

	def action( label="Action", parameter_type="None", parameter_label="Parameter", parameter_values=[] ):
		def decorator(function):
			name = function.__name__
			action = DeckAction( name, label, parameter_type, parameter_label, parameter_values, function )
			DeckController.actions[ name ] = action
			print("Discovered action:", name)
			return function
		return decorator

	def on_layout_update( self, layout_name ):
		layout = LayoutManager.layout_manager.get_layout(layout_name)
		for device in self.srv.devices:
			if device.get_layout_id() == layout_name:
				device.set_layout( layout_name, layout )



	async def on_message(self, device, message):

		action = None
		parameter = None
		uuid = None
		message_str = str(message)

		layout = LayoutManager.layout_manager.get_layout( device.get_layout_id() )
		actionName = layout[str(message)]["action"]

		try:
			action = self.actions[actionName]
		except KeyError:
			print("Invalid action:", actionName)
			return

		if not action.parameter_type == "None":
			try: 
				parameter = layout[str(message)]["parameter"]
			except KeyError:
				print("Missing parameter for action:", actionName)
				return
			await action.function( device, parameter ) 
		else:
			await action.function(device) 

	async def on_connect(self, device, is_repeated):
		layout = LayoutManager.layout_manager.get_layout( device.get_layout_id() )
		await device.set_layout_async(device.get_layout_id(),layout)
		if not is_repeated:
			device.addOnMessageListener( self, 1 )
		if self.device_delegate:
			self.device_delegate.refresh()
			device.set_event_handler(self.device_delegate)
		return False

	def run(self):
		self.srv.start()

	def stop(self):
		self.srv.stop()

from Deck.actions import *