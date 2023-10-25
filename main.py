#!/usr/bin/env python3
import http.server, ssl
import asyncio
import websockets
import threading
import json
import time
import os
import sys
import ifaddr
import re

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Deck.DeckDevice import DeckDevice
from Deck.DeckController import DeckController
from Deck.Gui.Layout import LayoutsPage
from Deck.Gui.Device import DevicesPage
from Deck.Gui.Macros import MacrosPage
from Deck.Gui.Settings import SettingsPage

import queue
#import win32gui, win32process, psutil


class MainWindow(QMainWindow):
	def __init__( self, controller, *args, **kwargs ):
		super(MainWindow, self).__init__(*args, **kwargs)
		icon = QIcon("icon.ico")
		self.setWindowIcon(icon)
		self.setWindowTitle( "Deck" )
		self.controller = controller
		
		tabSelector = QTabBar()
		tabSelector.insertTab( 0, "Devices" )
		tabSelector.insertTab( 1, "Layouts" )
		tabSelector.insertTab( 2, "Macros" )
		tabSelector.insertTab( 3, "Settings")


		self.devicesWidget = DevicesPage()
		self.devicesWidget.controller = controller

		layoutsWidget = LayoutsPage()
		macrosWidget = MacrosPage()
		self.settingsWidget = SettingsPage( controller.get_network_configuration() )
		tabLayout = QStackedLayout()

		self.settingsWidget.network_settings_changed.connect(self.network_settings_changed)

		tabLayout.addWidget( self.devicesWidget )
		tabLayout.addWidget( layoutsWidget )
		tabLayout.addWidget( macrosWidget )
		tabLayout.addWidget( self.settingsWidget )

		
		tabWidget = QWidget()
		tabWidget.setLayout(tabLayout)

		tabSelector.currentChanged.connect( tabLayout.setCurrentIndex )

		mainLayout = QVBoxLayout()

		mainLayout.addWidget(tabSelector)
		mainLayout.addWidget(tabWidget)

		widget = QWidget()
		widget.setLayout(mainLayout)

		self.setCentralWidget( widget )


	def network_settings_changed(self):

		settings = self.settingsWidget.get_network_settings()

		self.controller.set_network_configuration( settings )



if __name__ == "__main__":
	app = QApplication(sys.argv)
	controller = DeckController()
	window = MainWindow(controller)

	controller.device_delegate = window.devicesWidget

	controller_thread = threading.Thread( target = controller.run )
	controller_thread.start()

	
	window.show()

	app.exec_()

	controller.stop()

	
	

	#controller = DeckController()
	#controller.run()
