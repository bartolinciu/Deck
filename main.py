#!/usr/bin/env python3

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from Deck.DeckController import DeckController
from Gui.MainWindow import MainWindow

import sys
import threading
import os

if __name__ == "__main__":
	app = QApplication(sys.argv)
	app.setQuitOnLastWindowClosed(False)


	controller = DeckController()
	window = MainWindow(controller)

	icon = QIcon( os.path.join(os.path.dirname(__file__), "icon.ico"))

	tray = QSystemTrayIcon()
	tray.setIcon(icon)
	tray.setVisible(True)

	tray.activated.connect(lambda reason: window.show() if reason != QSystemTrayIcon.ActivationReason.Context else None  )

	menu = QMenu()
	option1 = QAction("Open Deck")
	option1.triggered.connect( lambda: window.show() )

	menu.addAction( option1 )
	menu.addSeparator()
	options = []
	for i, tab in enumerate(window.get_tab_names()):
		option = QAction(tab)
		option.triggered.connect( lambda checked, page=i: window.show(page) )
		options.append(option)
		menu.addAction(option)

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

