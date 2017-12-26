# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import *


class RuleResponseInline(admin.TabularInline):
    model = RuleResponse


class RuleSubstitutionInline(admin.TabularInline):
    model = RuleSubstitution


class RuleAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'hostname', 'path', 'verb', 'action', 'delay_ms', 'live_url')
    list_filter = ('vendor', 'verb', 'action')
    inlines = (RuleResponseInline, RuleSubstitutionInline)

admin.site.register(Rule, RuleAdmin)
