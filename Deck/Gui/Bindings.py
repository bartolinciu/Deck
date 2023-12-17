from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from Deck.BindingManager import manager as BindingManager
from Deck.LayoutManager import layout_manager as LayoutManager
from Deck.DeviceManager import device_manager as DeviceManager

import re

class WindowTitleValidator(QValidator):
	def __init__(self, default, *args, **kwargs):
		super(WindowTitleValidator, self).__init__(*args, **kwargs)
		self.default = default

	def set_default(self, default):
		self.default = default

	def fixup(self, value):
		return self.default

	def validate(self, value, pos):
		result = QValidator.State.Acceptable
		if value != "*":
			try:
				re.compile( value )
			except re.error:
				result = QValidator.State.Intermediate
		return (result, value, pos)


class BindingTreeItem( QTreeWidgetItem ):
	def __init__( self, binding, *args, **kwargs ):
		super( BindingTreeItem, self ).__init__( type = QTreeWidgetItem.ItemType.UserType+1, *args, **kwargs)
		self.application = QLineEdit()
		self.title = QLineEdit()
		self.device = QComboBox()
		self.layout = QComboBox()

		self.device.addItem( "Choose device", "" )
		self.device.addItem( "Any device", "*" )

		for uuid, device in DeviceManager.get_device_configs().items():
			self.device.addItem( device.get_name(), uuid )
		
		for layout in LayoutManager.get_layout_list():
			self.layout.addItem(layout)

		self.application.setText( binding["app"] )
		self.title.setText( binding["title"] )
		self.device.setCurrentIndex( self.device.findData( binding["device"] ) )
		self.layout.setCurrentIndex( self.layout.findText( binding["layout"] ) )


		self.validator = WindowTitleValidator( binding["title"] )
		self.title.setValidator( self.validator )

		self.application.editingFinished.connect(self.parameter_changed)
		self.title.editingFinished.connect(self.title_changed)
		self.device.currentIndexChanged.connect(self.parameter_changed)
		self.layout.currentIndexChanged.connect(self.parameter_changed)

	def title_changed(self):
		self.validator.set_default( self.title.text() )
		self.title.clearFocus()
		self.parameter_changed()

	def get_binding(self):
		binding = {
			"app": self.application.text(),
			"title": self.title.text(),
			"device": self.device.currentData(),
			"layout": self.layout.currentText()
			}

		return binding 

	def parameter_changed(self):
		self.emitDataChanged()

	def set_widgets(self):
		self.treeWidget().setItemWidget( self, 1, self.application )
		self.treeWidget().setItemWidget( self, 2, self.title )
		self.treeWidget().setItemWidget( self, 3, self.device )
		self.treeWidget().setItemWidget( self, 4, self.layout )



class BindingTreeWidget( QTreeWidget ):
	def __init__( self, *args, **kwargs ):
		super( BindingTreeWidget, self ).__init__( *args, **kwargs )
		self.setColumnCount(5)
		self.setHeaderLabels( ["No","App", "Window Title", "Device", "Layout" ] )

	def refresh(self):
		self.clear()
		for binding in BindingManager.get_bindings():
			binding_item = BindingTreeItem( binding )
			self.addTopLevelItem( binding_item )


	def showEvent(self, event):
		self.refresh()

	def addTopLevelItem( self, item ):
		item.setText(0, str(self.topLevelItemCount()+1))
		QTreeWidget.addTopLevelItem( self, item )
		item.set_widgets()

class BindingsPage(QWidget):
	def __init__(self, *args, **kwargs):
		super( BindingsPage, self ).__init__(*args, **kwargs)
		self.setLayout( QVBoxLayout() )

		self.tree = BindingTreeWidget()
		self.tree.itemChanged.connect(self.binding_changed)

		frame = QFrame()
		frame.setFrameShape( QFrame.Shape.StyledPanel )

		self.add_binding_button = QPushButton("\u271a")
		self.add_binding_button.clicked.connect( self.add_binding )
		self.delete_binding_button = QPushButton( "\u274c" )
		self.delete_binding_button.clicked.connect( self.delete_binding )

		self.move_binding_up_button = QPushButton("\u2191")
		self.move_binding_up_button.clicked.connect(self.move_binding_up)
		self.move_binding_down_button = QPushButton("\u2193")
		self.move_binding_down_button.clicked.connect(self.move_binding_down)

		layout = QHBoxLayout()
		layout.addWidget( self.add_binding_button )
		layout.addWidget( self.delete_binding_button )
		layout.addWidget( self.move_binding_up_button )
		layout.addWidget( self.move_binding_down_button )

		frame.setLayout(layout)

		self.layout().addWidget(frame)
		self.layout().addWidget( self.tree )


	def add_binding(self):
		binding = {"app": "", "title":"", "device":"", "layout":""}
		BindingManager.add_binding(binding)
		self.tree.refresh()
		self.tree.setCurrentItem( self.tree.topLevelItem( self.tree.topLevelItemCount()-1 ) )

	def delete_binding(self):
		index = self.tree.indexOfTopLevelItem( self.tree.currentItem() )
		BindingManager.pop_binding( self.tree.indexOfTopLevelItem( self.tree.currentItem() ) )
		self.tree.refresh()
		if index > 0:
			self.tree.setCurrentItem( self.tree.topLevelItem(index-1) )
		else:
			self.tree.setCurrentItem( self.tree.topLevelItem(index) )

	def move_binding_up(self):
		index = self.tree.indexOfTopLevelItem( self.tree.currentItem() )
		BindingManager.move_binding( index, index-1 )
		self.tree.refresh()
		if index > 0:
			self.tree.setCurrentItem( self.tree.topLevelItem(index-1) )
		else:
			self.tree.setCurrentItem( self.tree.topLevelItem(index) )

	def move_binding_down(self):
		index = self.tree.indexOfTopLevelItem( self.tree.currentItem() )
		BindingManager.move_binding( index, index+1 )
		self.tree.refresh()
		if index+1 < self.tree.topLevelItemCount():
			self.tree.setCurrentItem( self.tree.topLevelItem(index+1) )
		else:
			self.tree.setCurrentItem( self.tree.topLevelItem(index) )

	def binding_changed(self, item, col):
		BindingManager.update_binding( self.tree.indexOfTopLevelItem(item), item.get_binding() )