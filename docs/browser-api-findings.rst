Browser API investigation, updated 2026-10-04
=============================================

Finding and decision
--------------------

The signed-in browser can read the central REST API using the website's native
Authorization header. People paging and a one-person detail read succeeded;
Giving contribution, overview, batch, fund/folder and method reads also succeeded.
An independently registered OAuth client is not required for this supervised
browser path. Public website JavaScript identifies contracts; access still
requires the operator's authenticated session and its permissions.

Use an experimental browser-session adapter as the practical next transport for
this non-Owner account. Keep authentication and provider response shapes separate
from the existing CSV/JSON Lines interchange. EasyTithe is not required and no
EasyTithe integration is proposed. The documented API-key adapter remains an
alternative if an authorized Owner supplies a key; it cannot unblock this account
by itself. Independent OAuth registration/onboarding remains unverified.

The expanded investigation and its remaining contract limits are recorded in
``docs/browser-route-coverage.rst`` and ``docs/browser-session-investigation.rst``.
No OAuth application, grant, account change or data export was created.

Initial public-source evidence, 2026-10-03
------------------------------------------

Inspected 29 loaded public JavaScript assets and six directly referenced
application chunks: OAuth, OAuthAuthorize, Login, People, Events and Tags.
The main bundle was 624,009 bytes, SHA-256
``b9f0aed2843b52365a72a97c92cef528c0f139fabd0cd4abf07f63bf7868e662``.
It contained 595 path-literal references and 284 directly matched HTTP method/path
declarations. These counts include writes, duplicate routes, and frontend paths;
they are not counts of verified or available read endpoints.

Primary code sources:

* https://main.ddgv4rlrmu56c.amplifyapp.com/assets/main-BkBiSYb4.js
* https://main.ddgv4rlrmu56c.amplifyapp.com/assets/OAuth-DWbF_oby.js
* https://main.ddgv4rlrmu56c.amplifyapp.com/assets/OAuthAuthorize-CUsc7j0e.js
* https://main.ddgv4rlrmu56c.amplifyapp.com/assets/Login-vOorYZni.js

Source was fetched as text with credentials omitted and never executed by the
inspector. Only bounded code-derived metadata was returned; source bodies,
inline scripts, authentication values, browser storage and account records were
not retained. Public CDN/service origins are provenance, not account origins.
Summaries in the ignored private browser directory contain static code metadata.

The following authentication failure describes the initial pass, before the
successful session investigation on October 4. The prior read-only pass observed
cookie/CSRF AJAX calls. During this pass,
navigation to the newer People application produced an account-origin AJAX GET
with an Authorization header. Its value was not read and the request ended with
a fetch error, so this is not proof of a successfully authorized API call.
The browser then returned to a login screen. Capture was paused and another
interactive login was requested; public code inspection continued without login.
The reason for the authentication transition remains unverified.

The account/API-key documentation remains at
https://support.breezechms.com/hc/en-us/articles/360001324153-API-Advanced-Custom-Development
and https://app.breezechms.com/api. An official documentation search did not
establish a public v2/OAuth onboarding contract. Search results for other products
named Breeze were excluded. No support message was sent.

Service paths
-------------

**Documented account API:** ``https://<account>.breezechms.com/api`` with an
API key. This is the transport implemented by the supported library.

**New application API:** the bundle's ``apiHost`` is
``https://api.breezechms.com/api/v2``. The bundled client declares REST reads and
writes for people, tags, calendars, event instances, funds, users and other
features. Bundle presence does not establish this account's permissions or
third-party eligibility. Generated request declarations identify methods and
query names; they do not supply a complete validated response schema.

**Authentication bridge:** ``helmHost`` is
``https://api.breezechms.com/helm/v1``. The bundle also declares direct POST helpers
for ``/auth/token/breeze`` with a ``token`` body field, and
``/auth/access_token`` with ``client_id``, ``grant_type``, ``scope`` and
``session_token`` body fields. The literal grant type is ``session_token``.
This establishes token-exchange code in the website, not authorization to reuse
its bundled client configuration. Exact runtime host binding and the bridge's
external access contract still need verification.

**Legacy browser AJAX:** account-origin ``/ajax/...`` calls use browser state.
The earlier pass saw cookie/CSRF requests, including blocked POST
``/ajax/get_forms_list``. Newer frontend code also uses an Authorization header
on an AJAX request. Header styles can differ between application generations.
Do not assume a single auth mechanism for the entire account website.

Read candidates from exact bundled declarations
-----------------------------------------------

Paths below are relative to the new API client. ``{id}`` describes a dynamic
segment; real identifiers are reduced inside the browser and never returned. Query keys are code identifiers only.

