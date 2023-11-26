from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Deck.LayoutManager import layout_manager
from Deck.DeckController import DeckController
from Deck.ImageManager import manager as ImageManager

import sys 

import traceback

def print_stack_trace():
	print("**********************************************")
	print("stack trace:")
	for line in traceback.format_stack():
		print(line.strip())
	print("**********************************************")

import os



class ActionParametersWidget( QFrame ):
	parameters_changed = pyqtSignal( list )
	def __init__( self, parameters_description, *args, **kwargs ):
		super( ActionParametersWidget, self ).__init__( *args, **kwargs )
		self.setFrameShape( QFrame.StyledPanel )
		grid = QGridLayout()
		self.setLayout( grid )
		self.parameters_description = {}
		self.parameters = []
		self.setting_parameters = False

		self.build( parameters_description )

	def build(self, parameters_description):
		self.building = True
		for child in self.children()[1:]:
			child.deleteLater()
			self.layout().removeWidget( child )

		self.parameters_description = parameters_description
		self.parameters = [None] * len(parameters_description)
		for i, parameter in enumerate( parameters_description ):
			label = QLabel( parameter["label"] )
			parameter_widget = None
			match parameter["type"]:
				case "List":
					parameter_widget = QComboBox()
					for value in parameter["values"]:
						parameter_widget.addItem( value )
					parameter_widget.currentIndexChanged.connect( lambda index, i = i: self.parameter_changed(i) )
					

				case "Boolean":
					parameter_widget = QCheckBox()
					parameter_widget.stateChanged.connect( lambda state, i = i: self.parameter_changed(i) )

				case "Text":
					parameter_widget = QLineEdit()
					parameter_widget.editingFinished.connect( lambda i = i: self.parameter_changed(i) )
			self.layout().addWidget( label, i, 0 )
			self.layout().addWidget( parameter_widget, i, 1 )
			self.parameter_changed(i)

		self.building = False

	def set_parameters( self, parameters ):
		self.setting_parameters = True
		self.parameters = parameters
		for i, parameter in enumerate(parameters):
			if i >= self.layout().rowCount():
				break
			widget = self.layout().itemAtPosition( i, 1 ).widget()

			match self.parameters_description[i]["type"]:
				case "List":

					if isinstance( parameter, str ):
						widget.setCurrentText( parameter )
						

				case "Boolean":
					if isinstance( parameter, bool ):
						widget.setChecked( parameter )

				case "Text":
					if isinstance( parameter, str ):
						widget.setText(parameter)

		self.setting_parameters = False

	def parameter_changed(self, i):
		widget = self.layout().itemAtPosition( i, 1 ).widget()
		parameter = None
		match self.parameters_description[i]["type"]:
			case "List":
				parameter = widget.currentText()

		if self.setting_parameters:
			return
		
		
		match self.parameters_description[i]["type"]:
			case "List":
				parameter = widget.currentText()

			case "Boolean":
				parameter = widget.isChecked()

			case "Text":
				parameter = widget.text()

		self.parameters[i] = parameter
		if not self.building:
			self.parameters_changed.emit( self.parameters )

	def reset(self):
		self.setting_parameters = True
		for i, parameter in enumerate(self.parameters_description):
			widget = self.layout().itemAtPosition( i, 1 ).widget()
			match parameter["type"]:
				case "List":
					widget.setCurrentIndex(0)
					self.parameters[i] = widget.currentText()

				case "Boolean":
					widget.setChecked(False)
					self.parameters[i] = False

				case "Text":
					widget.setText("")
					self.parameters[i] = ""
		self.setting_parameters = False


