import logging
import time

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect

from rules.models import Rule
from vendors.models import Vendor

logger = logging.getLogger(__name__)


class StormCloudMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def vendor_lookup(self, server_name):
        """Currently goes off of hostname ONLY, but ideally the path could be a component, particularly when the
        hostname is localhost. However, since it's stored on the vendor as a complete base_url including a hostname..."""
        vendors = Vendor.objects.filter(base_url=server_name)
        if vendors.count() > 1:
            logger.error("More than one vendor found for hostname %s", server_name)
            raise Exception("More than one vendor for hostname %s" % server_name)

        return vendors.first()

    def rule_lookup(self, vendor, path, verb):
        lookup_kwargs = {}
        if vendor:
            lookup_kwargs['vendor__in'] = vendor

        lookup_kwargs['path'] = path
        lookup_kwargs['verb'] = verb

        rules = Rule.objects.filter(**lookup_kwargs)

        if rules.count() > 1:
            logger.error("More than one rule for path %s / vendor %s", path, vendor)
            raise Exception("More than one rule for path %s / vendor %s" % (path, vendor))

        return rules.first()

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # bypass for Django admin
        if request.META['PATH_INFO'].startswith('/admin/'):
            logger.debug("StormCloud Ignoring Admin URL %s" % request.META['PATH_INFO'])
            return self.get_response(request)  # act normally / return to Django

        logger.info("StormCloud received request to\n URL: %s \n Hostname: %s \n Verb: %s",
                        request.META['PATH_INFO'], request.META['SERVER_NAME'], request.META['REQUEST_METHOD'])
        vendor = self.vendor_lookup(request.META['SERVER_NAME'])
        logger.debug("  Determined vendor as %s" % vendor)
        rule = self.rule_lookup(vendor=vendor, path=request.META['PATH_INFO'], verb=request.META['REQUEST_METHOD'])

        if not rule:  # nothing found
            # go ahead and create one with what we know
            rule = Rule.objects.create(vendor=vendor, hostname=request.META['SERVER_NAME'], path=request.META['PATH_INFO'],
                                       verb=request.META['REQUEST_METHOD'])
            logger.info("  No rule was found for URL %s / Vendor %s / Hostname %s / Verb %s, one was created.",
                        request.META['PATH_INFO'], vendor, request.META['SERVER_NAME'], request.META['REQUEST_METHOD'])
            return HttpResponse("")  # blank response initially

        # todo: some better reading of GET/POST parameters to make rules more fine-grained, may require architectural changes
        # str(request.GET.dict())
        # str(request.POST.dict())

        if not rule.action:
            logger.info("  No action was found for URL %s / Vendor %s / Hostname %s / Verb %s, passing request to Django to handle.",
                        request.META['PATH_INFO'], vendor, request.META['SERVER_NAME'], request.META['REQUEST_METHOD'])
            return self.get_response(request)  # act normally / return to Django

        # was a delay requested?
        if rule.delay_ms:
            logger.info("  StormCloud initiating %s ms delay", rule.delay_ms)
            time.sleep(rule.delay_ms / 1000.0)  # convert ms to expected seconds

        if rule.action == 'flat':
            logger.info("  StormCloud returning flat response.")
            return HttpResponse(rule.flat_response)

        elif rule.action == 'live':
            logger.info("  StormCloud returning live response.")
            return HttpResponse(rule.live_response(get=request.GET.copy(), post=request.POST.copy(),
                                                   verb=request.META['REQUEST_METHOD']))

        elif rule.action == '301':
            url = rule.flat_response  # if not stored, if there are multiple configured URLs logging could report sending to the wrong URL
            logger.info("  StormCloud returning 301 response to %s", url)
            return HttpResponsePermanentRedirect(url)  # treat the text field as a URL field

        elif rule.action == '302':
            url = rule.flat_response  # if not stored, if there are multiple configured URLs logging could report sending to the wrong URL
            logger.info("  StormCloud returning 302 response to %s", url)
            return HttpResponseRedirect(url)

        else:
            try:
                int(rule.action)
            except ValueError:  # not an integer
                logger.error("  StormCloud could not convert action into an integer, so it can't infer what you want to "
                             "do. Should an additional action be written into stormcloud.middleware.StormCloudMiddleware ?")
                pass
            else:
                logger.info("  StormCloud returning %s response", rule.action)
                return HttpResponse('', status=int(rule.action))

        response = HttpResponse('')  # respond with nothing to everything else
        # response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
