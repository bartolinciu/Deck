from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import ifaddr

import re
import threading
import qrcode

from PIL.ImageQt import ImageQt

from Deck.AuthorizationManager import manager as AuthorizationManager

matcher = re.compile( "\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}" )

class CheckBox(QCheckBox):
	def __init__( self, *args, **kwargs ):
		super( CheckBox, self ).__init__(*args, **kwargs)
		self.state_map = {
			Qt.CheckState.Checked:Qt.CheckState.Unchecked,
			Qt.CheckState.Unchecked:Qt.CheckState.Checked,
			Qt.CheckState.PartiallyChecked:Qt.CheckState.Unchecked
			}
	def set_on_state(self, on_state):
		self.state_map[Qt.CheckState.Unchecked] = on_state

	def nextCheckState(self):
		self.setCheckState( self.state_map[self.checkState()] )

class ConnectDialog( QDialog ):
	def __init__( self, ip, *args, **kwargs ):
		super(ConnectDialog, self).__init__(*args, **kwargs)
		self.setWindowTitle( "Connect" )
		self.setLayout(QVBoxLayout())
		url_layout = QHBoxLayout()
		url_layout.addWidget(QLabel("Url: "))
		self.QRCode = QLabel()
		self.authorization_checkbox = QCheckBox("Include authorization")
		self.authorization_checkbox.stateChanged.connect(self.authorization_changed)
		self.link = QLabel()
		url_layout.addWidget(self.link)
		self.layout().addWidget(self.QRCode)
		self.layout().addLayout(url_layout)
		self.layout().addWidget(self.authorization_checkbox)
		self.ip = ip
		
		self.include_authorization = False

		self.timer = QTimer(self);
		self.timer.timeout.connect(self.set_url)
		self.timer.start(1000);

		self.set_url()


	def authorization_changed(self, status):
		self.include_authorization = status==Qt.CheckState.Checked.value
		self.set_url()

	def set_url(self):
		url = "http://" + self.ip + ":8080"
		if self.include_authorization:
			authorization = "#"
			match AuthorizationManager.get_method():
				case "pass":
					authorization += AuthorizationManager.get_passcode()

				case "temp":
					authorization += AuthorizationManager.get_temp_passcode()

			url += authorization

		self.QRCode.setPixmap( QPixmap.fromImage(ImageQt(qrcode.make(url)) ))
		self.link.setText(url)


class IPTreeItem( QTreeWidgetItem ):
	def __init__( self, IP, is_connected, *args, **kwargs ):
		super( IPTreeItem, self ).__init__( [IP], type = QTreeWidgetItem.ItemType.UserType+1, *args, **kwargs)
		self.ip = IP
		self.checkbox = QCheckBox()
		self.connect_button = QPushButton("Connect")

		self.connect_button.clicked.connect(self.show_dialog)
		self.is_connected = is_connected

	def show_dialog(self):
		connect_dialog = ConnectDialog(self.ip)
		connect_dialog.exec()