class ImagePropertiesDialog( QDialog ):
	def __init__( self, *args, blacklist = [], definition = None, **kwargs ):
		super( ImagePropertiesDialog, self ).__init__(*args, **kwargs)
		self.path_touched = False
		self.setWhatsThis("Image selection dialog window")
		self.blacklist = blacklist
		self.old_name = None
		self.setWindowTitle( "Image" )
		vertical_layout = QVBoxLayout()
		self.notification = QLabel()
		vertical_layout.addWidget(self.notification)
		grid_layout = QGridLayout()

		grid_layout.addWidget( QLabel("Name"), 0, 0 )
		grid_layout.addWidget( QLabel("Path"), 1, 0 )
		grid_layout.addWidget( QLabel("Import method"), 2, 0 )

		self.name = QLineEdit()
		self.name.textEdited.connect(self.name_edited)
		self.path = QLineEdit()
		self.path.editingFinished.connect(lambda: self.__setattr__("path_touched", True))

		grid_layout.addWidget( self.name, 0, 1 )

		path_layout = QHBoxLayout()

		browse_button = QPushButton("Browse...")
		browse_button.clicked.connect( self.select_image_file )
		path_layout.addWidget(self.path)
		path_layout.addWidget( browse_button )

		grid_layout.addLayout( path_layout, 1, 1 )

		button_layout = QHBoxLayout()
		button_save = QPushButton("Save")
		button_save.clicked.connect( self.save )
		button_cancel = QPushButton("Cancel")
		button_cancel.clicked.connect( lambda: self.done( QDialog.Rejected ) )
		button_layout.addWidget( button_save )
		button_layout.addWidget( button_cancel )

		method_layout = QHBoxLayout()
		self.method_link = QRadioButton( "Link" )
		method_copy = QRadioButton( "Copy" )
		method_copy.setChecked(True)
		if not ImageManager.symlinks_allowed():
			self.method_link.setDisabled(True)

		self.button_group = QButtonGroup()
		self.button_group.addButton( self.method_link )
		self.button_group.addButton( method_copy )

		method_layout.addWidget(method_copy)
		method_layout.addWidget(self.method_link)

		grid_layout.addLayout( method_layout, 2, 1 )

		vertical_layout.addLayout( grid_layout )
		vertical_layout.addLayout( button_layout )

		if definition:
			self.name.setText( definition["name"] )
			self.path.setText( definition["path"] )
			self.old_name = definition["name"]
			if definition["isLink"]:
				self.method_link.setChecked( True )

		self.setLayout( vertical_layout )

	def save(self):
		if self.name.text() == "":
			self.notification.setText( "Image must have a name" )
		elif self.name.text() != self.old_name and self.name.text() in self.blacklist:
			self.notification.setText( "Image with this name already exists" )
		elif not os.path.isfile( self.path.text() ) and not self.method_link.isChecked():
			self.notification.setText( "Image doesn't exist" )
		elif self.path.text() == "" and self.method_link.isChecked():
			self.notification.setText("Link path cannot be empty")
		else:
			self.done( QDialog.Accepted )

	def name_edited(self, text):
		if text != self.old_name and text in self.blacklist:
			self.notification.setText( "Image with this name already exists" )
		else:
			self.notification.setText("")

	def select_image_file(self):
		self.pathTouched = True
		supportedFormats = QImageReader.supportedImageFormats()
		text_filter = "Images ({})".format(" ".join(["*.{}".format(fo.data().decode()) for fo in supportedFormats]))
		file = QFileDialog.getOpenFileName( parent = self, caption = "Select image", filter = text_filter )
		self.path.setText(os.path.abspath(file[0]))

	def get_definition(self):
		definition = {
					  "name":self.name.text(),
					  "path":self.path.text(),
					  "isLink":self.method_link.isChecked(),
					  "pathTouched": self.path_touched
				}
		return definition

class ImageManagementDialog( QDialog ):
	def __init__( self, *args, **kwargs ):
		super(ImageManagementDialog, self).__init__(*args, **kwargs)
		self.selected_image = None
		self.setWindowTitle( "Manage images" )
		vertical_layout = QVBoxLayout()
		buttons_layout = QHBoxLayout()
		button_import = QPushButton("Import")
		button_import.clicked.connect( self.import_image )
		button_edit = QPushButton("Edit")
		button_edit.clicked.connect(self.edit_image)
		button_delete = QPushButton("Delete")
		button_delete.clicked.connect(self.delete_image)

		buttons_layout.addWidget( button_import )
		buttons_layout.addWidget( button_edit )
		buttons_layout.addWidget( button_delete )
		self.list_widget = QListWidget()
		self.list_widget.addItems( list(ImageManager.get_images()) )
		vertical_layout.addWidget(self.list_widget)
		vertical_layout.addLayout( buttons_layout )
		self.setLayout(vertical_layout)

	def import_image(self):
		properties_dialog = ImagePropertiesDialog( self )
		result = properties_dialog.exec()
		if result == QDialog.Accepted:
			definition = properties_dialog.get_definition()
			self.list_widget.addItem(definition["name"])
			ImageManager.import_image( definition )			
			


	def edit_image(self):
		if not self.list_widget.currentItem():
			return

		current_image = self.list_widget.currentItem().text()

		definition = ImageManager.get_image_definition( current_image )

		properties_dialog = ImagePropertiesDialog( self, definition = definition, blacklist = list( ImageManager.get_images() ) )
		result = properties_dialog.exec()

		if result == QDialog.Accepted:
			definition = properties_dialog.get_definition()
			if current_image != definition["name"]:
				self.list_widget.currentItem().setText( definition["name"] )
			ImageManager.update_image( current_image, definition )
			
		

	def delete_image(self):
		if not self.list_widget.currentItem():
			return

		current_image = self.list_widget.currentItem().text()
		ImageManager.delete_image( current_image )
		self.list_widget.takeItem( self.list_widget.currentRow() )

