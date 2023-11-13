class cached_property:
	def __get__(self=<django.utils.functional.cached_property object at 0x106d3aa10>, instance=<django.db.models.sql.where.WhereNode object at 0x107d1ecd0>, cls=<class 'django.db.models.sql.where.WhereNode'>):
		res = instance.__dict__[self.name] = self.func(instance)
		return res

class SimpleLazyObject:
	def __getattribute__(self=<django.utils.functional.SimpleLazyObject object at 0x1072ffc10>, name='_wrapped'):
		return super().__getattribute__(name)
		value = super().__getattribute__(name)

