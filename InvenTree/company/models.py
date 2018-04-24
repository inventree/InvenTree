# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models


def rename_company_image(instance, filename):
    base = 'company_images'

    if filename.count('.') > 0:
        ext = filename.split('.')[-1]
    else:
        ext = ''

    fn = 'company_{pk}_img'.format(pk=instance.pk)

    if ext:
        fn += '.' + ext

    return os.path.join(base, fn)


class Company(models.Model):

    name = models.CharField(max_length=100, unique=True,
                            help_text='Company name')

    description = models.CharField(max_length=500)

    website = models.URLField(blank=True, help_text='Company website URL')

    address = models.CharField(max_length=200,
                               blank=True, help_text='Company address')

    phone = models.CharField(max_length=50,
                             blank=True)

    email = models.EmailField(blank=True)

    contact = models.CharField(max_length=100,
                               blank=True)

    URL = models.URLField(blank=True, help_text='Link to external company information')

    image = models.ImageField(upload_to=rename_company_image, max_length=255, null=True, blank=True)

    notes = models.TextField(blank=True)

    is_customer = models.BooleanField(default=False)

    is_supplier = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/company/{id}/".format(id=self.id)

    @property
    def part_count(self):
        return self.parts.count()

    @property
    def has_parts(self):
        return self.part_count > 0
