# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Vendor(models.Model):
    name = models.CharField(max_length=64, null=False, blank=True, default='')
    base_url = models.CharField(max_length=256, null=False, blank=True, default='')
    override_instructions = models.TextField(null=False, blank=True, default='')

    def __unicode__(self):
        return self.name
