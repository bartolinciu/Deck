from Deck.DeckServer import DeckServer
import asyncio
from collections import namedtuple
from Deck import LayoutManager
from Deck import DeviceManager
from Deck.ImageManager import manager as ImageManager
from Deck.BindingManager import manager as BindingManager
import threading

import ifaddr
import re
import time
import os
import json
import sys

import Deck

DeckAction = namedtuple( "DeckAction", "name label parameters function" )

if sys.platform=="win32":
	import win32process
	import psutil

class DeckController:
	actions = {  }
	network_filename = "network.json"
	network_path = os.path.join( Deck.config_path, network_filename )
	def __init__(self):

		if not os.path.isdir( Deck.config_path ):
			os.makedirs(Deck.config_path)
		
		if os.path.isfile(self.network_path):
			with open( self.network_path, "rt" ) as f:
				self.network_configuration = json.loads( f.read() )
		else:
			self.network_configuration = []
			self.save()

		ips = self.get_ips_from_configuration(self.network_configuration)
		self.srv = DeckServer( ips, 8080 )
		self.srv.addOnConnectListener( self, 1 )

		
		self.device_delegate = None
		self.running = False
		self.ready = True
		LayoutManager.layout_manager.add_layout_update_listener( self, 1 )
		LayoutManager.layout_manager.add_rename_listener(self, 1)
		ImageManager.add_image_update_listener( self, 1 )
		
		self.window = None
		self.app = None
		self.title = None

		self.window_watchdog = threading.Thread( target = self.monitor_active_window, daemon = True )

		self.debug_time = None

	def monitor_active_window(self):
		import pywinctl
		import pywintypes
		while self.running:
			try:
				window = pywinctl.getActiveWindow()
				self.debug_time = time.time()
				if window == None:
					continue

				window_changed = ( window != self.window )
				app = ""
				try:
					if sys.platform == "win32":
						pid = win32process.GetWindowThreadProcessId( window.getHandle() )[1]
						app = psutil.Process(pid).exe().split("\\")[-1]
					else:
						app = window.getAppName()
				except pywintypes.com_error:
					pass
				title = window.title

				
				app_changed = (app != self.app )
				title_changed = (title != self.title)
				self.window = window
				self.app = app
				self.title = title

				if window_changed or app_changed or title_changed:
					self.active_window_changed()
			except pywintypes.error:
				pass

			time.sleep(0.05)
		print("stopping window watchdog")

	def active_window_changed(self):
		bindings = BindingManager.get_bindings_by_window( self.app, self.title )
		title_specific_bindings = []
		title_universal_bindings = []
		universal_bindings = []
		
		for binding in bindings:
			if binding["title"] == "*" and binding["device"] == "*":
				universal_bindings.append(binding)
			if binding["title"] != "*":
				title_specific_bindings.append(binding)
			else:
				title_universal_bindings.append(binding)


		def get_binding_by_device(device):
			for binding_list in [ title_specific_bindings, title_universal_bindings ]:
				for binding in binding_list:
					if binding["device"] == device.get_uuid():
						return binding
			for binding in title_specific_bindings:
				if binding["device"] == "*":
					return binding

			if len(universal_bindings) > 0:
				return universal_bindings[0]
			return None

		
		for device in self.srv.devices:
			device_time = time.time()
			binding = get_binding_by_device( device )
			if binding == None:
				continue
			layout_name = binding["layout"]
			if layout_name != device.get_layout_id():
				layout = LayoutManager.layout_manager.get_layout(layout_name)
				device.set_layout( layout_name, layout )


	def on_rename(self, old_name, new_name):
		for device in self.srv.devices:
			if device.get_layout_id() == old_name:
				device.rename_layout(new_name)

	def on_image_update(self, old_name, new_name):
		print("Controller.on_image_update")
		LayoutManager.layout_manager.update_images(old_name, new_name)

	def action( label="Action", parameters = [] ):
		def decorator(function):
			name = function.__name__
			action = DeckAction( name, label, parameters, function )
			DeckController.actions[ name ] = action
			print("Discovered action:", name)
			return function
		return decorator

	def on_layout_update( self, layout_name, is_visual ):
		layout = LayoutManager.layout_manager.get_layout(layout_name)
		if is_visual:
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

	def get_ips_from_configuration(self, settings):
		
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
		return ips

	def set_network_configuration(self, settings):
		self.network_configuration = settings
		self.save()
		ips = self.get_ips_from_configuration(settings)
		self.change_interfaces(ips)

	def save(self):
		with open( self.network_path, "wt") as f:
			f.write( json.dumps( self.network_configuration, indent = "\t" ) )

	async def on_message(self, device, message):

		action = None
		parameter = None
		uuid = None
		message_str = str(message)

		layout = LayoutManager.layout_manager.get_layout( device.get_layout_id() )
		if layout == None:
			print("Empty layout")
			return

		if not message_str in layout:
			print("Button not found:", message_str)
			return

		button = layout[message_str]

		if not "action" in button:
			return

		actionName = button["action"]
			
		if not actionName in self.actions:
			print("Invalid action:", actionName)
			return

		action = self.actions[actionName]

		if len(action.parameters) > 0:
			if not "parameters" in button or len(button["parameters"]) != len(action.parameters):
				print("Missing parameter for action:", actionName)
				return
				
			await action.function( device, *button["parameters"] ) 
		else:
			await action.function(device) 

	async def on_connect(self, device, is_repeated):
		layout = LayoutManager.layout_manager.get_layout( device.get_layout_id() )
		if layout == None:
			layout = LayoutManager.LayoutManager.empty_layout
		await device.set_layout_async(device.get_layout_id(),layout)
		if not is_repeated:
			device.addOnMessageListener( self, 1 )
		if self.device_delegate:
			self.device_delegate.refresh()
			device.set_event_handler(self.device_delegate)
		return False

	def run(self):
		print("Starting controller")
		self.running = True
		self.window_watchdog.start()
		while self.running:
			try:
				while not self.ready:
					time.sleep(0.01)
				self.srv.run()
			except KeyboardInterrupt:
				self.running = False

		

	def stop(self):
		print("Stopping controller")
		self.running = False
		self.srv.stop()
		

@DeckController.action( label = "None", parameters=[] )
def none_action(device):
	pass

from Deck.actions import *