# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random

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
    delay_ms = models.PositiveIntegerField(null=True, blank=True,
                                           help_text=u'The response will be delayed by this much time, useful for '
                                                     u'simulating slow connections or causing timeouts.')
    master_wsdl_url = models.URLField(null=True, blank=True)
    wsdl_find = models.CharField(max_length=128, null=False, blank=True, default='')
    wsdl_replace = models.CharField(max_length=128, null=False, blank=True, default='')

    def __unicode__(self):
        return self.path

    @property
    def flat_response(self):
        active_responses = self.responses.filter(active=True)
        if active_responses.count() > 1:
            responses = [r.response for r in active_responses]
            return random.choice(responses)

        if active_responses.first():  # only one response, return it
            return active_responses.first().response

        return None  # fall back to an empty response


class RuleResponse(models.Model):
    rule = models.ForeignKey(Rule, related_name='responses')
    response = models.TextField(null=True, blank=True, default='')
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'Response for %s' % self.rule