.. list-table:: Representative candidate reads
   :header-rows: 1
   :widths: 35 65

   * - GET path
     - Declared query parameters
   * - ``/people``
     - ``collection_filter``, ``exact``, ``ids_only``, ``limit``, ``no_limit``,
       ``page``, ``pageSize``, ``sort``
   * - ``/people/search``
     - ``filters``, ``ids_only``, ``no_limit``, ``page``, ``pageSize``, ``sort``
   * - ``/people/{id}``
     - ``include``
   * - ``/tags``
     - ``filter``, ``page``, ``pageSize``, ``sort``
   * - ``/tags/folders``
     - ``filter``, ``sort``
   * - ``/tags/people/{id}``
     - ``people_ids_only``
   * - ``/event-instances``
     - ``filter``, ``has_service_plan``, ``has_set_list``, ``page``, ``pageSize``,
       ``sort``
   * - ``/events/calendars``
     - ``filter``
   * - ``/events/{id}``
     - No query keys matched in its declaration
   * - ``/contributions/funds``
     - ``filter``
   * - ``/people/export-config``
     - No query keys matched in its declaration

Pagination appears to use ``page`` and ``pageSize`` for several list endpoints.
Page numbering, allowed sizes, response envelopes, termination conditions,
stable ordering and consistency during concurrent edits remain unknown. Do not
infer these from the legacy API. Prefer bounded pages and explicit stable sort
over the bundle's ``no_limit`` option when validating later.

Funds reads were found, but a complete contribution-history export and form-entry
reads were not established in the scanned newer-client declarations. The older
documented API and legacy UI remain coverage candidates. Missing a declaration
in these assets does not prove the backend lacks an endpoint. ``export-config``
is configuration; it is not evidence of an export download API. No export file
was requested and the Giving page remains unverified.

OAuth evidence
--------------

The main bundle declares:

* GET ``/oauth/authorize``: ``client_id``, ``code_challenge``,
  ``code_challenge_method``, ``redirect_uri``, ``response_type``, ``state``,
  ``subdomain``.
* POST ``/oauth/accept``: ``code`` query parameter.
* GET ``/oauth/callback``: ``code`` and ``state``.
* GET ``/oauth/token``: ``client_id``, ``client_secret``, ``code``,
  ``code_verifier``, ``grant_type``.

The OAuthAuthorize chunk calls ``oAuthAcceptRequest``. This is additional evidence
of an application consent path, beyond generic OAuth text in dependencies.
The inspector did not navigate these routes or accept consent.

Application-management declarations include GET
``/api-auth/applications/{id}``, GET/POST ``/api-auth/application-requests`` and
GET/DELETE token-management routes. These suggest authorized-application/request
management. They do not establish a self-service client-registration endpoint.
Token-management responses were not requested because they can contain secrets.

