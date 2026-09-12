"""Minimal Django ORM create/get used to verify large-library slicing."""

from __future__ import annotations


def run() -> str:
    import django
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="haircut-test",
            DEBUG=True,
            INSTALLED_APPS=["django.contrib.contenttypes"],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
            USE_I18N=False,
            USE_TZ=False,
        )
    django.setup()

    from django.contrib.contenttypes.models import ContentType
    from django.db import connection

    with connection.schema_editor() as editor:
        editor.create_model(ContentType)

    obj = ContentType.objects.create(app_label="demo", model="thing")
    got = ContentType.objects.get(pk=obj.pk)
    assert got.model == "thing"
    return got.model


if __name__ == "__main__":
    print(run())
