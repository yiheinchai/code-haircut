class WhereNode:
	def create(cls=<class 'django.db.models.sql.where.WhereNode'>, children=None, connector='AND', negated=False):
		obj = Node(children, connector or cls.default, negated)
		obj.__class__ = cls
		return obj


	def _contains_aggregate(cls=<class 'django.db.models.sql.where.WhereNode'>, obj=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):


	def _contains_over_clause(cls=<class 'django.db.models.sql.where.WhereNode'>, obj=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>):

