# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.test import TestCase
from django.utils.timezone import now

from rules.models import Rule, RuleResponse


class StormCloudMiddlewareTests(TestCase):
    def test_request_creates_rule_entry(self):
        self.assertEqual(Rule.objects.all().count(), 0)

        response = self.client.get('/stripe/post/')

        self.assertEqual(Rule.objects.all().count(), 1)

    def test_request_gets_static_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.content, static.response)

    def test_request_gets_static_random_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)
        static2 = RuleResponse.objects.create(rule=rule, response='tricycle ant', active=True)

        response = self.client.get(rule.path)
        self.assertTrue(response.content in [static.response, static2.response])

    def test_static_request_with_delay(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat', delay_ms=200)
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)

        start = now()
        response = self.client.get(rule.path)
        end = now()
        self.assertEqual(response.content, static.response)
        self.assertTrue(end - start > datetime.timedelta(seconds=0.2))

        # remove the delay and verify it comes back faster
        rule.delay_ms = None
        rule.save()

        start = now()
        response = self.client.get(rule.path)
        end = now()
        self.assertEqual(response.content, rule.flat_response)
        self.assertTrue(end - start < datetime.timedelta(seconds=0.2))
