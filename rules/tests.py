# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from rules.models import Rule


class StormCloudMiddlewareTests(TestCase):
    def test_request_creates_rule_entry(self):
        self.assertEqual(Rule.objects.all().count(), 0)

        response = self.client.get('/stripe/post/')

        self.assertEqual(Rule.objects.all().count(), 1)

    def test_request_gets_static_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat', flat_response='unicycle cat')

        response = self.client.get(rule.path)
        self.assertEqual(response.content, rule.flat_response)
