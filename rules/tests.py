# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import json

from django.test import TestCase
from django.utils.timezone import now

from rules.models import Rule, RuleResponse, RuleSubstitution


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

    def test_request_get_vs_post_separate_static_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)

        rule2 = Rule.objects.create(hostname='testserver', path=rule.path, verb='POST',
                                   action='flat')
        static2 = RuleResponse.objects.create(rule=rule2, response='motorcycle llama', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.content, static.response)

        response = self.client.post(rule.path)  # same path, different verb
        self.assertEqual(response.content, static2.response)

    def test_request_gets_static_random_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)
        static2 = RuleResponse.objects.create(rule=rule, response='tricycle ant', active=True)

        response = self.client.get(rule.path)
        self.assertTrue(response.content in [static.response, static2.response])

    def test_request_gets_301_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='301')
        static = RuleResponse.objects.create(rule=rule, response='http://www.google.com/', active=True)

        response = self.client.get(rule.path)
        self.assertRedirects(response, static.response, 301, fetch_redirect_response=False)

    def test_request_gets_301_random_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='301')
        static = RuleResponse.objects.create(rule=rule, response='http://www.google1.com', active=True)
        static2 = RuleResponse.objects.create(rule=rule, response='http://www.google2.com', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.url in [static.response, static2.response])

    def test_request_gets_302_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='302')
        static = RuleResponse.objects.create(rule=rule, response='http://www.google.com/', active=True)

        response = self.client.get(rule.path)
        self.assertRedirects(response, static.response, fetch_redirect_response=False)

    def test_request_gets_302_random_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='302')
        static = RuleResponse.objects.create(rule=rule, response='http://www.google1.com', active=True)
        static2 = RuleResponse.objects.create(rule=rule, response='http://www.google2.com', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url in [static.response, static2.response])

    def test_request_action_not_defined(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='unknown')

        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, u'')

    def test_request_gets_500_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='500')

        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, 500)

    def test_request_gets_various_responses(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='501')

        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 502
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 503
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 504
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 401
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 402
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 403
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

        rule.action = 404
        rule.save()
        response = self.client.get(rule.path)
        self.assertEqual(response.status_code, int(rule.action))

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

    def test_request_static_response_with_substitution(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)
        substitute = RuleSubstitution.objects.create(rule=rule, find='unicycle', replace='toboggan', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.content, u'toboggan cat')

    def test_request_static_response_with_inactive_substitution(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='flat')
        static = RuleResponse.objects.create(rule=rule, response='unicycle cat', active=True)
        substitute = RuleSubstitution.objects.create(rule=rule, find='unicycle', replace='toboggan', active=False)

        response = self.client.get(rule.path)
        self.assertEqual(response.content, u'unicycle cat')

    def test_request_live_response(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='live', live_url='http://media.adamfast.com/stormcloud.txt')

        response = self.client.get(rule.path)
        self.assertEqual(response.content, u'live')

    def test_request_static_response_with_substitution(self):
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='GET',
                                   action='live', live_url='http://media.adamfast.com/stormcloud.txt')
        substitute = RuleSubstitution.objects.create(rule=rule, find='live', replace='replaced', active=True)

        response = self.client.get(rule.path)
        self.assertEqual(response.content, substitute.replace)

    def test_post_live_response_requestbin(self):
        self.skipTest("This one requires manual work, so it's disabled - remove skip if you want to test it this way."
                      "You'll also need to set up your own requestb.in and enter the URL here, as it's a temporary one"
                      "that will disappear shortly after I check this in.")
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='POST',
                                   action='live', live_url='https://requestb.in/wst72dws')

        response = self.client.post(rule.path, {'key1': 'value1'})

        print("Manually verify POST data at %s" % rule.live_url)

    def test_post_live_response_httpbin(self):
        # mode #2
        rule = Rule.objects.create(hostname='testserver', path='/stormcloud-test/', verb='POST',
                                   action='live', live_url='https://httpbin.org/post')

        test_payload = {'key1': 'value1'}
        response = self.client.post(rule.path, test_payload)
        response_data = json.loads(response.content)  # response.json() won't work because it doesn't return as application/json
        self.assertEqual(response_data['form'], test_payload)
