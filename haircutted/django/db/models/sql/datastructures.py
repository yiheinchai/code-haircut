class BaseTable:
	def __init__(self=<django.db.models.sql.datastructures.BaseTable object at 0x10766ded0>, table_name='polls_question', alias=None):
		self.table_name = table_name
		self.table_alias = alias


	def as_sql(self=<django.db.models.sql.datastructures.BaseTable object at 0x10766ded0>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		"" if self.table_alias == self.table_name else (" %s" % self.table_alias)
		alias_str = (
		base_sql = compiler.quote_name_unless_alias(self.table_name)
		return sql, params

