StormCloud
==========
StormCloud provides a toolkit for simulating all kinds of chaos with third-party service providers. Do you know how your
software would behave if your credit card processor went down, started returning 500s, timed out, returned garbage
responses, or any number of other things? When it happens isn't the time to find out. I'm trying to formalize and make
fully generic scripts I've been using to troubleshoot applications for years through this project.

To be clear, it's a standalone Django project, not an application you add into your own Django project. It will run as
part of testing but it won't become part of your code.

How it works:
=============
A Django middleware will capture all incoming requests except for the admin (or others configured not to be captured)
and if not configured otherwise respond with an empty HTTP 200 response while simultaneously creating a rule for that
request in the database to be configured as necessary.

How to use:
===========
There are a couple possible ways to use it - first is by configuring one or more third-party dependencies to point to
the URL StormCloud is running at INSTEAD of the vendor's own URL. How easy this will be depends on the vendor and their
library, and if you figure one out that isn't in the vendor-examples/ folder please consider contributing what you did
as a pull request so others can benefit.

Second is to set up a man-in-the-middle scenario by overriding DNS in some way. You could add entries in /etc/hosts
(or equivalent) pointing the necessary hostnames for that vendor on the computer running your application, or use a DNS
caching proxy on your local network and make the overrides there (I personally use a MikroTik router and approach it
this way as it takes effect on the whole network.) If you take this approach, you will likely end up overriding some
part of the vendor's library anyway because they will be verifying SSL certificates, and you won't have an SSL
certificate for their domain to allow that verification to pass.

Once it's configured, start up your site locally and begin using it (if you have Selenium or other browser tests for
common paths, this would be a great place to use them), and if you're getting 500s, address them one by one. At this
point all StormCloud is doing is logging what requests are coming in as rules you can configure, and returning an
empty string HTTP 200 response, something you and/or your vendor libraries likely don't expect your third-party vendors
to do. It will create some chaos.

Once you've gotten a representative sample of API actions (checkout processes, card verifications, metrics collections,
etc) logged, the StormCloud Rules admin will give you other choices of actions to take for each individual URL. (URLs
are stored as "Rules" in the Rule model.)


Actions you can take:
---------------------
- Respond with a flat text response (or randomly choose from other flat text responses)
- Return a HTTP 301 Permanent redirect to an address (or randomly choose from a list of addresses)
- Return a HTTP 302 Temporary redirect to an address (or randomly choose from a list of addresses)
- Return a HTTP 500 Internal Server Error
- Perform a live lookup of a remote URL (configured in StormCloud) and pass that along as the response.

"Extra" actions:
----------------
With any action above, you can also add a response delay (specified in milliseconds in the StormCloud admin for that
rule) to see how long waits for third-party API calls can affect your application, and if set highly enough to trigger
timeouts. Adjust your application as necessary to cope with these timeouts and you'll know that if your vendor goes
down you shouldn't go with them.

An extra note about timeouts:
-----------------------------
Timeouts are the more common (in my experience) thing to tune for, but you should also consider cases like being unable
to get DNS resolution of the third-party vendor's domains (this one is tough without a local DNS server that allows
overriding that a domain doesn't exist, and is more easily accomplished through changing the vendor's client library
configuration to point to a domain that legitimately doesn't exist), expired domains, expired SSL certificates, actual
internet failures where no TCP connections go through, etc. Those are out of scope for what StormCloud can provide, as
they live in different OSI layers.
