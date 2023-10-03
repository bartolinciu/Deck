import random
import os
import json

devicesPath = "devices"

def generateUUID():
	return "".join(["%02x" % i for i in random._urandom(8)])

class DeviceConfig:
	def init_new(self):
		self.configJSON = {
		"name": "new device",
		"uuid": generateUUID(),
		"currentLayout": "layout"
		}
		self.save()

	def __init__(self, name = None ):
		if name:
			self.init_from_file(name)
		else:
			self.init_new()

	def init_from_file(self, name):
		with open( os.path.join(devicesPath, name) ) as f:
			data = f.read()
			self.configJSON = json.loads(data)
		if self.configJSON["uuid"] != name:
			raise "filename doesn't match uuid"

	def get_layout(self):
		return self.configJSON["currentLayout"]

	def get_name(self):
		return self.configJSON["name"]

	def get_uuid(self):
		return self.configJSON["uuid"]

	def set_name(self, name):
		self.configJSON["name"] = name
		self.save()

	def set_layout(self, layout):
		self.configJSON["currentLayout"] = layout
		self.save()

	def save(self):
		with open( os.path.join(devicesPath, self.configJSON["uuid"]), "w" ) as f:
			f.write( json.dumps( self.configJSON ) )

	def delete(self):
		os.remove( os.path.join(devicesPath,  self.configJSON["uuid"]))


class DeviceManager:
	def __init__(self):
		self.configs = {}

	def load_devices(self):
		for root, dirs, files in os.walk( devicesPath ):
			for name in files:
				
				try:
					self.configs[name] = DeviceConfig(name)
				except Exception as e:
					print(e)
					continue
		

	def get_config(self, uuid):
		return self.configs[uuid]

	def new_device(self):
		config = DeviceConfig()
		self.configs[config.get_uuid()] = config
		return config

	def delete_device(self, device):
		uuid = device.get_uuid()
		self.configs.pop(uuid)
		device.delete()

device_manager = DeviceManager()
device_manager.load_devices()