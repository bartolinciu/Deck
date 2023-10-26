from Deck import LayoutManager
from Deck.DeckController import DeckController

@DeckController.action(label = "Load layout", parameters = [ {"label": "Layout", "type":"List", "values": LayoutManager.layout_manager.get_layout_list()} ]  )
async def loadLayout( device, layout_name ):
	layout = LayoutManager.layout_manager.get_layout(layout_name)
	await device.set_layout_async(layout_name, layout)
	print("loading layout:", layout_name)
