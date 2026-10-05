Read-only web coverage, 2026-10-04
===================================

Decision
--------

The existing interactive session supplies working central-API authorization.
Our own OAuth client is unnecessary for supervised browser reads. The public
website client does not provide unauthenticated access or establish a supported
third-party OAuth registration contract. Keep native authorization opaque inside
the browser and feed normalized results to the existing provider-independent
CSV/JSON Lines interchange. No EasyTithe account or integration is required.

People is the strongest first browser-adapter domain: native collection paging,
page-base behavior, disjoint subsequent pages, declared termination and one-person
details were checked. Giving has useful native JSON contracts, but its collection
ignored the attempted ``page=1&limit=25`` bound and exceeded two MiB. Validate its
actual filter/paging contract before implementing a full contribution export.
An API key remains a supported alternative only if an authorized Owner supplies
one. Account/API settings were never revisited.

Coverage boundary
-----------------

The consolidated traversal assessed ninety-two distinct discovered route
families, including aliases, redirects and one external redirect. The final
parent revisit exhausted its queue without link/schema truncation. Seven
additional fixed views were checked: followup assignment, merge selection,
automated tasks, Mailchimp, Planning Center, QuickBooks and the giving landing
page. Their three discovered child links were assessed too; one redirected
outside the account and was not inspected there. That child queue is empty.

Coverage is by page type and distinct query/view variants. Repeated entity links
use at most three representatives per no-query family; this was not a crawl of
every member, transaction or historical event. Raw URLs and identifiers stayed
in the private inspector's working memory. Family labels below distinguish paths
with identical masked display names and belong to this evidence pass only.
They are not current navigation indices after a service restart.

Visited domains include Dashboard; People filters/saved searches and profile
subpages; Tags/history; Events with attendance, out mode, volunteers, plans,
attachments, reports and settings; Giving reports/graphs, overview, batches,
funds, methods and pledges; Forms, entries, filters and previews; followups;
extensions; timeline; and administrative views outside Account. Import landing
pages and add-person/followup views were inspected without submitting forms.

Account/root-settings/API-administration and authentication/consent paths remain
excluded. Save/delete/send/install/import-processing/export-job/download actions
were not executed. Mutation-shaped links without a reviewed view exception
remain action exclusions, rather than being treated as ordinary page reads.
Conditional dialogs and processing flows were examined through code contracts;
no claim is made that every UI interaction or individual record was opened.

Some navigation aliases return a different available view: Groups returns
Dashboard, Songs returns Events, and installed/search extension aliases return
Extensions. These redirects do not by themselves prove permission denial.
The attendance out-mode document returned HTTP 200 and later became interactive,
but sometimes exceeded the twelve-second navigation deadline; its additional
inert read was aborted. Earlier matched traversal also covered this page type.

Runtime read contracts
----------------------

This table records response reductions from native page loading in the
consolidated/final view passes. It does not imply that every declared API route
was invoked. Fixed People probes additionally verified ``GET /api/v2/people``
and a derived person detail. Ninety-one curated central GET templates and
twenty-two exact legacy POST loaders are eligible for observation; templates
are candidates until successfully observed. ``other`` denotes a non-JSON,
non-leading-HTML legacy response, not a validated export envelope.

.. list-table:: Observed native reads
   :header-rows: 1
   :widths: 10 55 10 25

   * - Method
     - Public route template
     - HTTP
     - Reduced format
   * - GET
     - ``/api/v2/attachments``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions/batches``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions/funds``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions/funds/folders``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions/methods``
     - 200
     - json
   * - GET
     - ``/api/v2/contributions/overview``
     - 200
     - json
   * - GET
     - ``/api/v2/emails/history``
     - 200
     - json
   * - GET
     - ``/api/v2/event-instances``
     - 200
     - json
   * - GET
     - ``/api/v2/event-instances/{id}``
     - 200
     - json
   * - GET
     - ``/api/v2/events/calendars``
     - 200
     - json
   * - GET
     - ``/api/v2/features``
     - 200
     - json
   * - GET
     - ``/api/v2/history/{type}``
     - 200
     - json
   * - GET
     - ``/api/v2/integrations``
     - 200
     - json
   * - GET
     - ``/api/v2/integrations/{id}``
     - 200
     - json
   * - GET
     - ``/api/v2/me``
     - 200
     - json
   * - GET
     - ``/api/v2/message-templates``
     - 200
     - json
   * - GET
     - ``/api/v2/people/search``
     - 200
     - json
   * - GET
     - ``/api/v2/people/{id}``
     - 200
     - json
   * - GET
     - ``/api/v2/preferences``
     - 200
     - json
   * - GET
     - ``/api/v2/preferences/{identifier}``
     - 200
     - json
   * - GET
     - ``/api/v2/profile-merges``
     - 200
     - json
   * - GET
     - ``/api/v2/profilefields``
     - 200
     - json
   * - GET
     - ``/api/v2/roles``
     - 200
     - json
   * - GET
     - ``/api/v2/service-plan-templates``
     - 200
     - json
   * - GET
     - ``/api/v2/tags``
     - 200
     - json
   * - GET
     - ``/api/v2/tags/folders``
     - 200
     - json
   * - POST
     - ``/ajax/fundraisers_list``
     - 200
     - html
   * - POST
     - ``/ajax/get_forms_list``
     - 200
     - html
   * - POST
     - ``/ajax/load_form_entries``
     - 200
     - other
   * - POST
     - ``/ajax/load_history_table_text``
     - 200
     - other
   * - POST
     - ``/ajax/pledges_summary``
     - 500
     - http_error
   * - POST
     - ``/ajax/search_event_attendance``
     - 200
     - html
   * - POST
     - ``/ajax/search_event_attendance``
     - 200
     - too_large
   * - POST
     - ``/ajax/search_followups``
     - 200
     - html

