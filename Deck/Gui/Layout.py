from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Deck.LayoutManager import layout_manager
from Deck.DeckController import DeckController

import copy


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
		for i in range( len(self.parameters_description) ):
			self.layout().itemAtPosition( i, 0 ).widget().deleteLater()
			self.layout().itemAtPosition( i, 1 ).widget().deleteLater()

		self.parameters_description = parameters_description
		self.parameters = [None] * len(parameters_description)
		for i, parameter in enumerate( parameters_description ):
			label = QLabel( parameter["label"] )
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
		if self.setting_parameters:
			return
		
		widget = self.layout().itemAtPosition( i, 1 ).widget()
		parameter = None
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

		
		self.name_box = QLineEdit()
		self.name_box.editingFinished.connect( self.change_name )
		grid.addWidget( self.name_box, 0, 1 )

		grid.addWidget( QLabel("Action"), 1, 0)
		self.action_box = QComboBox()
		grid.addWidget( self.action_box, 1, 1 )

		self.parameter_stack = QStackedLayout()

		self.build_parameters()

		self.action_box.currentIndexChanged.connect( self.action_selected )

		self.layout().addLayout( self.parameter_stack )

	def _parameters_changed( self, parameters ):
		self.button["parameters"] = parameters
		if not self.set_by_code:
			self.parameters_changed.emit( self.button )

	def build_parameters(self):
		self.action_box.clear()
		for i, (action_name, action) in enumerate(DeckController.actions.items()):
			self.action_box.addItem( action.label, action_name )
			if i < self.parameter_stack.count():
				self.parameter_stack.itemAt( i ).widget().build( action.parameters )
			else:
				widget = ActionParametersWidget( action.parameters )
				widget.parameters_changed.connect( self._parameters_changed )
				self.parameter_stack.addWidget( widget )


	def set_button(self, button):
		self.set_by_code = True
		self.button = button
		self.name_box.setText(button["name"])
		if "action" in button:
			self.action_box.setCurrentIndex( self.action_box.findData( button["action"] ) )
			self.parameter_stack.currentWidget().set_parameters( button["parameters"] )
		else:
			self.action_box.setCurrentIndex(0)
		self.set_by_code = False

	def change_name(self):
		self.button["name"] = self.name_box.text()
		self.appearance_changed.emit(self.button)

	def showEvent(self, event):
		self.build_parameters()
		if self.button != None:
			self.set_button(self.button)
		super(ButtonPropertiesPanel, self).showEvent(event)

	def action_selected(self, index):
		self.parameter_stack.setCurrentIndex(index)
		if self.button != None:
			self.button["action"] = self.action_box.currentData()
		if not self.set_by_code:
			self.parameter_stack.currentWidget().reset()
			if self.button != None:
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
			button = QPushButton()
			button.setCheckable(True)
			button.pressed.connect( lambda i = i: self.button_selected(i) )
			self.buttons.append(button)

			buttons.addWidget( button, i//4, i%4 )

		self.setLayout(horizontal)

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
		print("button selected")
		if self.current_button >= 0:
			self.buttons[self.current_button].setChecked(False)
		self.current_button = i
		self.edited_by_code = True
		self.button_parameters.set_button( self.layout[str(self.current_button + 1)] )
		

	def set_layout( self, layout_name ):
		if self.current_button >= 0:
			self.buttons[self.current_button].setChecked(False)
		self.current_button = -1
		self.layout = layout_manager.get_layout(layout_name)
		self.layout_name = layout_name
		for i in range(16):
			self.buttons[i].setText( self.layout[str(i+1)]["name"] )

	def change_button_name(self):
		if self.current_button >= 0:
			self.buttons[ self.current_button ].setText( self.name_box.text() )
			self.layout[str(self.current_button+1)]["name"] = self.name_box.text()
			layout_manager.update_layout(self.layout_name, self.layout)


class LayoutsPage(QWidget):
	def __init__(self, *args, **kwargs):
		super(LayoutsPage, self).__init__(*args, **kwargs)
		self.layoutSelector = QComboBox()
		self.layoutWidget = LayoutWidget()

		for layout in layout_manager.get_layout_list():
			self.layoutSelector.addItem( layout )

		self.layoutSelector.currentIndexChanged.connect(self.select_layout)
		self.select_layout()

		vertical = QVBoxLayout()
		vertical.addWidget(self.layoutSelector)
		vertical.addWidget(self.layoutWidget)

		self.setLayout(vertical)


	def select_layout(self):
		layout = self.layoutSelector.currentText()
		self.layoutWidget.set_layout(layout)

