import os
import json
	
class LayoutManager:
	suffix = ".json"
	prefix = "layouts/"

	def __init__(self):
		self.loaded_layouts = {}
		self.update_listeners = []

	def update_parameters( self, new_parameter, filter = lambda layout_name, layout, button: True ):
		for layout_name in self.layouts:
			if layout_name in self.loaded_layouts:
				layout = self.get_layout(layout_name)
				changed = False
				for button in layout:
					try:
						if filter( layout_name, layout, layout[button] ):
							changed = True
							layout[button]["parameter"] = new_parameter
					except KeyError:
						pass
				
				if changed:
					self.update_layout( layout_name, layout )
			else:
				with open( LayoutManager.prefix+layout_name+LayoutManager.suffix ) as f:
					data = f.read()
					layout = json.loads(data)
					changed = False
					for button in layout:
						try:
							if filter( layout_name, layout, layout[button] ):
								changed = True
								layout[button]["parameter"] = new_parameter
						except KeyError:
							pass
					
					if changed:
						self.update_layout( layout_name, layout, skip_cache = True )



	def get_layout(self, id):
		if id in self.loaded_layouts:
			return self.loaded_layouts[id]
		with open( LayoutManager.prefix+id+LayoutManager.suffix ) as f:
			data = f.read()
			data = json.loads(data)
			self.loaded_layouts[id] = data
			return data

	def add_layout_update_listener( self, listener, priority ):
		self.update_listeners.append( (priority, listener) )
		self.update_listeners.sort( key = lambda x: x[0] )

	def load_layouts(self):
		self.layouts = []
		
		for root, dirs, files in os.walk( LayoutManager.prefix ):
			for file in files:
				if( file.endswith( LayoutManager.suffix ) ):
					name = file[ :-len(LayoutManager.suffix) ]

					self.layouts.append(name)
		print("Found layouts:")
		print( "\n".join(self.layouts) )

	def get_layout_list(self):
		return self.layouts

	def update_layout( self, layout_name, layout, visual_change = True, skip_cache = False ):
		if not skip_cache:
			self.loaded_layouts[layout_name] = layout

		with open( LayoutManager.prefix+layout_name+LayoutManager.suffix, "wt" ) as f:
			data = json.dumps(layout, indent="\t")
			f.write(data)

		for listener in self.update_listeners:
			listener[1].on_layout_update(layout_name, visual_change)

layout_manager = LayoutManager()
layout_manager.load_layouts()