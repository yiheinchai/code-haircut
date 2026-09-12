def ready() -> str:
    from .models import update_last_login

    return update_last_login()
