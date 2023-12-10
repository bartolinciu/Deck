import os
import re
import json


class BindingManager:
	binding_file_name = "binding.json"
	binding_file_path = os.path.join( os.path.dirname(__file__) , binding_file_name )
	def __init__(self, path = None):
		if not os.path.isfile(self.binding_file_path):
			self.bindings = []
			self.save()
		else:
			with open( self.binding_file_path, "rt" ) as f:
				self.bindings = json.loads( f.read() )

	def save(self):
		with open(self.binding_file_path, "wt") as f:
			f.write( json.dumps( self.bindings , indent = "\t" ))

	def reassign_bindings(self, uuid, target_uuid):
		for binding in self.bindings:
			if binding["device"] == uuid:
				binding["device"] = target_uuid

		self.save()

	def get_bindings( self ):
		return self.bindings

	def get_bindings_by_window(self, app, title):
		app_bindings = [ binding for binding in self.bindings if binding["app"] == app ]
		return [ binding for binding in app_bindings if binding["title"] == "*" or re.matcher(binding["title"]).match(title) ]

	def update_binding(self, i, binding):
		self.bindings[i] = binding
		self.save()

	def add_binding( self, binding ):
		self.bindings.append(binding)
		self.save()

	def pop_binding( self, i ):
		binding  = self.bindings[i]
		self.bindings = self.bindings[:i] + self.bindings[i+1:]
		self.save()
		return binding

	def move_binding(self, old_index, new_index):
		if old_index < 0 or old_index >= len(self.bindings) or new_index < 0 or new_index >= len(self.bindings):
			return
		binding = self.pop_binding(old_index)
		self.bindings.insert(new_index, binding)
		self.save()

manager = BindingManager()