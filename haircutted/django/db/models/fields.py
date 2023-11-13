class BigAutoField:
	def get_col(self=<django.db.models.fields.BigAutoField object at 0x10732fb10>, alias='polls_question', output_field=None):
		if alias == self.model._meta.db_table and (
		output_field is None or output_field == self
		return self.cached_col


	def select_format(self=<django.db.models.fields.BigAutoField object at 0x10732fb10>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, sql='"polls_question"."id"', params=[]):
		return sql, params


	def get_internal_type(self=<django.db.models.fields.BigAutoField object at 0x10732fb10>):
		return "BigAutoField"


	def __eq__(self=<django.db.models.fields.BigAutoField object at 0x10732fb10>, other=<django.db.models.fields.BigAutoField object at 0x10732fb10>):
		if isinstance(other, Field):
			return self.creation_counter == other.creation_counter and getattr(
			self, "model", None
			) == getattr(other, "model", None)


	def get_db_converters(self=<django.db.models.fields.BigAutoField object at 0x10732fb10>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return []

class CharField:
	def get_col(self=<django.db.models.fields.CharField object at 0x107275010>, alias='polls_question', output_field=None):
		if alias == self.model._meta.db_table and (
		output_field is None or output_field == self
		return self.cached_col


	def select_format(self=<django.db.models.fields.CharField object at 0x107275010>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, sql='"polls_question"."question_text"', params=[]):
		return sql, params


	def get_internal_type(self=<django.db.models.fields.CharField object at 0x107275010>):
		return "CharField"


	def __eq__(self=<django.db.models.fields.CharField object at 0x107275010>, other=<django.db.models.fields.CharField object at 0x107275010>):
		if isinstance(other, Field):
			return self.creation_counter == other.creation_counter and getattr(
			self, "model", None
			) == getattr(other, "model", None)


	def get_db_converters(self=<django.db.models.fields.CharField object at 0x107275010>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return []

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
			) == getattr(other, "model", None)


	def get_db_converters(self=<django.db.models.fields.DateTimeField object at 0x1072751d0>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		return []

