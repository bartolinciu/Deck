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
			f.write( json.dumps( self.bindings ), indent = "\t" )

	def get_bindings( self ):
		return self.bindings

	def get_bindings_by_window(self, app, title):
		app_bindings = [ binding for binding in self.bindings if binding["app"] == app ]
		return [ binding for binding in app_bindings if binding["title"] == "*" or re.matcher(binding["title"]).match(title) ]


	def add_binding( self, binding ):
		self.bindings.append(binding)

	def pop_binding( self, i ):
		binding  = self.bindings[i]
		self.bindings = self.bindings[:i] + self.bindings[i+1:]
		return binding

	def move_binding(self, old_index, new_index):
		self.bindings.insert(new_index, self.pop_binding(old_index))

manager = BindingManager()