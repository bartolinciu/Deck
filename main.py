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

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from Deck.DeckDevice import DeckDevice
from Deck.DeckController import DeckController
from Gui.Layout import LayoutsPage
from Gui.Device import DevicesPage
from Gui.Macros import MacrosPage
from Gui.Settings import SettingsPage
from Gui.Bindings import BindingsPage

import queue


class MainWindow(QMainWindow):
	def __init__( self, controller, *args, **kwargs ):
		super(MainWindow, self).__init__(*args, **kwargs)
		icon = QIcon("icon.ico")
		self.setWindowIcon(icon)
		self.setWindowTitle( "Deck" )
		self.controller = controller
		
		self.tabSelector = QTabBar()
		self.tabSelector.insertTab( 0, "Devices" )
		self.tabSelector.insertTab( 1, "Layouts" )
		self.tabSelector.insertTab( 2, "Macros" )
		self.tabSelector.insertTab( 3, "Bindings")
		self.tabSelector.insertTab( 4, "Settings")


		self.devicesWidget = DevicesPage()
		self.devicesWidget.controller = controller

		layoutsWidget = LayoutsPage()
		macrosWidget = MacrosPage()
		self.settingsWidget = SettingsPage( controller.get_network_configuration() )
		tabLayout = QStackedLayout()
		bindingsWidget = BindingsPage()

		self.settingsWidget.network_settings_changed.connect(self.network_settings_changed)

		tabLayout.addWidget( self.devicesWidget )
		tabLayout.addWidget( layoutsWidget )
		tabLayout.addWidget( macrosWidget )
		tabLayout.addWidget( bindingsWidget )
		tabLayout.addWidget( self.settingsWidget )

		
		tabWidget = QWidget()
		tabWidget.setLayout(tabLayout)

		self.tabSelector.currentChanged.connect( tabLayout.setCurrentIndex )

		mainLayout = QVBoxLayout()

		mainLayout.addWidget(self.tabSelector)
		mainLayout.addWidget(tabWidget)

		widget = QWidget()
		widget.setLayout(mainLayout)

		self.setCentralWidget( widget )


	def network_settings_changed(self):

		settings = self.settingsWidget.get_network_settings()

		self.controller.set_network_configuration( settings )

	def show( self, page = None ):
		if page != None:
			self.tabSelector.setCurrentIndex( page )
		QMainWindow.show( self )


if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setQuitOnLastWindowClosed(False)


	controller = DeckController()
	window = MainWindow(controller)

	icon = QIcon("icon.ico")

	tray = QSystemTrayIcon()
	tray.setIcon(icon)
	tray.setVisible(True)

	tray.activated.connect(lambda reason: window.show() if reason != QSystemTrayIcon.ActivationReason.Context else None  )

	menu = QMenu()
	option1 = QAction("Open Deck")
	option1.triggered.connect( lambda: window.show() )
	option2 = QAction("Devices")
	option2.triggered.connect( lambda: window.show(0) )
	option3 = QAction("Layouts")
	option3.triggered.connect( lambda: window.show(1) )
	option4 = QAction("Macros")
	option4.triggered.connect(lambda:window.show(2))
	option5 = QAction("Bindings")
	option5.triggered.connect(lambda:window.show(3))
	option6 = QAction("Settings")
	option6.triggered.connect(lambda:window.show(4))
	menu.addAction( option1 )
	menu.addSeparator()
	menu.addAction( option2 )
	menu.addAction( option3 )
	menu.addAction( option4 )
	menu.addAction( option5 )
	menu.addAction( option6 )
	menu.addSeparator()

	quit = QAction("Exit Deck")
	quit.triggered.connect(app.quit)
	menu.addAction(quit)
	tray.setContextMenu(menu)

	controller.device_delegate = window.devicesWidget

	controller_thread = threading.Thread( target = controller.run )
	controller_thread.start()

	
	window.show()

	app.exec()

	controller.stop()

	
	

	#controller = DeckController()
	#controller.run()
