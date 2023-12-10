from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from Deck.LayoutManager import layout_manager as LayoutManager
from Deck.DeviceManager import device_manager as DeviceManager
from Deck.BindingManager import manager as BindingManager

class DevicePropertiesWidget(QFrame):
	properties_changed = pyqtSignal( object )
	disconnect = pyqtSignal()
	forget = pyqtSignal()
	merge = pyqtSignal(str)
	def __init__(self, *args, **kwargs):
		super( DevicePropertiesWidget, self ).__init__(*args, **kwargs)
		self.set_by_code = False
			
		self.setFrameShape(QFrame.StyledPanel)
		self.properties = None
		layout = QGridLayout()
		layout.addWidget( QLabel("Name"), 0, 0 )
		self.name = QLineEdit()
		self.name.editingFinished.connect( self.name_changed )
		layout.addWidget(self.name, 0, 1, 1, 2)

		layout.addWidget( QLabel("Layout"), 1, 0, 1, 2 )
		self.layout_selector = QComboBox()
		self.list_layouts()
		self.layout_selector.currentIndexChanged.connect(self.layout_changed)
		layout.addWidget(self.layout_selector, 1, 1, 1, 2)

		self.disconnect_button = QPushButton("Disconnect")
		self.disconnect_button.clicked.connect( lambda: self.disconnect.emit() )
		self.forget_button = QPushButton("Forget")
		self.forget_button.clicked.connect(lambda:self.forget.emit())

		self.merge_button = QPushButton("Merge")
		self.merge_button.clicked.connect(lambda:self.merge.emit(self.target_device_selector.currentData()))

		layout.addWidget( QLabel("Merge with"), 2,0  )
		self.target_device_selector = QComboBox()


		layout.addWidget(self.target_device_selector, 2, 1)

		layout.addWidget( self.merge_button, 2, 2, 1, 1 )
		layout.addWidget( self.disconnect_button, 3, 0, 1, 3 )
		layout.addWidget( self.forget_button, 4, 0, 1, 3 )
		self.setLayout(layout)

	def list_mergable_devices(self):
		self.target_device_selector.clear()
		for _,config in DeviceManager.get_device_configs().items():
			if config.get_uuid() != self.properties.get_uuid() and config.get_uuid() != "0000000000000000":
				self.target_device_selector.addItem( config.get_name(), config.get_uuid() )


	def set_properties(self, properties):
		self.properties = properties
		self.layout_selector.setCurrentIndex( self.layout_selector.findText(properties.get_layout()) )
		self.name.setText( properties.get_name() )
		self.list_mergable_devices()

	def layout_changed(self, index):
		if self.set_by_code:
			return

		if self.properties != None:
			self.properties.set_layout( self.layout_selector.currentText() )
			self.properties_changed.emit( self.properties )

	def list_layouts(self):
		set_by_code = self.set_by_code
		self.set_by_code = True
		self.layout_selector.clear()
		for layout in LayoutManager.get_layout_list():
			self.layout_selector.addItem(layout)

		self.set_by_code = set_by_code

	def name_changed(self):
		if self.properties == None:
			return

		self.properties.set_name( self.name.text() )
		self.name.clearFocus()
		self.properties_changed.emit(self.properties)


class ScrollableButtonSelector(QScrollArea):
	button_selected = pyqtSignal( int )
	def __init__(self, *args, **kwargs):
		super(ScrollableButtonSelector, self).__init__(*args, **kwargs)
		self.layout = QVBoxLayout()
		self.content = QWidget()
		self.content.setLayout( self.layout )
		self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.setVerticalScrollBarPolicy( Qt.ScrollBarAsNeeded )
		self.setWidgetResizable( True )
		self.setWidget( self.content )

		self.current_button = -1
		self.button_count = 0
		

	def set_button_text( self, i, text ):
		self.layout.itemAt(i).widget().setText(text)


	def add_button(self, text):
		button = QPushButton(text)
		button.setCheckable(True)
		button.pressed.connect( lambda i = self.button_count: self.button_pressed(i) )
		self.button_count += 1
		self.layout.addWidget(button)

	def button_pressed(self, i):
		if self.current_button >= 0:
			self.layout.itemAt( self.current_button ).widget().setChecked(False)
		self.current_button = i
 
		self.button_selected.emit(i)

	def remove_item( self, i ):
		self.button_count -= 1
		self.layout.itemAt(i).widget().deleteLater()
		if i == self.current_button:
			self.current_button = -1

	def clear(self):
		for i in range( self.layout.count() ):
			self.layout.itemAt( i ).widget().deleteLater()

	def select_button(self, i):
		if i == -1 and self.current_button != -1:
			self.layout.itemAt(self.current_button).widget().setChecked(False)
			self.current_button = -1


		if i < 0 or i >= self.button_count:
			return

		self.current_button = i
		self.layout.itemAt(i).widget().setChecked(True)

