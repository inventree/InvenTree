from django.db import models
import InvenTree.helpers as helpers
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.contrib.auth.models import User
# Create your models here.


class SalesOrderBasket(models.Model):
    name = models.CharField(max_length=124, unique=True, null=True, default=None)
    created_by = models.ForeignKey(User,
                                   on_delete=models.SET_NULL,
                                   blank=True, null=True,
                                   related_name='+',
                                   verbose_name=_('Created By')
                                   )
    creation_date = models.DateField(auto_now_add=True, editable=False, verbose_name=_('Creation Date'))
    
    BUSY = 1  # Order is pending
    EMPTY = 0
    WAITING_FOR_PACKAGE = 2
    status = {
        BUSY: _("Busy"),
        EMPTY: _("Empty"),
        WAITING_FOR_PACKAGE: _("Waiting for packing")
    }
    # barcode = models.CharField(max_length=124, unique=True, null=True, default=None)

    def format_barcode(self, **kwargs):
        """ Return a JSON string for formatting a barcode for this Basket object """

        return helpers.MakeBarcode(
            'orderbasket',
            self.pk,
            {
                "name": self.name,
                "url": reverse('api-basket-detail', kwargs={'pk': self.id}),
            },
            **kwargs
        )

    @property
    def barcode(self):
        """
        Brief payload data (e.g. for labels)
        """
        return self.format_barcode(brief=True)