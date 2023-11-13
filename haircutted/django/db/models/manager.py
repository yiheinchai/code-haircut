class ManagerDescriptor:
	def __get__(self=<django.db.models.manager.ManagerDescriptor object at 0x107354690>, instance=None, cls=<django.db.models.base.ModelBase object at 0x1070929d0>):
		return cls._meta.managers_map[self.manager.name]

class Manager:
	def all(self=<django.db.models.manager.Manager object at 0x1073fb650>):
		return self.get_queryset()


	def get_queryset(self=<django.db.models.manager.Manager object at 0x1073fb650>):
		return self._queryset_class(model=self.model, using=self._db, hints=self._hints)

