import time

from django.http import HttpResponse

from rules.models import Rule
from vendors.models import Vendor


class StormCloudMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def vendor_lookup(self, server_name):
        vendors = Vendor.objects.filter(base_url=server_name)
        if vendors.count() > 1:
            raise Exception("More than one vendor for that hostname")

        return vendors.first()

    def rule_lookup(self, vendor, path, verb):
        lookup_kwargs = {}
        if vendor:
            lookup_kwargs['vendor__in'] = vendor

        lookup_kwargs['path'] = path
        lookup_kwargs['verb'] = verb

        rules = Rule.objects.filter(**lookup_kwargs)

        if rules.count() > 1:
            raise Exception("More than one rule for that path / vendor")

        return rules.first()

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        vendor = self.vendor_lookup(request.META['SERVER_NAME'])
        rule = self.rule_lookup(vendor=vendor, path=request.META['PATH_INFO'], verb=request.META['REQUEST_METHOD'])

        if not rule:  # nothing found
            # go ahead and create one with what we know
            rule = Rule.objects.create(vendor=vendor, hostname=request.META['SERVER_NAME'], path=request.META['PATH_INFO'],
                                       verb=request.META['REQUEST_METHOD'])
            return HttpResponse("")  # blank response initially

        # todo: some better reading of GET/POST parameters to make rules more fine-grained, may require architectural changes
        # str(request.GET.dict())
        # str(request.POST.dict())

        if not rule.action:  # no action configured for this URL
            return None  # act normally / return to Django

        # was a delay requested?
        if rule.delay_ms:
            time.sleep(rule.delay_ms / 1000.0)  # convert ms to expected seconds

        if rule.action == 'flat':
            return HttpResponse(rule.flat_response)

        response = HttpResponse('')  # respond with nothing to everything else
        # response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
