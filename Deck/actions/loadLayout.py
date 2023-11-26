from Deck.LayoutManager import layout_manager as LayoutManager
from Deck.DeckController import DeckController

class RenameListener:
	def on_rename(old_name, new_name):
		print("on_rename")
		LayoutManager.update_parameters( new_name, lambda layout_name, layout, button, index: button["action"] == "loadLayout" and index == 0 and button["parameters"][0] == "old_name" )
		DeckController.actions["loadLayout"].parameters[0]["values"] = LayoutManager.get_layout_list()

LayoutManager.add_rename_listener( RenameListener, 2 )

@DeckController.action(label = "Load layout", parameters = [ {"label": "Layout", "type":"List", "values": LayoutManager.get_layout_list()} ]  )
async def loadLayout( device, layout_name ):
	layout = LayoutManager.get_layout(layout_name)
	if not layout:
		layout = LayoutManager.empty_layout
	await device.set_layout_async(layout_name, layout)
	print("loading layout:", layout_name)
