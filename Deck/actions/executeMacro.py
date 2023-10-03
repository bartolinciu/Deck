import asyncio
from Deck.DeckController import DeckController
import json
from pynput.keyboard import Key, Controller as KeyboardController

keyboard = KeyboardController()

macros = {}

keymapping = {}

for i in Key:
	keymapping[i.name] = i

def loadMacros( file ):
	global macros
	with open(file) as f:
		data = f.read()
		macros = json.loads(data)

loadMacros("macros.json")

@DeckController.action( label = "Execute macro", parameter_type="List", parameter_label = "Macro", parameter_values= macros.keys() )
async def executeMacro( device, macro_name ):
	macro = macros[macro_name]
	for step in macro:
		print(step)
		if step["action"] in ["press", "release"]:
			key = step["key"]
			if len(key) > 1:
				key = keymapping[key]
			if step["action"] == "press":
				keyboard.press(key)
			else:
				keyboard.release(key)
		elif step["action"] == "delay":
			time.sleep( step["time"] )