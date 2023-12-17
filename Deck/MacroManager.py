import json
import pynput
import time
import Deck
import os


keyboard = pynput.keyboard.Controller()
mouse = pynput.mouse.Controller()

keymapping = {}

button_mapping = {}

for i in pynput.keyboard.Key:
	keymapping[i.name] = i

for button in pynput.mouse.Button:
	button_mapping[ button.name ] = button


class MacroManager:
	macro_file_name = "macros.json"
	macro_file_path = os.path.join( Deck.config_path, macro_file_name )
	def __init__(self):
		with open( self.macro_file_path ) as f:
			data = f.read()
			self.macros = json.loads(data)

	def get_macro(self, name):
		return self.macros[name]

	def get_macro_list(self):
		return self.macros.keys()

	def set_macro(self, name, macro):
		if macro != None:
			self.macros[name] = macro
		else:
			self.macros.pop(name)
		with open( self.macro_file_path, "wt" ) as f:
			data = json.dumps( self.macros, indent = "\t" )
			f.write( data )



	def execute_macro(self, name):
		macro = self.macros[name]
		for step in macro:
			print(step)
			time.sleep( step["delay"] )

			if step["device"] == "keyboard":
				key = step["key"]
				if len(key) > 1:
					if key.startswith("num_"):
						if key == "num_,":
							key = pynput.keyboard.KeyCode.from_vk(110)
						else:
							key = pynput.keyboard.KeyCode.from_vk( int(key[4:]) )
					elif key.startswith("vk_"):
						key = pynput.keyboard.KeyCode.from_vk( int(key[3:]) )
					else:
						key = keymapping[key]
				if step["action"] == "press":
					keyboard.press(key)
				else:
					keyboard.release(key)

			elif step["device"] == "mouse":
				match step["action"]:
					case "press":
						mouse.press( button_mapping[ step["button"] ] )

					case "release":
						mouse.release( button_mapping[ step["button"] ] )

					case "click":
						mouse.click( button_mapping[ step["button"] ], step["count"] )

					case "scroll":
						mouse.scroll( step["x"], step["y"] )

					case "position":
						mouse.position = ( step["x"], step["y"] )

					case "move":
						mouse.move( step["x"], step["y"] )



				


manager = MacroManager()