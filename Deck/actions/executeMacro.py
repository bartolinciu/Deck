import asyncio
from Deck.DeckController import DeckController

from Deck.MacroManager import manager
import threading

@DeckController.action( label = "Execute macro", parameter_type="List", parameter_label = "Macro", parameter_values= manager.get_macro_list() )
async def executeMacro( device, macro_name ):
	thread = threading.Thread( target = manager.execute_macro, daemon = True, args = [macro_name])
	thread.start()