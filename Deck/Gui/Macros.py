from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from Deck.MacroManager import manager

import re

from pynput import keyboard, mouse

class ScrollableButtonSelector(QScrollArea):
	button_selected = pyqtSignal( int, object )
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
		self.number_of_buttons = 0

	def edit_button( self, i, text, data ):

		button = self.layout.itemAt(i).widget()
		newButton = QPushButton(text)
		newButton.setCheckable(True)
		newButton.setChecked( button.isChecked() )
		newButton.pressed.connect( lambda i = i, data = data: self.button_pressed(i, data) )
		button.deleteLater()
		self.layout.insertWidget( i, newButton )



	def add_button(self, text, data = None):
		button = QPushButton(text)
		button.setCheckable(True)
		button.pressed.connect( lambda i = self.number_of_buttons, data = data: self.button_pressed(i, data) )

		self.layout.addWidget(button)
		self.number_of_buttons += 1

	def button_pressed(self, i, data):
		if self.current_button >= 0:
			self.layout.itemAt( self.current_button ).widget().setChecked(False)

		self.current_button = i
 
		self.button_selected.emit(i, data)

	def clear(self):
		self.number_of_buttons = 0
		for i in range( self.layout.count() ):
			self.layout.itemAt( i ).widget().deleteLater()

def key_to_text(key):
	text = key
	if len(text) > 1:
		text = text.capitalize()
		if text.endswith("_r"):
			text = "right _"+text[:-2]
		elif text.endswith("_l"):
			text = "left _"+text[:-2]

		text = text.split("_")
		for i, part in enumerate(text):
			text[i] = part.capitalize()

		if text[0] == "Media":
			text = " ".join( text[1:] )
		elif text[0] in ["Num", "Vk"]:
			text = " ".join(text)
		else:
			text = "".join(text)
	return text

def button_to_text(button):
	return {"left":"Left", "middle":"Middle", "right": "Right", "x1":"Button 4", "x2":"Button 5"}[button]

class KeyEdit(QLineEdit):
	key_changed = pyqtSignal( str )

	def on_press(self,key):
		print(key)
		event = QEvent(QEvent.User + 4)
		event.key = key
		QCoreApplication.postEvent(self, event )
		
	def set_key(self, key):
		if isinstance( key, keyboard.KeyCode ):
			key_str = str(key)	
			
			if not key_str.startswith("<"):
				self.key = key_str[1]
			elif hasattr(key, 'vk'):
				if 96 <= key.vk <= 105:
					self.key = "num_" + str(key.vk-96)
				elif key.vk == 110:
					self.key = "num_,"
				else:
					self.key = "vk_" + str(key.vk)
			
		elif isinstance(key, keyboard.Key):
			self.key = key.name
		elif isinstance(key, str):
			self.key = key

		self.setText( key_to_text(self.key) )


	def event(self, event):
		if event.type() == QEvent.User + 4:
			self.set_key( event.key )
				
			self.key_changed.emit( self.key )
			return True
		if event.type() == QEvent.KeyPress:
			return True
		return QLineEdit.event(self,event)

	def focusInEvent(self, event):
		font = self.font()
		font.setWeight( QFont.Bold )
		self.setFont(font)
		self.listener = keyboard.Listener(
		    on_press=self.on_press,
		    )
		self.listener.start()
		return QLineEdit.focusInEvent(self,event)

	def focusOutEvent(self, event):
		self.listener.stop()
		font = self.font()
		font.setWeight( QFont.Normal )
		self.setFont(font)

	


