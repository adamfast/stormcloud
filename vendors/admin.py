# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from vendors.models import *


class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url')

admin.site.register(Vendor, VendorAdmin)