class DevicesPage(QWidget):
	def __init__(self, *args, **kwargs):
		super(DevicesPage, self).__init__(*args, **kwargs)
		self.setLayout( QHBoxLayout() )
		self.device_list_widget = ScrollableButtonSelector()
		self.device_list_widget.button_selected.connect(self.device_selected)
		self.properties_panel = DevicePropertiesWidget()
		self.properties_panel.properties_changed.connect(self.device_properties_changed)

		self.properties_panel.disconnect.connect(self.disconnect_device)
		self.properties_panel.forget.connect(self.forget_device)
		self.properties_panel.merge.connect(self.merge_device)

		self.layout().addWidget(self.device_list_widget)
		self.layout().addWidget(self.properties_panel)
		self.current_device = -1


	def merge_device(self, target_uuid):
		if self.current_device != -1:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)
			name = DeviceManager.get_config(target_uuid).get_name()
			msg.setText("Are you sure you want to merge this device with " + name + "?")
			msg.setInformativeText("This device will be identified as " + name + ".\nAll bindings connected to this device will be reassigned to new device\nThis operation is irreversible")
			msg.setWindowTitle("Merge?")
			msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

			retval = msg.exec_()

			if not retval == QMessageBox.Ok:
				return

			device = self.devices[self.current_device]

			BindingManager.reassign_bindings( device.get_uuid(), target_uuid )
			device.merge(target_uuid)

	def device_properties_changed(self, properties):
		if self.current_device != -1:
			self.devices[self.current_device].set_name(properties.get_name())
			self.devices[self.current_device].set_layout( properties.get_layout(), LayoutManager.get_layout(properties.get_layout()) )
			self.device_list_widget.set_button_text( self.current_device, properties.get_name() )

	def disconnect_device(self):
		if self.current_device != -1:
			self.devices[self.current_device].disconnect()

	def forget_device(self):
		if self.current_device != -1:
			msg = QMessageBox()
			msg.setIcon(QMessageBox.Information)

			msg.setText("Are you sure you want to forget this device?")
			msg.setInformativeText("This operation is irreversible")
			msg.setWindowTitle("Forget?")
			msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

			retval = msg.exec_()

			if not retval == QMessageBox.Ok:
				return

			
			self.devices[self.current_device].forget()
			self.devices[self.current_device].disconnect()

	def device_selected(self, i):
		self.current_device = i
		self.properties_panel.set_properties( self.devices[i].get_configuration() )

	def event(self, event):
		if event.type() == QEvent.User + 1:
			self.list_devices()
				
				
			return True
		return QWidget.event(self,event)

	def list_devices(self):
		if self.controller:
			current_device = None
			if self.current_device != -1:
				current_device = self.devices[self.current_device]
			self.devices = self.controller.srv.devices[:]
			self.devices.sort( key = lambda x: x.get_name() )

			for i, device in enumerate(self.devices):
				if i < self.device_list_widget.button_count:
					self.device_list_widget.set_button_text(i, device.get_name())
				else:
					self.device_list_widget.add_button(device.get_name())

			for i in range( len(self.devices), self.device_list_widget.button_count):
				self.device_list_widget.remove_item(i)

			if current_device in self.devices:
				self.current_device = self.devices.index(current_device)
			else:
				self.current_device = -1

			self.device_list_widget.select_button(self.current_device)
			

	def refresh(self):
		QCoreApplication.postEvent(self, QEvent(QEvent.User + 1) )

