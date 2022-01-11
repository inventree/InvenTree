
import django
from ..models import SalesOrderBasket
from django.utils.translation import gettext as _
register = django.template.Library()

@register.simple_tag
def get_current_so_name(key):
  try:
    order = SalesOrderBasket.objects.filter(pk=key).first().get_current_so()
    return order.reference
  except Exception as e:
     return _("There is no order in basket right now")
  

@register.simple_tag
def get_current_so_link(key):
  try:
    order = SalesOrderBasket.objects.filter(pk=key).first().get_current_so()
    return order.pk
  except:
    return ""

@register.simple_tag
def get_current_so_responsible(key):
  try:
    order = SalesOrderBasket.objects.filter(pk=key).first().get_current_so()
    return order.responsible
  except:
    return ""
