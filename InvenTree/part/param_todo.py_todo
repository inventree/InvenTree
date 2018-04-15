"""
TODO - Implement part parameters, and templates

See code below
"""



class PartParameterTemplate(models.Model):
    """ A PartParameterTemplate pre-defines a parameter field,
    ready to be copied for use with a given Part.
    A PartParameterTemplate can be optionally associated with a PartCategory
    """
    name = models.CharField(max_length=20, unique=True)
    units = models.CharField(max_length=10, blank=True)

    # Parameter format
    PARAM_NUMERIC = 10
    PARAM_TEXT = 20
    PARAM_BOOL = 30

    PARAM_TYPE_CODES = {
        PARAM_NUMERIC: _("Numeric"),
        PARAM_TEXT: _("Text"),
        PARAM_BOOL: _("Bool")
    }

    format = models.PositiveIntegerField(
        default=PARAM_NUMERIC,
        choices=PARAM_TYPE_CODES.items(),
        validators=[MinValueValidator(0)])

    def __str__(self):
        return "{name} ({units})".format(
            name=self.name,
            units=self.units)

    class Meta:
        verbose_name = "Parameter Template"
        verbose_name_plural = "Parameter Templates"


class CategoryParameterLink(models.Model):
    """ Links a PartParameterTemplate to a PartCategory
    """
    category = models.ForeignKey(PartCategory, on_delete=models.CASCADE)
    template = models.ForeignKey(PartParameterTemplate, on_delete=models.CASCADE)

    def __str__(self):
        return "{name} - {cat}".format(
            name=self.template.name,
            cat=self.category)

    class Meta:
        verbose_name = "Category Parameter"
        verbose_name_plural = "Category Parameters"
        unique_together = ('category', 'template')


class PartParameter(models.Model):
    """ PartParameter is associated with a single part
    """

    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='parameters')
    template = models.ForeignKey(PartParameterTemplate)

    # Value data
    value = models.CharField(max_length=50, blank=True)
    min_value = models.CharField(max_length=50, blank=True)
    max_value = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return "{name} : {val}{units}".format(
            name=self.template.name,
            val=self.value,
            units=self.template.units)

    @property
    def units(self):
        return self.template.units

    @property
    def name(self):
        return self.template.name

    class Meta:
        verbose_name = "Part Parameter"
        verbose_name_plural = "Part Parameters"
        unique_together = ('part', 'template')
