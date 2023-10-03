from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Deck.LayoutManager import layout_manager
from Deck.DeckController import DeckController

class LayoutWidget(QWidget):
	def __init__(self, *args, **kwargs):
		super( LayoutWidget, self ).__init__(*args, **kwargs)
		self.current_button = -1

		horizontal = QHBoxLayout()
		buttons = QGridLayout()
		propertiesLayout = QVBoxLayout()

		self.name_box = QLineEdit()
		self.name_box.returnPressed.connect( self.change_button_name )
		self.name_box.editingFinished.connect( self.change_button_name )

		action_strip = QHBoxLayout()
		action_label = QLabel("Action:")
		self.action_box = QComboBox()
		for action in DeckController.actions:
			self.action_box.addItem( DeckController.actions[action].label, action )

		self.action_box.currentIndexChanged.connect( self.action_selected )
		action_strip.addWidget(action_label)
		action_strip.addWidget(self.action_box)

		parameter_strip_layout = QHBoxLayout()
		self.parameter_label = QLabel()

		self.parameter_stack = QStackedLayout()

		self.parameter_combo = QComboBox()
		self.parameter_edit = QLineEdit()
		self.parameter_boolean = QCheckBox()

		self.parameter_stack.addWidget( self.parameter_combo )
		self.parameter_stack.addWidget( self.parameter_edit )
		self.parameter_stack.addWidget( self.parameter_boolean )

		self.parameter_combo.currentIndexChanged.connect(self.parameter_changed)
		self.parameter_edit.editingFinished.connect(self.parameter_changed)
		self.parameter_boolean.stateChanged.connect(self.parameter_changed)

		parameter_strip_layout.addWidget( self.parameter_label )
		parameter_strip_layout.addLayout( self.parameter_stack )

		self.parameter_strip = QWidget()
		self.parameter_strip.setLayout( parameter_strip_layout )

		propertiesLayout.addWidget(self.name_box)
		propertiesLayout.addLayout(action_strip)
		propertiesLayout.addWidget(self.parameter_strip)
		

		horizontal.addLayout(buttons)
		horizontal.addLayout(propertiesLayout)

		self.buttons = []

		self.skip_parameter_save = False

		for i in range(16):
			button = QPushButton()
			button.setCheckable(True)
			button.pressed.connect( lambda i = i: self.button_selected(i) )
			self.buttons.append(button)

			buttons.addWidget( button, i//4, i%4 )

		self.setLayout(horizontal)

	def parameter_changed(self):
		if self.skip_parameter_save:
			return
		print("parameter changed")
		action = DeckController.actions[self.action_box.currentData()]
		if self.current_button < 0:
			return
		match action.parameter_type:
			case "List":
				self.layout[ str( self.current_button+1 ) ]["parameter"] = self.parameter_combo.currentText()
			case "Text":
				self.layout[ str( self.current_button+1 ) ]["parameter"] = self.parameter_edit.text()
			case "Boolean":
				self.layout[ str( self.current_button+1 ) ]["parameter"] = self.parameter_boolean.isChecked()
		#print(self.layout)
		layout_manager.update_layout(self.layout_name, self.layout)

	def action_selected(self):
		print("action selected", self.edited_by_code)
		try:
			action = DeckController.actions[ self.action_box.currentData() ]
			self.parameter_label.setText( action.parameter_label )
			self.skip_parameter_save = True

			match action.parameter_type:
				case "None":
					self.parameter_strip.hide()

				case "List":
					self.parameter_stack.setCurrentIndex(0)
					print("clear")
					self.parameter_combo.clear()
					print("adding items")
					for value in action.parameter_values:
						self.parameter_combo.addItem( value )

					if self.edited_by_code and self.current_button >= 0:
						print("changing index")
						self.parameter_combo.setCurrentIndex( self.parameter_combo.findText( self.layout[ str(self.current_button+1) ]["parameter"] ) )
					else:
						self.skip_parameter_save = False
						self.parameter_combo.setCurrentIndex(0)

					self.parameter_strip.show()

				case "Text":
					self.parameter_stack.setCurrentIndex(1)
					if self.edited_by_code and self.current_button >= 0:
						self.parameter_edit.setText( self.layout[ str(self.current_button+1) ]["parameter"] )
					else:
						self.skip_parameter_save = False
						self.parameter_edit.setText("")
					self.parameter_strip.show()

				case "Boolean":
					self.parameter_stack.setCurrentIndex(2)
					if self.edited_by_code and self.current_button >= 0:
						self.parameter_boolean.setChecked( self.layout[ str(self.current_button+1) ]["parameter"] )
					else:
						self.skip_parameter_save = False
						self.parameter_boolean.setChecked(False)
					self.parameter_strip.show()

			if not self.edited_by_code and self.current_button >= 0:
				self.layout[ str( self.current_button + 1 ) ]["action"] = action.name
				self.parameter_changed()
		except KeyError:
			self.parameter_strip.hide()
		self.skip_parameter_save=False


	def button_selected( self, i ):
		print("button selected")
		if self.current_button >= 0:
			self.buttons[self.current_button].setChecked(False)
		self.current_button = i
		self.edited_by_code = True
		self.name_box.setText( self.layout[str(i+1)]["name"] )
		try:
			self.action_box.setCurrentIndex( self.action_box.findData( self.layout[str(i+1)]["action"] ) )
		except KeyError:
			self.action_box.setCurrentIndex(-1)
		self.action_selected()
		self.edited_by_code = False

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