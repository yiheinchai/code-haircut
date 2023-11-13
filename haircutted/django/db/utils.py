class ConnectionRouter:
	def _route_db(self=<django.db.utils.ConnectionRouter object at 0x105eb9090>, model=<django.db.models.base.ModelBase object at 0x1070929d0>, **hints={}):
		chosen_db = None
		instance = hints.get("instance")
		return DEFAULT_DB_ALIAS

class ConnectionHandler:
	def __getitem__(self=<django.db.utils.ConnectionHandler object at 0x105ea0850>, alias='default'):
		try:
			return getattr(self._connections, alias)

class DatabaseErrorWrapper:
	def __enter__(self=<django.db.utils.DatabaseErrorWrapper object at 0x107661250>):
		pass


	def __exit__(self=<django.db.utils.DatabaseErrorWrapper object at 0x107661250>, exc_type=None, exc_value=None, traceback=None):


	def __call__(self=<django.db.utils.DatabaseErrorWrapper object at 0x107661250>, func=<built-in method fetchmany of SQLiteCursorWrapper object at 0x107d0b920>):
		def inner(*args, **kwargs):
		return inner