class StepProperties(QFrame):
	properties_changed = pyqtSignal( object )
	flag_key    = 0x01
	flag_button = 0x02
	flag_count  = 0x04
	flag_x      = 0x08
	flag_y      = 0x10
	def __init__(self, *args, **kwargs):
		super( StepProperties, self ).__init__(*args, **kwargs)
		self.setFrameShape(QFrame.Panel)

		self.triggered_by_code = False
		self.matcher = re.compile("\s*\\d+([\\.,]\\d{1,2})?")

		layout = QGridLayout()
		
		
		self.delay_label = QLabel("Delay")
		self.device_label = QLabel("Device")
		self.action_label = QLabel("Action")
		self.key_label = QLabel("Key")
		self.button_label = QLabel("Button")
		self.count_label = QLabel("Count")
		self.x_label = QLabel( "X" )
		self.y_label = QLabel( "Y" )


		layout.addWidget( self.delay_label,  0 ,0 )
		layout.addWidget( self.device_label, 1, 0 )
		layout.addWidget( self.action_label, 2, 0 )
		layout.addWidget( self.key_label,    3, 0 )
		layout.addWidget( self.button_label, 4, 0 )
		layout.addWidget( self.count_label,  5, 0 )
		layout.addWidget( self.x_label,      6, 0 )
		layout.addWidget( self.y_label,      7, 0 )

		self.delay = QLineEdit()
		layout.addWidget( self.delay, 0, 1 )


		self.device_selector = QComboBox()
		self.device_selector.addItem("Keyboard", "keyboard")
		self.device_selector.addItem("Mouse", "mouse")
		layout.addWidget( self.device_selector, 1, 1 )
		
		self.keyboard_action_selector = QComboBox()
		self.keyboard_action_selector.addItem( "Press", "press" )
		self.keyboard_action_selector.addItem( "Release", "release" )

		self.mouse_action_selector = QComboBox()
		self.mouse_action_selector.addItem( "Press", "press" )
		self.mouse_action_selector.addItem( "Release", "release" )
		self.mouse_action_selector.addItem( "Click", "click" )
		self.mouse_action_selector.addItem( "Scroll","scroll" )
		self.mouse_action_selector.addItem( "Position", "position" )
		self.mouse_action_selector.addItem( "Move", "move" )

		self.action_selector_stack = QStackedLayout()
		self.action_selector_stack.addWidget( self.keyboard_action_selector )
		self.action_selector_stack.addWidget( self.mouse_action_selector )

		layout.addLayout( self.action_selector_stack, 2, 1 )
		
		self.key = KeyEdit()
		self.key.key_changed.connect( self.key_changed )
		layout.addWidget( self.key, 3, 1 )

		self.button = QComboBox()
		self.button.addItem("Left", "left")
		self.button.addItem("Middle", "middle")
		self.button.addItem("Right", "right")
		self.button.addItem("Button 4", "x1")
		self.button.addItem("Button 5", "x2")
		self.button.currentIndexChanged.connect( self.button_changed )
		layout.addWidget( self.button, 4, 1 )

		self.count = QLineEdit()
		self.count.setValidator( QIntValidator() )
		self.count.editingFinished.connect( self.count_changed )
		layout.addWidget(self.count, 5, 1)

		self.x = QLineEdit()
		self.x.setValidator( QIntValidator() )
		self.x.editingFinished.connect( self.x_changed )
		layout.addWidget( self.x, 6, 1 )

		self.y = QLineEdit()
		self.y.setValidator( QIntValidator() )
		self.y.editingFinished.connect( self.y_changed )
		layout.addWidget( self.y, 7, 1 )


		self.device_selector.currentIndexChanged.connect( self.action_selector_stack.setCurrentIndex )
		self.device_selector.currentIndexChanged.connect( self.device_changed )

		self.delay.editingFinished.connect( self.delay_changed )

		self.mouse_action_selector.currentIndexChanged.connect( self.action_changed )
		self.keyboard_action_selector.currentIndexChanged.connect( self.action_changed )


		self.setLayout( layout )

	def show_parameters( self, parameters ):
		if parameters & self.flag_key:
			self.key_label.show()
			self.key.show()
		else:
			self.key_label.hide()
			self.key.hide()

		if parameters & self.flag_button:
			self.button_label.show()
			self.button.show()
		else:
			self.button_label.hide()
			self.button.hide()

		if parameters & self.flag_count:
			self.count_label.show()
			self.count.show()
		else:
			self.count_label.hide()
			self.count.hide()

		if parameters & self.flag_x:
			self.x_label.show()
			self.x.show()
		else:
			self.x_label.hide()
			self.x.hide()

		if parameters & self.flag_y:
			self.y_label.show()
			self.y.show()
		else:
			self.y_label.hide()
			self.y.hide()

	def device_changed(self, index):
		if not self.triggered_by_code:
			self.step["device"] = ["keyboard", "mouse"][index]
			self.action_selector_stack.currentWidget().blockSignals(True)
			self.action_selector_stack.currentWidget().setCurrentIndex(0)
			self.action_changed(0)
			self.action_selector_stack.currentWidget().blockSignals(False)

	def clear_parameters( self, parameters ):
		for parameter in parameters:
			if parameter in self.step:
				self.step.pop(parameter)
		
	def action_changed( self, index ):
		if not self.triggered_by_code:
			if self.device_selector.currentIndex() == 0:
				self.step["action"] = ["press", "release"][index]
				self.clear_parameters(["button" "count", "x", "y"])
				self.show_parameters( self.flag_key )
				self.key.set_key("")
				self.key_changed( "" )
				
			else:
				self.step["action"] = ["press", "release", "click", "scroll",  "position", "move"][index]
				match index:
					case 0 | 1:
						self.show_parameters( self.flag_button )
						self.clear_parameters(["key", "count", "x", "y"])
						self.button.setCurrentIndex(0)
						self.button_changed(0)


					case 2:
						self.show_parameters( self.flag_button | self.flag_count )
						self.clear_parameters(["key", "x", "y"])
						self.button.setCurrentIndex(0)
						self.count.setText("0")
						self.button_changed( 0 )
						self.count_changed()


					case 3 | 4 | 5:
						self.show_parameters( self.flag_x | self.flag_y )
						self.clear_parameters(["key", "button", "count" ])
						self.x.setText("0")
						self.x_changed()
						self.y.setText("0")
						self.y_changed()
						



	def key_changed( self, key ):
		self.step["key"] = key
		self.properties_changed.emit( self.step )

	def button_changed( self, button ):
		if not self.triggered_by_code:
			self.step["button"] = self.button.currentData()
			self.properties_changed.emit( self.step )

	def count_changed( self, count ):
		self.step["count"] = int(self.count.text())
		self.properties_changed.emit( self.step )

	def x_changed( self ):
		self.step["x"] = int(self.x.text())
		self.properties_changed.emit( self.step )

	def y_changed( self ):
		self.step["y"] = int(self.y.text())
		self.properties_changed.emit( self.step )

	def set_step(self, step):
		self.triggered_by_code = True
		self.step = step
		self.delay.setText( str( step["delay"] ) + "s" )
		match step["device"]:
			case "keyboard":
				self.device_selector.setCurrentIndex(0)
				self.keyboard_action_selector.setCurrentIndex( self.keyboard_action_selector.findData( step["action"] ) )
				self.key.set_key( step["key"] )
				self.show_parameters( self.flag_key )
			case "mouse":
				self.device_selector.setCurrentIndex(1)
				index = self.mouse_action_selector.findData( step["action"] )
				self.mouse_action_selector.setCurrentIndex(index)

				match index:
					case 0 | 1:
						self.show_parameters( self.flag_button )
						self.button.setCurrentIndex( self.button.findData(step["button"]) )


					case 2:
						self.show_parameters( self.flag_button | self.flag_count )
						self.button.setCurrentIndex( self.button.findData(step["button"]) )
						self.count.setText( str( step["count"] ) )

					case 3 | 4 | 5:
						self.show_parameters( self.flag_x | self.flag_y )
						self.x.setText( str(step["x"]) )
						self.y.setText( str(step["y"]) )


		self.triggered_by_code = False
		

	def delay_changed(self):
		value_str = self.matcher.match( self.delay.text()).group(0) 
		value_str = ".".join(value_str.split(","))
		value = float( value_str )
		self.step["delay"] = value
		self.delay.setText( str(value) + "s" )

		self.properties_changed.emit( self.step )




