class Question:
	def __init__(self=<polls.models.Question object at 0x107d1f6d0>, *args=(1, 'are you gay?', datetime(2023, 11, 8, 23, 52, 21, 573273, tzinfo=<datetime.timezone object at 0x1055000d0>, fold=0)), **kwargs={}):
		cls = self.__class__
		opts = self._meta
		_setattr = setattr
		_DEFERRED = DEFERRED
		pre_init.send(sender=cls, args=args, kwargs=kwargs)
		self._state = ModelState()
		if not kwargs:
		fields_iter = iter(opts.concrete_fields)
		for val, field in zip(args, fields_iter):
		_setattr(self, field.attname, val)
		for val, field in zip(args, fields_iter):
		_setattr(self, field.attname, val)
		for val, field in zip(args, fields_iter):
		_setattr(self, field.attname, val)
		for val, field in zip(args, fields_iter):
		for field in fields_iter:
		super().__init__()
		post_init.send(sender=cls, instance=self)

