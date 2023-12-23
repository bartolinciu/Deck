import os


import json
import shutil

import Deck

class ImageManager:
	image_filename = "images.json"
	image_path = os.path.join( Deck.config_path, image_filename )
	def __init__(self):
		self.update_listeners = []
		if not os.path.isdir( Deck.config_path ):
			os.makedirs(Deck.config_path)
		if not os.path.isfile( self.image_path ):
			self.images = {}
			with open( self.image_path, "wt" ) as f:
				f.write( "{}" )
		else:
			with open( self.image_path, "rt" ) as f:
				self.images = json.loads( f.read() )

	def add_image_update_listener( self, listener, priority ):
		self.update_listeners.append( (priority, listener) )
		self.update_listeners.sort( key = lambda x: x[0] )

	def get_images(self):
		return self.images.keys()

	def get_hosting_path(self, image):
		return self.images[image]["hostingPath"]

	def symlinks_allowed(self):
		try:
			os.symlink( "a", "tmp.lnk" )
			os.unlink( "tmp.lnk" )
			return True
		except OSError:
			return False

	def get_image_definition(self, image):
		definition = None
		try:
			definition = self.images[image]
			definition["name"] = image
		except KeyError:
			pass
		return definition

	def import_image(self, definition):
		name = definition.pop("name")
		

		_, extension = os.path.splitext( definition["path"] )

		if "pathTouched" in definition:
			definition.pop("pathTouched")

		if not self.symlinks_allowed():
			definition["isLink"] = False

		definition["hostingPath"] = os.path.join( "images", name + extension)

		if definition["isLink"]:
			os.symlink( definition["path"], self.hosting_path_to_filesystem_path( definition["hostingPath"]) )
		else:
			shutil.copyfile( definition["path"], self.hosting_path_to_filesystem_path( definition["hostingPath"]) )

		self.images[ name ] = definition
		self.save()

	def hosting_path_to_filesystem_path(self, hosting_path):
		return os.path.join(Deck.web_path, hosting_path)

	def update_image( self, old_name, new_definition ):
		old_definition = self.images[ old_name ]
		new_name=new_definition.pop("name")

		_, extension = os.path.splitext( new_definition["path"] )
		new_definition["hostingPath"] = os.path.join( "images", new_name + extension)

		path_touched = new_definition.pop("pathTouched")

		if not self.symlinks_allowed() and new_definition["isLink"] and ( not old_definition["isLink"] or ( new_definition["path"] != old_definition["path"] ) ):
			new_definition["isLink"] = False

		if new_name != old_name and  \
			(
				(new_definition["isLink"] and old_definition["isLink"] and new_definition["path"] == old_definition["path"]) or \
				( not path_touched and not new_definition["isLink"] and not old_definition["isLink"] ) \
			):
			os.rename( self.hosting_path_to_filesystem_path(old_definition["hostingPath"]), self.hosting_path_to_filesystem_path(new_definition["hostingPath"]) )
		else:
			if os.path.isfile( self.hosting_path_to_filesystem_path(old_definition["hostingPath"] ) ):
				os.unlink( self.hosting_path_to_filesystem_path( old_definition["hostingPath"] ) )	
			if new_definition["isLink"]:
				os.symlink( new_definition["path"], self.hosting_path_to_filesystem_path( new_definition["hostingPath"] ) )
			else:
				shutil.copyfile( new_definition["path"], self.hosting_path_to_filesystem_path( new_definition["hostingPath"] ) )


		self.images.pop( old_name )
		self.images[ new_name ] = new_definition
		self.save()

		for listener in self.update_listeners:
			listener[1].on_image_update(old_name, new_name)
		

	def delete_image( self, name ):
		definition = self.images[name]
		if os.path.isfile( self.hosting_path_to_filesystem_path( definition["hostingPath"] ) ):
			os.unlink( self.hosting_path_to_filesystem_path(definition["hostingPath"] ) )		

		self.images.pop( name )
		self.save()

		for listener in self.update_listeners:
			listener[1].on_image_update(old_name, None)

	def save(self):
		with open( self.image_path, "wt" ) as f:
			f.write( json.dumps( self.images, indent="\t" ) )

manager = ImageManager()