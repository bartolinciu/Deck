import Deck

import argparse
import os

parser = argparse.ArgumentParser( prog = "Deck", description = "Standalone deck controller" )
parser.add_argument("-b", "--base", help = "Base directory for files with no specified location")
parser.add_argument('-w', '--web', help="Location of web interface")
parser.add_argument("-c", "--config", help="Location of configuration files")
parser.add_argument("-l", "--layouts", help = "Location of layout description files")
parser.add_argument("-d", "--devices", help = "Location of device configuration files")

args = parser.parse_args()

if args.base != None:
	Deck.base_path = args.base
	Deck.config_path = os.path.join(Deck.base_path, "config")
	Deck.devices_path = os.path.join(Deck.base_path, "devices")
	Deck.layouts_path = os.path.join(Deck.base_path, "layouts")
	Deck.web_path = os.path.join(Deck.base_path, "web")




if args.config != None:
	Deck.config_path = args.config

if args.devices != None:
	Deck.device_path = args.devices

if args.layouts != None:
	Deck.layout_path = args.layouts

if args.web != None:
	Deck.web_path = args.web

from Deck.DeckController import DeckController

if __name__=="__main__":
		controller = DeckController()
		controller.run()