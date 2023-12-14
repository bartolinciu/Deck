from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import ifaddr

import re
import threading

from Deck.AuthorizationManager import manager as AuthorizationManager

matcher = re.compile( "\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}" )

class CheckBox(QCheckBox):
	def __init__( self, *args, **kwargs ):
		super( CheckBox, self ).__init__(*args, **kwargs)
		self.state_map = {
			Qt.Checked:Qt.Unchecked,
			Qt.Unchecked:Qt.Checked,
			Qt.PartiallyChecked:Qt.Unchecked
			}
	def set_on_state(self, on_state):
		self.state_map[Qt.Unchecked] = on_state

	def nextCheckState(self):
		self.setCheckState( self.state_map[self.checkState()] )

class IPTreeItem( QTreeWidgetItem ):
	def __init__( self, IP, *args, **kwargs ):
		super( IPTreeItem, self ).__init__( [IP], type = QTreeWidgetItem.UserType+1, *args, **kwargs)
		self.checkbox = QCheckBox()

class InterfaceTreeItem( QTreeWidgetItem ):

	def __init__( self, interface, *args, **kwargs ):
		matching_ips = [ ip for ip in interface.ips if bool( matcher.match( str( ip.ip) ) ) ]
		self.name = matching_ips[0].nice_name if len(matching_ips) > 0 else interface.nice_name
		super( InterfaceTreeItem, self ).__init__( [ self.name ],type = QTreeWidgetItem.UserType+1, *args, **kwargs)
		self.checkbox = CheckBox()
		self.checkbox.setTristate(True)
		self.checkbox.stateChanged.connect( self.interface_status_changed )
		self.addChild( IPTreeItem("Any IP") )
		self.child(0).checkbox.stateChanged.connect( self.any_ip_status_changed )
		self.ips = []
		for ip in matching_ips:
			ip_str = str(ip.ip)
			self.ips.append(ip_str)
			item = IPTreeItem( ip_str )
			item.checkbox.stateChanged.connect( self.ip_status_changed )
			self.addChild( item )

	def interface_status_changed(self, state):
		if state == Qt.Checked:
			children_checked = False
			for i in range( self.childCount() ):
				if self.child(i).checkbox.isChecked():
					children_checked = True
					break
			if not children_checked:
				self.child(0).checkbox.setCheckState(Qt.Checked)

	def any_ip_status_changed( self, state ):
		if state == Qt.Checked:
			if self.checkbox.checkState() != Qt.Unchecked:
				self.checkbox.setCheckState( Qt.Checked )
			self.checkbox.set_on_state( Qt.Checked )
			for i in range(1, self.childCount()):
				self.child(i).checkbox.setCheckState( Qt.Unchecked )


	def ip_status_changed( self, state ):
		if state == Qt.Checked:
			if self.checkbox.checkState() != Qt.Unchecked:
				self.checkbox.setCheckState( Qt.PartiallyChecked )
			self.checkbox.set_on_state( Qt.PartiallyChecked )
			self.child(0).checkbox.setCheckState( Qt.Unchecked )
		else:
			checked = False
			for i in range( self.childCount()):
				if self.child(i).checkbox.isChecked():
					checked = True
					break

			if not checked:
				self.child(0).checkbox.setCheckState( Qt.Checked )


	def set_widgets(self):
		for i in range( self.childCount() ):
			child = self.child(i)
			self.treeWidget().setItemWidget( child, 1, child.checkbox )
		self.treeWidget().setItemWidget( self, 1, self.checkbox )

	def get_ips(self):
		ips = {}
		for i in range(1, self.childCount()):
			ips[self.ips[i-1]] = self.child(i).checkbox.isChecked()
		return ips

	def get_configuration(self):
		interface = { 
				"name" : self.name,
				"isActive":self.checkbox.checkState() in [Qt.Checked, Qt.PartiallyChecked],
				"useAnyIp": self.child(0).checkbox.isChecked(),
				"ips": self.get_ips()
				}
		return interface

	def configure(self, configuration):
		if configuration["isActive"]:
			if configuration["useAnyIp"]:
				self.checkbox.setCheckState( Qt.Checked )
			elif len(configuration["ips"]) > 0:
				self.checkbox.setCheckState(Qt.PartiallyChecked)

		if configuration["useAnyIp"]:
			self.child(0).checkbox.setCheckState(Qt.Checked)

		for ip in configuration["ips"]:
			if ip in self.ips:
				self.child( self.ips.index(ip) + 1 ).checkbox.setChecked( configuration["ips"][ip] )
			else:
				item = IPTreeItem( ip )
				item.checkbox.setChecked( configuration["ips"][ip] )
				item.checkbox.stateChanged.connect( self.ip_status_changed )
				self.addChild(item)
				self.ips.append(ip)

		self.set_widgets()