class InterfaceTreeItem( QTreeWidgetItem ):

	def __init__( self, interface, *args, **kwargs ):
		matching_ips = [ ip for ip in interface.ips if bool( matcher.match( str( ip.ip) ) ) ]
		self.name = matching_ips[0].nice_name if len(matching_ips) > 0 else interface.nice_name
		super( InterfaceTreeItem, self ).__init__( [ self.name ],type = QTreeWidgetItem.ItemType.UserType+1, *args, **kwargs)
		self.checkbox = CheckBox()
		self.checkbox.setTristate(True)
		self.checkbox.stateChanged.connect( self.interface_status_changed )
		self.addChild( IPTreeItem("Any IP", False ) )
		self.child(0).checkbox.stateChanged.connect( self.any_ip_status_changed )
		self.ips = []
		first_interface = True
		for ip in matching_ips:
			ip_str = str(ip.ip)
			self.ips.append(ip_str)
			if first_interface:
				self.child(0).ip = ip_str
				self.child(0).is_connected = True
				first_interface = False
			item = IPTreeItem( ip_str, True )
			item.checkbox.stateChanged.connect( self.ip_status_changed )
			self.addChild( item )

	def interface_status_changed(self, state):
		if state == Qt.CheckState.Checked.value:
			children_checked = False
			for i in range( self.childCount() ):
				if self.child(i).checkbox.isChecked():
					children_checked = True
					break
			if not children_checked:
				self.child(0).checkbox.setCheckState(Qt.CheckState.Checked)

	def any_ip_status_changed( self, state ):
		if state == Qt.CheckState.Checked.value:
			if self.checkbox.checkState() != Qt.CheckState.Unchecked:
				self.checkbox.setCheckState( Qt.CheckState.Checked )
			self.checkbox.set_on_state( Qt.CheckState.Checked )
			for i in range(1, self.childCount()):
				self.child(i).checkbox.setCheckState( Qt.CheckState.Unchecked )


	def ip_status_changed( self, state ):
		if state == Qt.CheckState.Checked.value:
			if self.checkbox.checkState() != Qt.CheckState.Unchecked:
				self.checkbox.setCheckState( Qt.CheckState.PartiallyChecked )
			self.checkbox.set_on_state( Qt.CheckState.PartiallyChecked )
			self.child(0).checkbox.setCheckState( Qt.CheckState.Unchecked )
		else:
			checked = False
			for i in range( self.childCount()):
				if self.child(i).checkbox.isChecked():
					checked = True
					break

			if not checked:
				self.child(0).checkbox.setCheckState( Qt.CheckState.Checked )


	def set_widgets(self):
		for i in range( self.childCount() ):
			child = self.child(i)
			self.treeWidget().setItemWidget( child, 1, child.checkbox )
			if child.is_connected:
				self.treeWidget().setItemWidget( child, 2, child.connect_button )
		self.treeWidget().setItemWidget( self, 1, self.checkbox )

	def get_ips(self):
		ips = {}
		for i in range(1, self.childCount()):
			ips[self.ips[i-1]] = self.child(i).checkbox.isChecked()
		return ips

	def get_configuration(self):
		interface = { 
				"name" : self.name,
				"isActive":self.checkbox.checkState() in [Qt.CheckState.Checked, Qt.CheckState.PartiallyChecked],
				"useAnyIp": self.child(0).checkbox.isChecked(),
				"ips": self.get_ips()
				}
		return interface

	def configure(self, configuration):
		if configuration["isActive"]:
			if configuration["useAnyIp"]:
				self.checkbox.setCheckState( Qt.CheckState.Checked )
			elif len(configuration["ips"]) > 0:
				self.checkbox.setCheckState(Qt.CheckState.PartiallyChecked)

		if configuration["useAnyIp"]:
			self.child(0).checkbox.setCheckState(Qt.CheckState.Checked)

		for ip in configuration["ips"]:
			if ip in self.ips:
				self.child( self.ips.index(ip) + 1 ).checkbox.setChecked( configuration["ips"][ip] )
			else:
				item = IPTreeItem( ip, False )
				item.checkbox.setChecked( configuration["ips"][ip] )
				item.checkbox.stateChanged.connect( self.ip_status_changed )
				self.addChild(item)
				self.ips.append(ip)

		self.set_widgets()

class InterfacesTreeWidget( QTreeWidget ):
	def __init__( self, *args, **kwargs ):
		super( InterfacesTreeWidget, self ).__init__( *args, **kwargs )
		self.setColumnCount(3)
		self.setHeaderLabels( ["", "Active", "Connect"] )


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
		result = QValidator.State.Intermediate
		if len(value) == 6 and value.isdigit():
			result = QValidator.State.Acceptable
		return (result, value, pos)



class AuthorizationPanel( QFrame ):
	def __init__(self, *args, **kwargs):
		super( AuthorizationPanel, self ).__init__(*args, **kwargs)
		self.setFrameShape(QFrame.Shape.StyledPanel)
		self.setLayout(QHBoxLayout())
		self.layout().addWidget(QLabel("New device Authorization method:"))
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
		self.passcode_display.setAlignment(Qt.AlignmentFlag.AlignHCenter)
		widget = QWidget()
		widget.setLayout(QHBoxLayout())
		widget.layout().addWidget( self.passcode_display )
		parameters_layout.addWidget(widget)

		widget = QWidget()
		widget.setLayout(QHBoxLayout())
		self.passcode_validator = PasscodeValidator(AuthorizationManager.get_passcode())

		self.passcode_edit = QLineEdit(AuthorizationManager.get_passcode())
		self.passcode_edit.setValidator(self.passcode_validator)
		self.passcode_edit.setEchoMode(QLineEdit.EchoMode.Password)
		self.passcode_edit.editingFinished.connect( self.passcode_changed )
		
		self.passcode_visibility_checkbox = QCheckBox("Show characters")
		self.passcode_visibility_checkbox.stateChanged.connect(lambda state: self.passcode_edit.setEchoMode({Qt.CheckState.Unchecked.value:QLineEdit.EchoMode.Password, Qt.CheckState.Checked.value:QLineEdit.EchoMode.Normal}[state]))
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
		if event.type() == QEvent.Type.User + 2:
			self._request_authorization( event.device )
				
			return True
		return QWidget.event(self,event)

	def request_authorization(self, device):
		self.authorization = False
		event = QEvent(QEvent.Type.User + 2)
		event.device = device
		QCoreApplication.postEvent(self, event )
		with self.cv:
			self.cv.wait()

		return self.authorization


	def _request_authorization(self, device):
		msg = QMessageBox()
		msg.setIcon(QMessageBox.Icon.Question)

		msg.setText("Unknown device is trying to connect from " + device.websockets[0].remote_address[0] + ". Allow?")
		msg.setWindowTitle("New device")
		msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

		retval = msg.exec()

		self.authorization = retval == QMessageBox.StandardButton.Yes
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