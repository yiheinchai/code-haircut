class Col:
	def as_sql(self=<django.db.models.expressions.Col object at 0x107660a50>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		alias, column = self.alias, self.target.column
		identifiers = (alias, column) if alias else (column,)
		sql = ".".join(map(compiler.quote_name_unless_alias, identifiers))
		return sql, []


	def select_format(self=<django.db.models.expressions.Col object at 0x107660a50>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, sql='"polls_question"."pub_date"', params=[]):
		if hasattr(self.output_field, "select_format"):
			return self.output_field.select_format(compiler, sql, params)


	def get_db_converters(self=<django.db.models.expressions.Col object at 0x107660a50>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		if self.target == self.output_field:
			return self.output_field.get_db_converters(connection)

