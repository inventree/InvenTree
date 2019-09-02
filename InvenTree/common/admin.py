from django.contrib import admin

from .models import Currency


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'suffix', 'description', 'value', 'base')


admin.site.register(Currency, CurrencyAdmin)
