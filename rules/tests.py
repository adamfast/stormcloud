# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from rules.models import Rule


class StormCloudMiddlewareTests(TestCase):
    def test_request(self):
        self.assertEqual(Rule.objects.all().count(), 0)

        response = self.client.get('/stripe/post/')

        self.assertEqual(Rule.objects.all().count(), 1)
