class Manager:
	def all(self=<django.db.models.manager.Manager object at 0x1073fb650>):
		return self.get_queryset()


	def get_queryset(self=<django.db.models.manager.Manager object at 0x1073fb650>):
		return self._queryset_class(model=self.model, using=self._db, hints=self._hints)

