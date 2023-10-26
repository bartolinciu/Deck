import asyncio
from Deck.DeckController import DeckController

@DeckController.action( label = "Test", parameters = [{"label": "Parameter", "type":"Boolean"}])
async def test(device, parameters):
	print(parameter)