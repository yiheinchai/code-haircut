class LazySettings:
	def __getattribute__(self=<django.conf.LazySettings object at 0x105945e10>, name='USE_TZ'):
		value = super().__getattribute__(name)
		return value

