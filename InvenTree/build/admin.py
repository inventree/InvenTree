# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Build, BuildOutput


class BuildAdmin(admin.ModelAdmin):

    list_display = ('status', )


class BuildOutputAdmin(admin.ModelAdmin):

    list_display = ('build', 'part', 'batch', 'quantity', )


admin.site.register(Build, BuildAdmin)
admin.site.register(BuildOutput, BuildOutputAdmin)