class ButtonPropertiesPanel(QWidget):
	parameters_changed = pyqtSignal( dict )
	appearance_changed = pyqtSignal( dict )
	def __init__( self, *args, **kwargs ):
		super( ButtonPropertiesPanel, self ).__init__(*args, **kwargs)
		self.button = None
		self.set_by_code = False
		self.setLayout( QVBoxLayout() )
		frame = QFrame()
		frame.setFrameShape(QFrame.StyledPanel)
		grid = QGridLayout()
		frame.setLayout(grid)
		self.layout().addWidget( frame )

		grid.addWidget( QLabel("Text"), 0, 0 )
		grid.addWidget( QLabel("Image"), 1, 0 )

		
		self.image_selector = QComboBox()
		self.image_selector.currentTextChanged.connect( self.image_changed )

		self.list_images()

		manage_images_button = QPushButton("Manage")
		manage_images_button.pressed.connect( self.manage_images )

		image_layout = QHBoxLayout()
		image_layout.addWidget( self.image_selector )
		image_layout.addWidget( manage_images_button )

		grid.addLayout( image_layout, 1, 1 )

		
		self.name_box = QLineEdit()
		self.name_box.editingFinished.connect( self.change_name )
		grid.addWidget( self.name_box, 0, 1 )

		grid.addWidget( QLabel("Action"), 2, 0)
		self.action_box = QComboBox()
		grid.addWidget( self.action_box, 2, 1 )

		self.parameter_stack = QStackedLayout()

		self.build_parameters()

		self.action_box.currentIndexChanged.connect( self.action_selected )

		self.layout().addLayout( self.parameter_stack )

		
	def list_images(self):
		self.set_by_code = True
		self.image_selector.clear()
		self.image_selector.addItem("Choose image")

		for image in ImageManager.get_images():
			self.image_selector.addItem( image )

		if self.button and "image" in self.button:
			self.image_selector.setCurrentText( self.button["image"] )

		self.set_by_code = False

	def manage_images(self):
		manage_dialog = ImageManagementDialog(self)
		manage_dialog.exec()

		self.list_images()

	def image_changed( self ):
		if not self.button:
			return

		if self.set_by_code:
			return

		if self.image_selector.currentIndex() > 0:
			self.button["image"] = self.image_selector.currentText()
		else:
			self.button["image"] = None

		self.appearance_changed.emit(self.button)



	def _parameters_changed( self, parameters ):
		self.button["parameters"] = parameters
		if not self.set_by_code:
			self.parameters_changed.emit( self.button )

	def build_parameters(self):
		self.set_by_code = True
		self.action_box.clear()
		for i, (action_name, action) in enumerate(DeckController.actions.items()):
			self.action_box.addItem( action.label, action_name )
			if i < self.parameter_stack.count():
				self.parameter_stack.itemAt( i ).widget().build( action.parameters )
			else:
				widget = ActionParametersWidget( action.parameters )
				widget.parameters_changed.connect( self._parameters_changed )
				self.parameter_stack.addWidget( widget )
		self.set_by_code = False


	def set_button(self, button):
		self.set_by_code = True
		self.button = button
		self.name_box.setText(button["name"])
		if "action" in button:
			self.action_box.setCurrentIndex( self.action_box.findData( button["action"] ) )
			self.parameter_stack.currentWidget().set_parameters( button["parameters"] )
		else:
			self.action_box.setCurrentIndex(0)
		if "image" in button and self.image_selector.findText(button["image"]) != -1:
			self.image_selector.setCurrentText(button["image"])
		else:
			self.image_selector.setCurrentIndex(0)
		self.set_by_code = False

	def change_name(self):
		self.button["name"] = self.name_box.text()
		self.appearance_changed.emit(self.button)

	def showEvent(self, event):
		super(ButtonPropertiesPanel, self).showEvent(event)
		self.refresh()
		
	def refresh(self):
		self.build_parameters()
		if self.button != None:
			self.set_button(self.button)
		
	def action_selected(self, index):
		self.parameter_stack.setCurrentIndex(index)
		if not self.set_by_code:
			self.parameter_stack.currentWidget().reset()
			if self.button != None:
				self.button["action"] = self.action_box.currentData()
				self.parameters_changed.emit( self.button )



