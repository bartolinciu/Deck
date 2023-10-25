from Deck.DeckServer import DeckServer
import asyncio
from collections import namedtuple
from Deck import LayoutManager
from Deck import DeviceManager
import threading

import ifaddr
import re
import time
import os
import json

DeckAction = namedtuple( "DeckAction", "name label parameter_type parameter_label parameter_values function" )


class DeckController:
	actions = {}
	def __init__(self):
		self.srv = DeckServer( ["0.0.0.0"], 8080 )
		self.srv.addOnConnectListener( self, 1 )
		
		self.device_delegate = None
		self.running = False
		self.ready = True
		LayoutManager.layout_manager.add_layout_update_listener( self, 1 )
		with open( os.path.join( os.path.dirname(__file__) , "network.json" ), "rt" ) as f:
			self.network_configuration = json.loads( f.read() )

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

	def change_interfaces( self, interfaces ):
		self.ready= False
		listeners = self.srv.onConnectListeners
		self.srv.stop( reconnect = True )
		while not self.srv.has_stopped():
			time.sleep(0.01)
		self.srv = DeckServer( interfaces, 8080 )
		self.srv.onConnectListeners = listeners
		self.ready = True

	def get_network_configuration(self):
		return self.network_configuration

	def set_network_configuration(self, settings):
		self.network_configuration = settings
		with open( os.path.join( os.path.dirname(__file__) , "network.json" ), "wt") as f:
			f.write( json.dumps( self.network_configuration, indent = "\t" ) )
		adapters = ifaddr.get_adapters()
		adapter_dict = {}
		matcher = re.compile( "\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}" )
		for adapter in adapters:
			matching_ips = [ ip for ip in adapter.ips if bool( matcher.match( str( ip.ip) ) ) ]
			if len(matching_ips) > 0:
				adapter_dict[ matching_ips[0].nice_name ] = [ str(ip.ip) for ip in matching_ips ]
		ips = []


		for interface in settings:
			if interface["isActive"] and interface["name"] in adapter_dict:
				if interface["useAnyIp"]:
					ips.extend(adapter_dict[interface["name"]])
				else:
					for ip in interface["ips"]:
						if interface["ips"][ip] and ip in adapter_dict[interface["name"]]:
							ips.append(ip)
		self.change_interfaces(ips)

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
		self.running = True
		while self.running:
			while not self.ready:
				time.sleep(0.01)
			self.srv.run()

		

	def stop(self):
		self.running = False
		self.srv.stop()

from Deck.actions import *