Giving details and limits
-------------------------

``GET /api/v2/contributions`` returns ``api``/``data`` JSON envelopes. Reviewed
row fields include ``id``, ``person_id``, ``fund_id``, ``batch_id``, ``amount``,
``paid_on``, ``method`` and ``note``. Amounts/dates/notes/IDs were never returned;
only their types were reduced. Native Dashboard reads have two ``filter[...]``
parameters whose inner identifiers remain hidden by the curated reducer. Exact
filter encoding, stable ordering and complete collection termination remain
unverified. Do not repeat the failed generic paging probe unchanged.

``/contributions/overview`` uses a numeric ``year`` query and a summary envelope.
``/contributions/batches`` accepts native ``page`` and ``sort`` queries and has
``pagination`` with ``current_page``, ``last_page``, ``per_page``, ``count`` and
``total`` field types. Omitting ``page`` produced an unpaginated collection.
Funds, fund folders and payment methods also returned JSON successfully.
Financial totals and numeric financial metadata are always type-only.

Legacy Giving uses ``POST /ajax/payments_search_results`` and HTML fragments;
a prior matched person-Giving view observed HTTP 200. This is separate from the
newer central JSON path. Pledge summary returned HTTP 500, and one native
attendance search exceeded the two-MiB reducer bound. These are recorded limits,
not successful schema/export validation.

Native billing-header requests received HTTP 403. Their bodies were excluded,
and this failure does not deny the successful contribution reads. API-v2 rate
limits and snapshot consistency were not established. Dashboard keepalive was
healthy across the investigation, but this does not establish access-token
lifetimes or prove an unattended refresh contract. No refresh was forced and
independent OAuth onboarding remains unverified.

Export code includes job-creating POSTs, asynchronous completion/polling and
email delivery helpers. Those workflows were assessed statically and were not
started. A browser adapter should read structured collections directly, use
explicit bounds, fail on incomplete domains and preserve custom fields in the
raw interchange where mapping is not yet established. Forms and several legacy
pages need their HTML/custom response contracts validated separately.

Static source provenance
-------------------------

The primary generated client bundle is
https://main.ddgv4rlrmu56c.amplifyapp.com/assets/main-BkBiSYb4.js,
624,009 bytes, SHA-256
``b9f0aed2843b52365a72a97c92cef528c0f139fabd0cd4abf07f63bf7868e662``.
Its initial literal scan found 117 GET declarations, with eighty-six eligible
read templates after authentication, linking/billing and credential exclusions.

Giving and Dashboard also load a separate observed Breeze application script,
1,690,117 bytes, SHA-256
``75d0e704aecc3e9249fe8ee38f75f4a09a9b080f3fed83216007e7a680dfbe1d``.
Its origin remains masked; it was read with credentials omitted. Its Giving
chunks reveal contribution/overview/batch calls absent from the main generated
client. Ten additional Dashboard chunks were inspected as bounded static source.
Source references and nearby identifiers establish implementation candidates,
not backend side-effect guarantees. Dynamic expressions, conditional routes
and internal Webpack modules are not fully enumerable by a literal scanner.

Route-family evidence
---------------------

The table retains masked requested paths only. Redirect destinations are shown
when observed. A late/failed navigation is recorded even where another pass
successfully covered the same generic page type.

