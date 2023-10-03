from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Deck.LayoutManager import layout_manager

class DevicePropertiesWidget(QWidget):
	def __init__(self, *args, **kwargs):
		super(DevicePropertiesWidget, self).__init__(*args, **kwargs)
		layout = QVBoxLayout()
		self.name = QLineEdit() 
		self.disconnect = QPushButton("Disconnect")
		self.forget = QPushButton("Forget")
		self.device = None
		self.name.returnPressed.connect( self.setDeviceName )
		self.disconnect.pressed.connect( self.disconnectDevice )
		self.forget.pressed.connect( self.forgetDevice )

		layoutLayout = QHBoxLayout()
		label = QLabel("Active layout:")
		self.combo = QComboBox()
		for layout_name in layout_manager.get_layout_list():
			self.combo.addItem(layout_name)
		self.combo.setCurrentIndex(-1)
		self.combo.currentTextChanged.connect(self.selectLayout)
		layoutLayout.addWidget(label)
		layoutLayout.addWidget(self.combo)

		layout.addWidget( self.name )
		layout.addLayout(layoutLayout)
		layout.addWidget( self.disconnect )
		layout.addWidget( self.forget )
		self.setLayout(layout)

	def selectLayout(self, text):
		if self.device and text:
			layout = layout_manager.get_layout(text)
			self.device.set_layout(text, layout)

	def disconnectDevice(self):
		print("disconnectDevice")
		self.button.deleteLater()
		if not self.device == None:
			self.device.disconnect()
			self.device = None

	def forgetDevice(self):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Information)

		msg.setText("Are you sure you want to forget this device?")
		msg.setInformativeText("This operation is irreversible")
		msg.setWindowTitle("Forget?")
		msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

		retval = msg.exec_()

		if not retval == QMessageBox.Ok:
			return

		if self.device:
			self.device.forget()
		self.disconnectDevice()
		

	def setDeviceName(self):
		if not self.device == None:
			self.device.set_name( self.name.text() )
			self.button.setText(self.name.text())
			self.parent().refresh()

	def setDevice(self, device):
		self.device = device
		self.combo.setCurrentIndex( self.combo.findText( device.get_layout_id() ) )
		self.name.setText(device.get_name())

	def setActiveButton( self, button ):
		print("setting active button")
		self.button = button



class DevicesPage(QWidget):
	def __init__(self, *args, **kwargs):
		super(DevicesPage, self).__init__(*args, **kwargs)
		topLayout = QHBoxLayout()
		self.deviceListLayout = QVBoxLayout()
		self.deviceListPanel = QWidget()
		self.deviceListPanel.setLayout(self.deviceListLayout)

		self.propertiesPanel = DevicePropertiesWidget()

		topLayout.addWidget(self.deviceListPanel)
		topLayout.addWidget(self.propertiesPanel)
		self.setLayout(topLayout)

	def addDevice(self, device):
		button = QPushButton( device.get_name() )
		button.pressed.connect( lambda: self.propertiesPanel.setDevice(device) )
		button.pressed.connect( lambda: self.propertiesPanel.setActiveButton(button) )
		

		self.deviceListLayout.addWidget(button)

	def event(self, event):
		if event.type() == QEvent.User + 1:
			if self.controller:
				layout = QVBoxLayout()
				tmpWidget = QWidget()
				tmpWidget.setLayout( self.deviceListLayout )
				devices = self.controller.srv.devices[:]
				devices.sort( key = lambda x: x.get_name() )
				self.deviceListLayout = layout
				for device in devices:
					self.addDevice(device)
				self.deviceListPanel.setLayout(layout)
				
			return True
		return QWidget.event(self,event)


	def refresh(self):
		QCoreApplication.postEvent(self, QEvent(QEvent.User + 1) )

