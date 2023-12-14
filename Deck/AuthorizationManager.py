import os
import threading
import time
import random
import json

class AuthorizationManager:
	auth_file_name = "auth.json"
	auth_file_path = os.path.join( os.path.dirname(__file__) , auth_file_name )
	def __init__(self, path = None):
		if not os.path.isfile(self.auth_file_path):
			self.config = {"method": "all", "passcode":"", "blacklist": []}
			self.save()
		else:
			with open( self.auth_file_path, "rt" ) as f:
				self.config = json.loads( f.read() )

		self.delegate = None

		self.timeout = 30

	def save(self):
		with open(self.auth_file_path, "wt") as f:
			f.write( json.dumps( self.config , indent = "\t" ))

	def set_method(self, method):
		self.config["method"] = method
		self.save()

	def set_passcode(self, passcode):
		self.config["passcode"] = passcode
		self.save()

	def get_method(self):
		return self.config["method"]

	def get_passcode(self):
		return self.config["passcode"]

	def get_temp_passcode(self):
		code = str(round( ((time.time()//self.timeout)*self.timeout ** 123) % 10000 ))
		return "0" * (4-len(code)) + code

	def set_delegate(self, delegate):
		self.delegate = delegate

	def _request_authorization(self, device):
		authorized = False
		match self.config["method"]:
			case "none":
				authorized = False

			case "all":
				authorized =  True

			case "pass":
				for i in range(3):
					authorized = device.request_passcode() == self.config["passcode"]
					if authorized:
						break

			case "temp":
				for i in range(3):
					authorized = device.request_passcode() == self.get_temp_passcode()
					if authorized:
						break

			case "delegate":
				if self.delegate == None:
					authorized = False
				else:
					authorized = self.delegate.request_authorization(device)

		if authorized:
			device.grant_access()
		else:
			device.reject_access()

	def request_authorization( self, device):
		threading.Thread( target = self._request_authorization, args = (device,), daemon = True ).start()

manager = AuthorizationManager()