# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from vendors.models import Vendor

ACTION_CHOICES = (
    ('flat', 'Respond with Flat Response'),
    ('wsdl_replaced', 'Respond with cached find/replaced WSDL file'),
)


class Rule(models.Model):
    vendor = models.ForeignKey(Vendor, null=True, blank=True)
    hostname = models.CharField(max_length=64, null=False, blank=True, default='')
    path = models.CharField(max_length=256, null=False, blank=True, default='')
    verb = models.CharField(max_length=32, null=False, blank=False, default='GET')
    action = models.CharField(max_length=64, null=False, blank=True, default='', choices=ACTION_CHOICES)
    delay_ms = models.PositiveIntegerField(null=True, blank=True)
    flat_response = models.TextField(null=True, blank=True)
    master_wsdl_url = models.URLField(null=True, blank=True)
    wsdl_find = models.CharField(max_length=128, null=False, blank=True, default='')
    wsdl_replace = models.CharField(max_length=128, null=False, blank=True, default='')

    def __unicode__(self):
        return self.path
