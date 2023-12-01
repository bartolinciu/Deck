import os
import json
	
import shutil

class LayoutManager:
	suffix = ".json"
	prefix = "layouts/"

	empty_layout = {
		"1":{ "name": "" },
		"2":{ "name": "" },
		"3":{ "name": "" },
		"4":{ "name": "" },
		"5":{ "name": "" },
		"6":{ "name": "" },
		"7":{ "name": "" },
		"8":{ "name": "" },
		"9":{ "name": "" },
		"10":{ "name": "" },
		"11":{ "name": "" },
		"12":{ "name": "" },
		"13":{ "name": "" },
		"14":{ "name": "" },
		"15":{ "name": "" },
		"16":{ "name": "" }
	}

	def __init__(self):
		self.loaded_layouts = {}
		self.update_listeners = []
		self.rename_listeners = []

	def update_images( self, old_image, new_image ):
		for layout_name in self.layouts:
			if layout_name in self.loaded_layouts:
				if layout_name in self.loaded_layouts:

					layout = self.get_layout(layout_name)
					changed = False
					for i,button in layout.items():
						if "image" in button and button["image"] == old_image:
							button["image"] = new_image
							changed = True

				
				if changed:
					self.update_layout( layout_name, layout, visual_change = True )
			else:
				with open( LayoutManager.prefix+layout_name+LayoutManager.suffix ) as f:
					data = f.read()
					layout = json.loads(data)
					changed = False
					for i,button in layout.items():
						if "image" in button and button["image"] == old_image:
							button["image"] = new_image
							changed = True
					
					if changed:
						self.update_layout( layout_name, layout, skip_cache = True, visual_change = True )

	def update_parameters( self, new_parameter, filter = lambda layout_name, layout, button, index: True ):
		print("Update parameters")
		for layout_name in self.layouts:
			print(layout_name)
			if layout_name in self.loaded_layouts:
				layout = self.get_layout(layout_name)
				changed = False
				for button_id,button in layout.items():
					if "parameters" in button:
						for i,parameter in enumerate(button["parameters"]):
							if filter( layout_name, layout, button, i ):
								changed = True
								layout[button_id]["parameters"][i] = new_parameter

				
				if changed:
					self.update_layout( layout_name, layout )
			else:
				with open( LayoutManager.prefix+layout_name+LayoutManager.suffix ) as f:
					data = f.read()
					layout = json.loads(data)
					changed = False
					for button_id,button in layout.items():
						if "parameters" in button:
							for i,parameter in enumerate(button["parameters"]):
								if filter( layout_name, layout, button, i ):
									changed = True
									layout[button_id]["parameters"][i] = new_parameter
					
					if changed:
						self.update_layout( layout_name, layout, skip_cache = True )

	def import_layout(self, layout_path):
		if not os.path.isfile(layout_path):
			print("Couldn't find file")
			return False

		file, ext = os.path.splitext(layout_path)
		if not ext == self.suffix:
			print("incorrect extension")
			return False

		name = os.path.basename(file)

		if name in self.layouts:
			print("layout already exists")
			return False

		self.layouts.append(name)
		shutil.copyfile( layout_path, os.path.join( self.prefix, os.path.basename(layout_path) ) )
		return True


	def rename_layout( self, old_name, new_name ):
		if not old_name in self.layouts:
			return

		if old_name == new_name:
			return

		if old_name in self.loaded_layouts:
			self.loaded_layouts[new_name] = self.loaded_layouts.pop(old_name)

		self.layouts.remove(old_name)
		self.layouts.append(new_name)

		os.rename( self.prefix + old_name + self.suffix, self.prefix + new_name + self.suffix )

		for listener in self.rename_listeners:
			listener[1].on_rename(old_name, new_name)


	def get_layout(self, id):
		if not id in self.layouts:
			return None
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

	def add_rename_listener( self, listener, priority ):
		print("adding rename listener", listener, priority)
		self.rename_listeners.append( (priority, listener) )
		self.rename_listeners.sort( key = lambda x: x[0] )

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

	def duplicate_layout(self, name):
		if not name in self.layouts:
			return None

		copy_name = name + " - copy"
		i = 2

		while copy_name in self.layouts:
			copy_name = name + " - copy ({})".format(i)
			i+=1

		layout = self.get_layout(name)

		self.update_layout(copy_name, layout)
		self.layouts.append(copy_name)

		return copy_name

	def new_layout( self ):
		name = "New layout"
		i = 2

		while name in self.layouts:
			name = "New layout ({})".format( i )
			i+=1

		self.update_layout( name, self.empty_layout )
		self.layouts.append(name)
		return name

	def export_layout( self, layout_name, path ):
		if not layout_name in self.layouts:
			return False

		shutil.copyfile( self.prefix + layout_name + self.suffix, path )

	def update_layout( self, layout_name, layout, visual_change = True, skip_cache = False ):
		if not skip_cache:
			self.loaded_layouts[layout_name] = layout

		path = LayoutManager.prefix+layout_name+LayoutManager.suffix

		if layout == None:
			os.unlink(path)
			self.layouts.remove(layout_name)
			if layout_name in self.loaded_layouts:
				self.loaded_layouts.pop(layout_name)

		else:
			with open( path, "wt" ) as f:
				data = json.dumps(layout, indent="\t")
				f.write(data)

		for listener in self.update_listeners:
			listener[1].on_layout_update(layout_name, visual_change)

layout_manager = LayoutManager()
layout_manager.load_layouts()