.. list-table:: Consolidated discovered families
   :header-rows: 1
   :widths: 10 45 45

   * - Family
     - Requested shape
     - Disposition / observed destination
   * - 0
     - ``/``
     - ready: /r/dashboard
   * - 1
     - ``/dashboard``
     - ready: /r/dashboard
   * - 2
     - ``/people``
     - ready: /people
   * - 3
     - ``/people/filter``
     - ready: /people/filter
   * - 4
     - ``/people/saved``
     - ready: /people/saved
   * - 5
     - ``/r/people``
     - ready: /people
   * - 6
     - ``/r/tags``
     - ready: /r/tags
   * - 7
     - ``/r/events``
     - ready: /r/events
   * - 8
     - ``/events/blockout_dates``
     - ready: /events/blockout_dates
   * - 9
     - ``/followups``
     - ready: /followups
   * - 10
     - ``/followups/search``
     - ready: /followups/search
   * - 11
     - ``/history``
     - ready: /r/history/people
   * - 12
     - ``/history/email``
     - ready: /history/email
   * - 13
     - ``/groups``
     - ready: /r/dashboard
   * - 14
     - ``/songs``
     - ready: /r/events
   * - 15
     - ``/extensions``
     - ready: /extensions
   * - 16
     - ``/extensions/installed``
     - ready: /extensions
   * - 17
     - ``/extensions/search``
     - ready: /extensions
   * - 18
     - ``/payments/reports``
     - ready: /payments/reports
   * - 19
     - ``/payments/reports/list_people``
     - ready: /payments/reports/list_people
   * - 20
     - ``/payments/reports/graph``
     - ready: /payments/reports/graph
   * - 21
     - ``/forms``
     - ready: /forms/all
   * - 22
     - ``/timeline/{segment}``
     - ready: /timeline/{segment}
   * - 23
     - ``/roles/all``
     - ready: /roles/all
   * - 24
     - ``/admin/members``
     - ready: /admin/members
   * - 25
     - ``/admin/profile_mapping``
     - ready: /admin/profile_mapping
   * - 26
     - ``/admin/users``
     - ready: /admin/users
   * - 27
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 28
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 29
     - ``/{segment}/{segment}/{segment}``
     - ready: /{segment}/{segment}/{segment}
   * - 30
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 31
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 32
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 33
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 34
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 35
     - ``/followups/{segment}``
     - ready: /followups/{segment}
   * - 36
     - ``/people/{segment}``
     - ready: /people/{segment}
   * - 37
     - ``/r/dashboard``
     - ready: /r/dashboard
   * - 38
     - ``/payments``
     - ready: /payments/reports
   * - 39
     - ``/people/view/{segment}``
     - ready: /people/view/{segment}
   * - 41
     - ``/{segment}/internal``
     - ready: /{segment}/internal
   * - 42
     - ``/extensions/{segment}``
     - ready: /extensions/{segment}
   * - 43
     - ``/people/{segment}/notes``
     - ready: /people/{segment}/notes
   * - 44
     - ``/people/{segment}/tags``
     - ready: /people/{segment}/tags
   * - 45
     - ``/people/view/{segment}/message``
     - ready: /r/dashboard
   * - 46
     - ``/{segment}/recurring``
     - ready: /{segment}/recurring
   * - 47
     - ``/tags/view/{segment}``
     - ready: /tags/view/{segment}
   * - 48
     - ``/r/history/tags``
     - ready: /r/history/tags
   * - 50
     - ``/followups/{segment}``
     - ready: /followups/{segment}
   * - 51
     - ``/r/history/people``
     - ready: /r/history/people
   * - 52
     - ``/r/history/events``
     - ready: /r/history/events
   * - 53
     - ``/history/text``
     - ready: /history/text
   * - 54
     - ``/history/people``
     - ready: /r/history/people
   * - 55
     - ``/history/tags``
     - ready: /r/history/tags
   * - 56
     - ``/history/events``
     - ready: /r/history/events
   * - 57
     - ``/payments/overview``
     - ready: /r/payments/overview
   * - 58
     - ``/payments/batches``
     - ready: /r/payments/batches
   * - 59
     - ``/payments/funds``
     - ready: /r/payments/funds
   * - 60
     - ``/payments/pledges``
     - ready: /payments/pledges
   * - 61
     - ``/payments/methods``
     - ready: /r/payments/methods
   * - 62
     - ``/forms/all``
     - ready: /forms/all
   * - 63
     - ``/forms/entries/{segment}``
     - ready: /forms/entries/{segment}
   * - 64
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 79
     - ``/{segment}/methods``
     - ready: /{segment}/methods
   * - 80
     - ``/{segment}/{segment}``
     - ready: /{segment}/{segment}
   * - 81
     - ``/{segment}/{segment}``
     - outside_account_redirect
   * - 82
     - ``/people/view/{segment}/groups``
     - ready: /people/view/{segment}/groups
   * - 83
     - ``/people/view/{segment}/tags``
     - ready: /people/view/{segment}/tags
   * - 84
     - ``/people/view/{segment}/attendance``
     - ready: /people/view/{segment}/attendance
   * - 85
     - ``/people/view/{segment}/payments``
     - ready: /people/view/{segment}/pledges
   * - 86
     - ``/people/view/{segment}/notes``
     - ready: /people/view/{segment}/notes
   * - 87
     - ``/people/view/{segment}/followups``
     - ready: /people/view/{segment}/followups
   * - 88
     - ``/people/view/{segment}/forms``
     - ready: /people/view/{segment}/forms
   * - 89
     - ``/people/view/{segment}/{segment}``
     - ready: /people/view/{segment}/{segment}
   * - 91
     - ``/events/view/{segment}``
     - ready: /events/view/{segment}
   * - 92
     - ``/r/payments/overview``
     - ready: /r/payments/overview
   * - 93
     - ``/r/payments/batches``
     - ready: /r/payments/batches
   * - 94
     - ``/r/payments/funds``
     - ready: /r/payments/funds
   * - 95
     - ``/r/payments/methods``
     - ready: /r/payments/methods
   * - 96
     - ``/forms/entries/{segment}/filter``
     - ready: /forms/entries/{segment}/filter
   * - 97
     - ``/forms/view/{segment}``
     - ready: /forms/view/{segment}
   * - 98
     - ``/events/people/{segment}``
     - ready: /events/people/{segment}
   * - 99
     - ``/events/{segment}/plan``
     - ready: /events/{segment}/plan
   * - 100
     - ``/events/reports/{segment}``
     - ready: /events/reports/{segment}
   * - 102
     - ``/events/{segment}/{segment}``
     - ready: /events/{segment}/{segment}
   * - 103
     - ``/events/volunteers2/{segment}``
     - ready: /events/volunteers2/{segment}
   * - 104
     - ``/events/settings/{segment}``
     - ready: /events/settings/{segment}
   * - 105
     - ``/events/people/{segment}/out``
     - request_failed
   * - 106
     - ``/events/{segment}/attachments``
     - ready: /events/{segment}/attachments
   * - 107
     - ``/people/view/{segment}/pledges``
     - ready: /people/view/{segment}/pledges
   * - 108
     - ``/events/{segment}/{segment}``
     - ready: /events/{segment}/{segment}
   * - 109
     - ``/events/volunteers2/{segment}/{segment}``
     - ready: /events/volunteers2/{segment}/{segment}

