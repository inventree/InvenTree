# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Build


class BuildAdmin(admin.ModelAdmin):

    list_display = ('status', )


admin.site.register(Build, BuildAdmin)
