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
			self.config = {"method": "all", "passcode":""}
			self.save()
		else:
			with open( self.auth_file_path, "rt" ) as f:
				self.config = json.loads( f.read() )

		self.delegate = None
		self.salt1 = random.random()
		self.salt2 = random.random()

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
		return self.config("passcode")

	def get_temp_passcode(self):
		return round((((time.time()//60)*60) ** (self.salt1*10)) % (10000*self.salt2) )

	def _request_authorization(self, device):
		authorized = False
		match self.config["method"]:
			case "none":
				authorized = False

			case "all":
				authorized =  True

			case "pass":
				authorized = device.request_passcode() == self.config["passcode"]

			case "temp":
				authorized = device.request_passcode() == self.get_temp_passcode()

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