class InterfacesTreeWidget( QTreeWidget ):
	def __init__( self, *args, **kwargs ):
		super( InterfacesTreeWidget, self ).__init__( *args, **kwargs )
		self.setColumnCount(2)
		self.setHeaderLabels( ["", "Active"] )


	def get_interfaces(self):
		interfaces = []
		for i in range( self.topLevelItemCount() ):
			item = self.topLevelItem(i)
			
			interfaces.append( item.get_configuration() )
		return interfaces

	def configure(self, configuration):
		for interface in configuration:
			interface_found = False
			for i in range( self.topLevelItemCount() ):
				if self.topLevelItem(i).name == interface["name"]:
					interface_found = True
					self.topLevelItem(i).configure( interface )

			if not interface_found:
				fake_interface = ifaddr.Adapter( interface["name"], interface["name"], [] )
				item = InterfaceTreeItem( fake_interface )
				self.addTopLevelItem( item )
				item.configure(interface)

	def addTopLevelItem( self, item ):
		QTreeWidget.addTopLevelItem( self, item )
		item.set_widgets()

class PasscodeValidator(QValidator):
	def __init__(self, default, *args, **kwargs):
		super(PasscodeValidator, self).__init__(*args, **kwargs)
		self.default = default

	def set_default(self, default):
		self.default = default

	def fixup(self, value):
		return self.default

	def validate(self, value, pos):
		result = QValidator.Intermediate
		if len(value) == 4 and value.isdigit():
			result = QValidator.Acceptable
		return (result, value, pos)



