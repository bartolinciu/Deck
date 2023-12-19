from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from Gui.Layout import LayoutsPage
from Gui.Device import DevicesPage
from Gui.Macros import MacrosPage
from Gui.Settings import SettingsPage
from Gui.Bindings import BindingsPage



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

	def get_tab_names(self):
		tab_names = []
		for i in range( self.tabSelector.count() ):
			tab_names.append( self.tabSelector.tabText(i) )
		return tab_names

	def network_settings_changed(self):

		settings = self.settingsWidget.get_network_settings()

		self.controller.set_network_configuration( settings )

	def show( self, page = None ):
		if page != None:
			self.tabSelector.setCurrentIndex( page )
		QMainWindow.show( self )
