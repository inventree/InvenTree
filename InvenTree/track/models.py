from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from part.models import Part

class UniquePart(models.Model):
    """ A unique instance of a Part object.
    Used for tracking parts based on serial numbers,
    and tracking all events in the life of a part
    """
    
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    created = models.DateField(auto_now_add=True,
                               editable=False)
    serial = models.IntegerField()
    
    createdBy = models.ForeignKey(User)
    
class PartTrackingInfo(models.Model):
    """ Single data-point in the life of a UniquePart
    Each time something happens to the UniquePart,
    a new PartTrackingInfo object should be created.
    """
    
    part = models.ForeignKey(UniquePart, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True,
                            editable=False)
    notes = models.CharField(max_length=500)
    
    