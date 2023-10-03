import asyncio
from Deck.DeckController import DeckController

@DeckController.action( label = "Test", parameter_type="Boolean", parameter_label = "Parameter", parameter_values= [] )
async def test(device, parameter):
	print(parameter)