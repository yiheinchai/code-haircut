class cached_property:
	def __get__(self=<django.utils.functional.cached_property object at 0x106d3b7d0>, instance=<django.db.models.sql.query.Query object at 0x107704590>, cls=<class 'django.db.models.sql.query.Query'>):
		res = instance.__dict__[self.name] = self.func(instance)
		self.ref_alias(alias)
		return alias
		def __get__(self=<django.utils.functional.cached_property object at 0x106d3a950>, instance=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>, cls=<class 'django.db.models.sql.where.WhereNode'>):
		res = instance.__dict__[self.name] = self.func(instance)
		def __get__(self=<django.utils.functional.cached_property object at 0x106d3aa10>, instance=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>, cls=<class 'django.db.models.sql.where.WhereNode'>):
		res = instance.__dict__[self.name] = self.func(instance)
		return self, None, None
		extra_select = self.get_extra_select(order_by, self.select)
		self.has_extra_select = bool(extra_select)
		group_by = self.get_group_by(self.select + extra_select, order_by)
		for_update_part = None
		with_limit_offset = with_limits and self.query.is_sliced
		combinator = self.query.combinator
		features = self.connection.features
		distinct_fields, distinct_params = self.get_distinct()

class SimpleLazyObject:
	def __getattribute__(self=<django.utils.functional.SimpleLazyObject object at 0x1072ffc10>, name='sub'):
		value = super().__getattribute__(name)
		! __getattribute__: (<class 'AttributeError'>, AttributeError("'SimpleLazyObject' object has no attribute 'sub'"), <traceback object at 0x107d1f6c0>)
		def __getattribute__(self=<django.utils.functional.SimpleLazyObject object at 0x1072ffc10>, name='_wrapped'):
		return super().__getattribute__(name)

