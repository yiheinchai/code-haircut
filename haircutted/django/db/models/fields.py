class DateTimeField:
	def get_col(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>, alias='polls_question', output_field=None):
		if alias == self.model._meta.db_table and (
		output_field is None or output_field == self
		return self.cached_col


	def select_format(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, sql='"polls_question"."pub_date"', params=[]):
		return sql, params


	def get_internal_type(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>):
		return "DateTimeField"


	def __eq__(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>, other=<django.db.models.fields.DateTimeField object at 0x1072751d0>):
		if isinstance(other, Field):
		return self.creation_counter == other.creation_counter and getattr(
		self, "model", None
		return self.creation_counter == other.creation_counter and getattr(
		) == getattr(other, "model", None)
		return self.creation_counter == other.creation_counter and getattr(


	def get_db_converters(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return []