class AuthorizationPanel( QFrame ):
	def __init__(self, *args, **kwargs):
		super( AuthorizationPanel, self ).__init__(*args, **kwargs)
		self.setFrameShape(QFrame.StyledPanel)
		self.setLayout(QHBoxLayout())
		self.method_selector = QComboBox()
		self.method_selector.addItem("Block all devices", "none")
		self.method_selector.addItem("Allow all devices", "all")
		self.method_selector.addItem("Temporary access code", "temp")
		self.method_selector.addItem("Passcode", "pass")
		self.method_selector.addItem("Ask for permission", "delegate")
		self.layout().addWidget(self.method_selector)
		parameters_layout = QStackedLayout()		

		parameters_layout.addWidget( QWidget() ) #no parameters when blocking all devices
		parameters_layout.addWidget( QWidget() ) #no parameters when accepting all devices

		self.passcode_display = QLabel( AuthorizationManager.get_temp_passcode() )
		self.passcode_display.setStyleSheet("QLabel{ background-color:black; font-size:30px; } QLabel:hover{background-color:transparent;}")
		self.passcode_display.setMaximumWidth( self.width()//2 )
		widget = QWidget()
		widget.setLayout(QHBoxLayout())
		widget.layout().addWidget( self.passcode_display )
		parameters_layout.addWidget(widget)

		widget = QWidget()
		widget.setLayout(QHBoxLayout())
		self.passcode_validator = PasscodeValidator(AuthorizationManager.get_passcode())

		self.passcode_edit = QLineEdit(AuthorizationManager.get_passcode())
		self.passcode_edit.setValidator(self.passcode_validator)
		self.passcode_edit.setEchoMode(QLineEdit.Password)
		self.passcode_edit.editingFinished.connect( self.passcode_changed )
		self.passcode_visibility_checkbox = QCheckBox("Show characters")
		self.passcode_visibility_checkbox.stateChanged.connect(lambda state: self.passcode_edit.setEchoMode({Qt.Unchecked:QLineEdit.Password, Qt.Checked:QLineEdit.Normal}[state]))
		widget.layout().addWidget(self.passcode_edit)
		widget.layout().addWidget(self.passcode_visibility_checkbox)
		parameters_layout.addWidget(widget)

		parameters_layout.addWidget(QWidget())
		self.layout().addLayout(parameters_layout)

		self.method_selector.currentIndexChanged.connect(parameters_layout.setCurrentIndex)
		self.method_selector.setCurrentIndex( self.method_selector.findData( AuthorizationManager.get_method() ) )
		self.method_selector.currentIndexChanged.connect(self.method_selected)

		self.timer = QTimer(self);
		self.timer.timeout.connect(self.set_temp_passcode)
		self.timer.start(1000);

		self.cv = threading.Condition()

		self.authorization = False

		AuthorizationManager.set_delegate(self)



	def passcode_changed(self):
		AuthorizationManager.set_passcode( self.passcode_edit.text() )
		self.passcode_validator.set_default(self.passcode_edit.text())
		self.passcode_edit.clearFocus()

	def method_selected(self, index):
		AuthorizationManager.set_method( self.method_selector.currentData() )

	def set_temp_passcode(self):
		self.passcode_display.setText(AuthorizationManager.get_temp_passcode())

	def event( self, event ):
		if event.type() == QEvent.User + 2:
			self._request_authorization( event.device )
				
			return True
		return QWidget.event(self,event)

	def request_authorization(self, device):
		self.authorization = False
		event = QEvent(QEvent.User + 2)
		event.device = device
		QCoreApplication.postEvent(self, event )
		with self.cv:
			self.cv.wait()

		return self.authorization


	def _request_authorization(self, device):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Question)

		msg.setText("Unknown device is trying to connect from " + device.websockets[0].remote_address[0] + ". Allow?")
		msg.setWindowTitle("New device")
		msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

		retval = msg.exec_()

		self.authorization = retval == QMessageBox.Yes
		with self.cv:
			self.cv.notify()



class SettingsPage(QWidget):
	network_settings_changed = pyqtSignal()
	authorization_password_changed = pyqtSignal()
	def __init__(self, config = None, *args, **kwargs):
		super(SettingsPage, self).__init__(*args, **kwargs)
		layout = QVBoxLayout()
		layout.addWidget(AuthorizationPanel())
		self.tree = InterfacesTreeWidget()

		self.config = config
		self.list_interfaces()

		controlls = QHBoxLayout()
		refresh_button = QPushButton("Refresh")
		refresh_button.clicked.connect( self.list_interfaces )
		apply_button = QPushButton("Apply")
		apply_button.clicked.connect(self.apply)

		controlls.addWidget(refresh_button)
		controlls.addWidget(apply_button)
		

		layout.addWidget(self.tree)
		layout.addLayout(controlls)
		self.setLayout(layout)

	def apply(self):
		self.config = self.tree.get_interfaces()
		self.network_settings_changed.emit()

	def get_network_settings(self):
		return self.config

	def list_interfaces(self):

		self.tree.clear()
		
		interfaces = ifaddr.get_adapters()
		for interface in interfaces:
			interfaceItem = InterfaceTreeItem( interface )
			self.tree.addTopLevelItem( interfaceItem )

		if self.config:
			self.tree.configure( self.config )