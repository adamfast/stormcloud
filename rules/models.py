# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import requests

from django.db import models

from vendors.models import Vendor

ACTION_CHOICES = (
    ('flat', 'Respond with Configured Response (chooses randomly from active if multiple available)'),
    ('301', 'Respond with a 301 permanent redirect (store URL(s) as Responses to be randomly chosen from)'),
    ('302', 'Respond with a 302 temporary redirect (store URL(s) as Responses to be randomly chosen from)'),
    ('500', 'Respond with an internal server error'),
    ('live', 'Retrieve live URL')
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
    live_url = models.URLField(null=True, blank=True, help_text=u'Used if a live URL should be retrieved.')

    def __unicode__(self):
        return self.path

    def perform_substitutions(self, content):
        for substitute in self.substitutions.filter(active=True):
            content = content.replace(substitute.find, substitute.replace)

        return content

    @property
    def flat_response(self):
        response = ''  # fall back to an empty response
        active_responses = self.responses.filter(active=True)
        if active_responses.count() > 1:
            responses = [r.response for r in active_responses]
            response = random.choice(responses)

        if active_responses.first():  # only one response, return it
            response = active_responses.first().response

        response = self.perform_substitutions(response)

        return response  # fall back to an empty response

    def live_response(self, get=None, verb='get'):
        response = ''  # fall back to empty response

        if self.live_url and verb == 'get':  # require a URL
            live_response = requests.get(self.live_url, params=get)
            if live_response.status_code == 200:
                response = live_response.content

        response = self.perform_substitutions(response)

        return response


class RuleResponse(models.Model):
    rule = models.ForeignKey(Rule, related_name='responses')
    response = models.TextField(null=True, blank=True, default='')
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'Response for %s' % self.rule


class RuleSubstitution(models.Model):
    rule = models.ForeignKey(Rule, related_name='substitutions')
    find = models.TextField(null=False, blank=False)
    replace = models.TextField(null=False, blank=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return u'Replace for rule %s' % self.rule
