import asyncio
from Deck.DeckController import DeckController

from Deck.MacroManager import manager


@DeckController.action( label = "Execute macro", parameter_type="List", parameter_label = "Macro", parameter_values= manager.get_macro_list() )
async def executeMacro( device, macro_name ):
	manager.execute_macro(macro_name)
