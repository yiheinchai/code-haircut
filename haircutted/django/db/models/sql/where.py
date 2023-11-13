class WhereNode:
	def __init__(self=<django.db.models.sql.where.WhereNode object at 0x107d1e910>, children=None, connector=None, negated=False):
		self.children = children[:] if children else []
		self.connector = connector or self.default
		self.negated = negated


	def clone(self=<django.db.models.sql.where.WhereNode object at 0x107d1e910>):
		clone = self.create(connector=self.connector, negated=self.negated)
		return clone


	def split_having_qualify(self=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>, negated=False, must_group_by=False):


	def contains_aggregate(self=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):
		return self._contains_aggregate(self)
		return res


	def contains_over_clause(self=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):
		return self._contains_over_clause(self)
		return res


	def as_sql(self=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>, compiler=<django.db.models.sql.compiler.SQLCompiler object at 0x10766d890>, connection=<django.db.backends.sqlite3.base.DatabaseWrapper object at 0x107275790>):
		result = []
		result_params = []
		if self.connector == AND:
			full_needed, empty_needed = len(self.children), 1
		conn = " %s " % self.connector
		sql_string = conn.join(result)
		! compile: (<class 'django.core.exceptions.FullResultSet'>, FullResultSet(), <traceback object at 0x107d1f380>)

