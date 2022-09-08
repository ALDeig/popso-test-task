from django.contrib import admin

from . import models

admin.site.register(models.Channel)
admin.site.register(models.News)
admin.site.register(models.Tag)
# Register your models here.