class MacrosPage(QWidget):
	def __init__(self, *args, **kwargs):
		super(MacrosPage, self).__init__( *args, **kwargs )
		layout = QHBoxLayout()

		self.macroSelector = ScrollableButtonSelector()
		self.stepSelector = ScrollableButtonSelector()
		
		for macro in manager.get_macro_list():
			self.macroSelector.add_button( macro, macro )

		self.macroSelector.button_selected.connect(self.macro_selected)
		self.stepSelector.button_selected.connect(self.step_selected)

		self.properties = StepProperties()

		layout.addWidget(self.macroSelector)
		layout.addWidget(self.stepSelector)
		layout.addWidget(self.properties)

		self.properties.properties_changed.connect(self.properties_changed)

		self.setLayout(layout)

		self.current_step = -1

	def macro_selected(self, i, macro_name):
		self.macro_name = macro_name
		self.macro = manager.get_macro( macro_name )
		self.stepSelector.clear()
		for i, step in enumerate(self.macro):
			text = step["action"] + " "
			if step["device"] == "keyboard":
				text += key_to_text(step["key"])
			elif step["device"] == "mouse" and step["action"] in ["press", "release"]:
				text += button_to_text(step["button"])

			self.stepSelector.add_button( text, step )

	def step_selected(self, i, step ):
		self.current_step = i
		self.properties.set_step(step)

	def properties_changed(self, step):
		print("properties have changed")
		text = step["action"] + " "
		if step["device"] == "keyboard":
			text += key_to_text(step["key"])
		elif step["device"] == "mouse" and step["action"] in ["press", "release"]:
			text += button_to_text( step["button"] )
		self.stepSelector.edit_button( self.current_step, text, step )
		self.macro[self.current_step] = step
		manager.set_macro( self.macro_name, self.macro )