The declared GET token exchange needs special verification. OAuth 2.0's token
endpoint normally requires POST (RFC 6749 section 3.2:
https://www.rfc-editor.org/rfc/rfc6749#section-3.2). The bundle's declaration is
evidence of website code, not a standards-compliant external contract. Do not
copy the GET/query-secret pattern into a new consumer. Client secrets, codes and
verifiers must never enter logs, command-line arguments or saved request URLs.

Anonymous public-discovery checks returned HTML rather than JSON at
``/.well-known/oauth-authorization-server`` and
``/.well-known/openid-configuration`` on the central API host.
``/api/v2/openapi.json`` returned HTTP 404. These checks did not establish
published discovery metadata or an OpenAPI document at those locations; they
do not prove that none exists elsewhere. Failed response bodies were not read.

Options and recommended order
-----------------------------

1. **Documented API-key transport:** keep it as the default for unattended
   exports. Its current support/coverage is already represented in the library.
2. **Registered OAuth client for v2:** investigate first for a durable alternate
   integration. Confirm external client provisioning, redirect URI rules, scopes,
   token exchange method, refresh/revocation, and whether access is account-wide
   or tied to a user's role. Use our own registration if available.
3. **Interactive browser transport:** useful for read-only reconnaissance and
   gaps. Reuse the logged-in browser to issue explicitly reviewed reads and
   locally summarize schemas; do not extract tokens into environment files or
   reuse a website client ID. Handle re-login and CSRF inside the browser.
4. **Website token bridge:** the least understood option. Its session-token
   exchange and internal client configuration need a supported external-use
   contract before implementing an unattended client.

Owner restriction and client provisioning, 2026-10-04
-----------------------------------------------------

The operator confirmed that the signed-in user is not the Account Owner and
excluded Manage Account and API settings from all further inspection. Capture
was paused. Those navigation labels and the Account-menu fallback were removed;
the inspector rejects account/settings pages before reading DOM or sources and
blocks their requests while guarded capture is active. No account setting,
application registration or consent was changed. The browser is left under
operator control; public research does not require navigating that page.

A fresh anonymous fetch rechecked the three public OAuth-related bundles; main
matched its previously recorded SHA-256. Main contains the identifier
``createApiApplicationRequest`` and the previously observed POST
``/api-auth/application-requests``. This establishes an application-request
operation, not issuance of an OAuth client ID/secret. No registration request
was sent. Regex identifier matching cannot prove that another provisioning
mechanism is absent.

The official Breeze `API development article
<https://support.breezechms.com/hc/en-us/articles/360001324153-API-Advanced-Custom-Development>`_
describes API keys obtained by Account Owners. The public `Tithely access page
<https://docs.tithe.ly/reference/introduction>`_ describes requested access and
public/private API keys; its `setup guide
<https://docs.tithe.ly/reference/setup>`_ requires Tithely test and live accounts.
These pages do not document registering a third-party Breeze v2 OAuth client.
That portal should not be assumed to provision Breeze clients.

Draft provisioning questions (not sent)
---------------------------------------

We are developing a Python 3 exporter that reads authorized Breeze data into
consumer-independent CSV/JSONL. Does Breeze support third-party OAuth clients
for ``https://api.breezechms.com/api/v2``? If so:

* How do we register our own client, and does provisioning require an Account
  Owner, a developer program or vendor approval? Is a test tenant available?
* Are authorization-code flow, S256 PKCE and loopback redirects supported for
  a local CLI? Must the client be public or confidential?
* What are the documented authorization/token endpoints and exchange methods?
  The website bundle declares a GET token call; is that internal-only?
* Which read scopes cover people, tags, events, contributions and form entries?
  Are permissions constrained by the consenting user's role?
* Are offline access, refresh-token rotation, expiry, revocation and unattended
  operation supported? What pagination and rate-limit contracts apply?

Do not include account URLs, credentials, tokens or production records in this
inquiry. Client provisioning remains unresolved; no OAuth environment variables
or implementation are added until the supported contract is known.

Next validation on ordinary pages
---------------------------------

* Resolve supported external client provisioning through public documentation
  or a separately authorized vendor inquiry. Do not revisit account/API settings.
* Trace one People list load to bind the real service origin, client and request
  parameters. The bundled GET list declaration is a candidate, not permission
  to replay arbitrary GETs. The inspector now blocks known OAuth grant and
  impersonation GET routes as well as writes.
* Permit only specifically reviewed read requests. If authenticated response
  inspection is added, reduce records immediately in memory to approved schema
  names/types and bounded counts; do not persist provider bodies or fixtures.
* Validate pagination with two small pages, a stable sort, empty-page behavior
  and expiry handling. Record only compatibility results.
* Resolve Giving's redirect and compare transaction/form export coverage against
  the documented API before choosing any new adapter.

ATLAS hardness report
---------------------

Privacy: static assets only, exact observed CDN allowlist, omitted credentials,
no inline scripts or storage values, same-origin dependency restrictions,
generic route placeholders, no source snippets, and bounded metadata output.
An early lexical-snippet approach was removed because nested template strings
made its masking unreliable. Final output uses structural matches only.

Standards: the Python standard and tooling guide were read. No JavaScript-specific
standard or research-specific workflow guide was found in the required standards
library; no substitute policy was invented. The small browser-only JavaScript
scanner was checked in the installed Firefox runtime using fixed synthetic input.

Compatibility: asset indices are stable within a document as new imports load;
navigation creates a new document/catalog. Match the filename and SHA-256 when
comparing observations. Request methods are matched directly against their URL
declaration; nearby methods/property names remain explicitly labeled approximate.
Regex extraction is not a full JavaScript parser and cannot establish server
behavior or response models. Directly referenced dependencies are limited to
one hop, sources to 12 MiB, and route references to 700 with truncation reported.

Verification: synthetic browser checks verify static URL selection, omitted
credentials, zero account network traffic, redaction of secret values and IDs,
exact-method matching, parameter-name extraction and absence of source snippets.
They also verify stable indices and revalidation of cached asset locations.
Python tests cover invalid asset/dependency input and inspection without login
capture, plus known GET grant/impersonation blocking. Full local gate and artifact
verification results are recorded in browser-inspection.rst.

Pass: a materially better map of API/auth options and a reusable static-source
inspector. Remaining limits: no authenticated v2 acceptance test, no OAuth client
registration/consent, no token exchange, and no production export download.
