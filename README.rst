PyBreezeChMS
============

Python 3.14 interface to the BreezeChMS REST API. Runtime and CI use Python
3.14.8. Requests is installed automatically with the package.

Installation
------------

.. code-block:: sh

   uv pip install 'git+https://github.com/firestrand/pyBreezeChMS.git@main'

Getting started
---------------

Set BREEZE_API_KEY in your runtime environment.

.. code-block:: python

   import os
   from breeze import breeze

   with breeze.BreezeApi(
       breeze_url='https://your-subdomain.breezechms.com',
       api_key=os.environ['BREEZE_API_KEY'],
   ) as client:
       people = client.get_people()

Clients own default sessions and support close() and context managers. Injected
transports remain caller-owned and must implement HttpConnection. The client
verifies TLS, rejects redirects, bounds responses to 16 MiB by default, uses a
60-second inactivity timeout, a checked elapsed budget, and account pacing.
It does not retry writes. Blocked synchronous requests cannot be forcibly
interrupted; see README.md for budget and coordination limits. Use pagination for
larger reports. Dry-run methods return None without making Breeze requests.
BreezeError reports HTTP, transport, malformed-response and API failures.

Development
-----------

Clone the core repository and install uv 0.12.22. Run scripts/check.sh and
scripts/check-artifacts.sh for locked checks, offline tests, vulnerability
scanning, builds, and installation smoke tests. See README.md for the Python 3
legacy EasyTithe migration, and docs/maintenance.rst for the
standards audit.
Provider-independent CSV/JSON Lines exchange, optional dotenv support, installed
preview/plan/apply commands and durable recovery are in docs/data-exchange.rst.
Populate private .env using .env.example for Breeze URL/key configuration.
The supported workflow has no EasyTithe dependency. These CLI changes are local
and unreleased. Opt-in read probes are in docs/provider-contracts.rst.
Interactive Firefox login and private request-metadata inspection are described
in docs/browser-inspection.rst. Browser tooling is development-only.

Compatibility
-------------

Version 2.0 requires Python 3.14 and Requests >=2.34.2,<3. Older interpreters and
Python 2-only adapters are removed. URLs require HTTPS Breeze subdomains.
Query values are encoded. Endpoint constants are string-compatible StrEnum
values. Operational errors are sanitized and preserve their exception causes.

License
-------

Apache 2.0. See LICENSE.
