from django.db import models
from InvenTree.status_codes import BasketStatus
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
    
  

    status =  models.PositiveIntegerField(
        choices=BasketStatus.items(),
        default=BasketStatus.EMPTY,
        help_text=_('Basket status')
    )
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


    def __str__(self):

        return f"{self.name} - {self.status}"