class LayoutWidget(QWidget):
	def __init__(self, *args, **kwargs):
		super( LayoutWidget, self ).__init__(*args, **kwargs)
		self.current_button = -1

		horizontal = QHBoxLayout()
		buttons = QGridLayout()
		
		self.button_parameters = ButtonPropertiesPanel()
		self.button_parameters.parameters_changed.connect( self.parameters_changed )
		self.button_parameters.appearance_changed.connect( self.button_appearance_changed )

		horizontal.addLayout(buttons)
		horizontal.addWidget(self.button_parameters)

		self.buttons = []

		self.skip_parameter_save = False

		for i in range(16):
			button = QToolButton()
			button.setCheckable(True)
			button.pressed.connect( lambda i = i: self.button_selected(i) )
			self.buttons.append(button)

			buttons.addWidget( button, i//4, i%4 )

		self.setLayout(horizontal)
		ImageManager.add_image_update_listener(self, 2)
		layout_manager.add_rename_listener( self, 2 )

	def on_rename(self, old_name, new_name):
		if self.layout_name == old_name:
			self.layout_name = new_name

	def refresh(self):
		self.button_parameters.refresh()
		if self.layout_name:
			self.set_layout(self.layout_name)

	def on_image_update(self, old_name, new_name):
		self.set_layout(self.layout_name)

	def parameters_changed(self, button):
		if self.current_button >= 0:
			self.layout[ str(self.current_button+1) ] = button
			layout_manager.update_layout(self.layout_name, self.layout, visual_change = False)

	def button_appearance_changed(self, button):
		if self.current_button >= 0:
			self.buttons[self.current_button].setText( button["name"] )
			self.layout[ str(self.current_button+1) ] = button
			layout_manager.update_layout(self.layout_name, self.layout, visual_change = True)

	def button_selected( self, i ):
		if self.current_button >= 0:
			self.buttons[self.current_button].setChecked(False)
		self.current_button = i
		self.edited_by_code = True
		self.button_parameters.set_button( self.layout[str(self.current_button + 1)] )
		
	def resizeEvent( self, event ):
		for button in self.buttons:
			button.setFixedSize( QSize(event.size().width() //10, int(event.size().height() * 0.18) ))

	def set_layout( self, layout_name ):
		if self.current_button >= 0:
			self.buttons[self.current_button].setChecked(False)
		self.current_button = -1
		self.layout = layout_manager.get_layout(layout_name)
		self.layout_name = layout_name
		for i in range(16):
			button = self.layout[str(i+1)]
			self.buttons[i].setText( button["name"] )
			icon = QIcon()
			self.buttons[i].setToolButtonStyle( Qt.ToolButtonTextOnly )
			if "image" in button and button["image"]!=None:
				definition = ImageManager.get_image_definition( button["image"] )
				if definition:
					pixmap = QPixmap( definition["hostingPath"] )
					pixmap = pixmap.scaled( QSize(45,40), Qt.KeepAspectRatio, Qt.SmoothTransformation )
					icon = QIcon(pixmap)
					self.buttons[i].setToolButtonStyle( Qt.ToolButtonTextUnderIcon )
				

			self.buttons[i].setIcon(icon)

	def change_button_name(self):
		if self.current_button >= 0:
			self.buttons[ self.current_button ].setText( self.name_box.text() )
			self.layout[str(self.current_button+1)]["name"] = self.name_box.text()
			layout_manager.update_layout(self.layout_name, self.layout)

class ToolButton( QToolButton ):
	def paintEvent(self, event):
		p = QStylePainter(self)
		opt = QStyleOptionToolButton()
		self.initStyleOption( opt )
		opt.features &= ( ~QStyleOptionToolButton.HasMenu )
		p.drawComplexControl( QStyle.CC_ToolButton, opt )

class LayoutValidator( QValidator ):
	def __init__(self, old_name, blacklist, *args, **kwargs):
		super( QValidator, self ).__init__( *args, **kwargs )
		self.old_name = old_name
		self.blacklist = blacklist

	def fixup(self, value):
		return self.old_name

	def validate(self, value, pos):
		if value != self.old_name and value in self.blacklist:
			return (QValidator.Intermediate, value, pos)
		else:
			return (QValidator.Acceptable, value, pos)



class LayoutsPage(QWidget):
	def __init__(self, *args, **kwargs):
		super(LayoutsPage, self).__init__(*args, **kwargs)
		self.layoutSelector = QComboBox()
		self.layoutWidget = LayoutWidget()
		top_layout = QHBoxLayout()
		layout_menu_button = ToolButton()
		self.option1 = QAction("New")
		self.option1.triggered.connect(self.new_layout)
		self.option2 = QAction("Import")
		self.option2.triggered.connect( self.import_layout )
		self.option3 = QAction("Rename")
		self.option3.triggered.connect(self.rename_layout)
		self.option4 = QAction("Duplicate")
		self.option4.triggered.connect(self.duplicate_layout)
		self.option5 = QAction("Export")
		self.option5.triggered.connect(self.export_layout)
		self.option6 = QAction("Delete")
		self.option6.triggered.connect(self.delete_layout)

		self.menu = QMenu()
		self.menu.addAction( self.option1 )
		self.menu.addAction(self.option2)
		self.menu.addSeparator()
		self.menu.addAction(self.option3)
		self.menu.addAction(self.option4)
		self.menu.addAction(self.option5)
		self.menu.addSeparator()
		self.menu.addAction(self.option6)

		layout_menu_button.setMenu(self.menu)
		#layout_menu_button.setArrowType( Qt.DownArrow )
		layout_menu_button.setText("\u2022\u2022\u2022")
		layout_menu_button.setPopupMode( QToolButton.InstantPopup )

		top_layout.addWidget( self.layoutSelector )
		top_layout.addWidget(layout_menu_button)

		self.list_layouts()

		self.layoutSelector.setInsertPolicy(QComboBox.InsertAtCurrent)		

		self.layoutSelector.currentIndexChanged.connect(self.select_layout)
		
		self.select_layout()

		vertical = QVBoxLayout()
		vertical.addLayout(top_layout)
		vertical.addWidget(self.layoutWidget)

		self.stashed_layout = None

		self.setLayout(vertical)

	def list_layouts(self):
		self.layoutSelector.blockSignals(True)
		self.layoutSelector.clear()
		for layout in layout_manager.get_layout_list():
			self.layoutSelector.addItem( layout )
		self.layoutSelector.blockSignals(False)

	def select_layout(self):
		layout = self.layoutSelector.currentText()
		self.layoutWidget.set_layout(layout)

	def new_layout(self):
		pass

	def import_layout(self):
		text_filter = "Layout files (*.json)"
		file = QFileDialog.getOpenFileName( parent = self, caption = "Select image", filter = text_filter )
		if not layout_manager.import_layout( file[0] ):
			print("Couldn't import layout")
		else:
			self.list_layouts()
			self.layoutSelector.setCurrentIndex(self.layoutSelector.count()-1)


	def rename_layout(self):
		self.stashed_layout = self.layoutSelector.currentText()
		self.layoutSelector.setEditable(True)
		self.layoutSelector.lineEdit().editingFinished.connect( self.layout_renamed )
		validator = LayoutValidator( self.layoutSelector.currentText(), layout_manager.get_layout_list())
		self.layoutSelector.setValidator( validator )

	def layout_renamed(self):
		self.layoutSelector.setEditable(False)
		if self.stashed_layout != self.layoutSelector.currentText():
			layout_manager.rename_layout( self.stashed_layout, self.layoutSelector.currentText() )
			self.layoutWidget.refresh()




	def duplicate_layout(self):
		pass

	def export_layout(self):
		pass

	def delete_layout(self):
		pass