Expanded ATLAS hardness report
-------------------------------

Privacy/security: synthetic fixtures verify hidden records/IDs/token values,
unknown-field masking, numeric financial redaction, request-filter privacy,
Account/frame exclusions, opaque header reuse and bounded inert HTML/static
source reads. Only fixed reviewed requests and private observed-link indices
are accepted; no arbitrary browser evaluation/request interface was added.

Failures: exact BiDi ``no such request`` cancellation is handled without replay;
other guard failures stop inspection. Navigation readiness is matched and bounded;
late/unverified documents are not silently counted as successful navigation.
External redirects stop before DOM inspection. Recovered parent branches and
persisted frontier metadata prevented an empty queue from hiding interrupted work.
HTTP errors, oversized bodies and discovery/sample truncation remain explicit.

Concurrency/load: control operations are serialized, keepalive runs every two
minutes, and live probes use request spacing and total deadlines. Record links
are grouped before retention; registries, response bytes, frame traversal,
schema depth, samples and inline/static source sizes are bounded. No production
load or API-v2 rate-limit claim is made.

Verification: ``uv tool run --from uv==0.12.22 bash scripts/check.sh`` passed
Ruff, type checking, 364 tests (one live test skipped), required coverage,
dependency audit and wheel/sdist builds. The browser-inspection Python tests
account for 122 passing cases. 94 synthetic browser checks passed for response/request privacy, native
probes, static source, inert HTML, session maintenance and list controls. No account mutations, OAuth
registration, export jobs or production data files were created.

Follow-ups: implement the supervised browser adapter with the established
People contract; validate contribution filters/paging and legacy Forms envelopes
before advertising complete export coverage. Request independent OAuth access
only if unattended operation becomes a requirement and vendor onboarding is
confirmed through an authorized route outside the excluded Account page.
