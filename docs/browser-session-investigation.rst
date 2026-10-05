Browser-session investigation
=============================

Expanded traversal GOTCHA, 2026-10-04
-------------------------------------

The operator requested exhaustion of pages and subpages except Account. Expand
discovery from the six initial navigation links to same-account links observed
in ordinary documents and approved same-origin frames. Keep raw URLs/identifiers
only in the private inspector's working memory; return generic route shapes,
indexes, query-key names and fixed eligibility categories, never link labels or
record values. Check frame URLs before reading their DOM; do not inspect an
Account/settings/API-administration frame. Reject cross-origin, credential-
bearing URLs, authentication/consent, destructive GETs and download/job actions.
Retain a bounded registry of observed links for navigation; no arbitrary URL
or script input. All navigation requires the write guard. Inspect reachable
page families and their subpage/view variants, grouping repeated entity IDs
without persisting them. Track observed, investigated, excluded and unresolved
route families so exhaustion can be assessed against the actual frontier.
Do not call the investigation exhaustive while a reachable unreviewed family
or necessary read-loader contract remains open. Rendering forms is not proof
of mutation: review mutation-shaped view routes individually before access.

Traversal pass one reached forty-five page/view variants. Its dense record
links exhausted the initial private URL registry and link scan caps; remaining
work cannot be called exhausted. Increase the observed-link scan to twenty
thousand with structural grouping before retention (at most three representative
URLs per generic no-query route family), while preserving explicit truncation.
Keep distinct query variants as separate candidates. Restore the pending frontier
by revisiting parent views after instrumentation changes; no record URL is saved.

Read-loader review from those pages: permit the exact native POST paths
``list_filtered_people``, ``people_tag_list``, ``search_followups``,
``load_form_entries``, ``show_entry``, ``get_person_from_id``,
``get_family_id_by_person_id``, ``get_profile_fields_json``,
``load_archived_people``, ``load_archived_forms``,
``get_form_json_by_url_slug``, ``grouped_payment_details`` and
``payment_details_by_payment_id`` under ``/ajax/``. The inline declarations
separate these reads from filter persistence, assignments, form-entry edits,
profile synchronization and contribution mutations. Observe native loading only;
there is no arbitrary POST replay or arbitrary record-ID input. Summarize their
responses with the same in-browser byte/depth/field limits; never return body
values. Read intent is frontend evidence, not a backend side-effect guarantee.

Public route frontier: some preview documents contain no application navigation.
Register a fixed list of ordinary page paths declared by the inspected public
client route registry, plus previously observed main pages, on the same account
origin. Candidate routes remain separate from observed links in evidence. There
is no caller-supplied route/URL. Require guarded navigation and retain Account,
authentication and action exclusions. Visiting a declared route can establish
availability, redirect, error or permission limits; public declaration alone
is not account coverage. This includes administrative view routes outside the
excluded Account area under the operator's expanded all-pages request; never
change roles, users, permissions or mappings.

Expand native response observation to the generated client's reviewed GET route
templates, rather than only the original six collections. The unchanged public
bundle declares 117 literal GET contracts; eighty-six remain after excluding
authentication, identity transitions, account billing/linking and credential
operations. Match static segments and bounded dynamic segments against this
fixed vocabulary, returning the public template (never the actual record ID).
Do not issue extra API requests. Keep byte/schema bounds and test private IDs,
unreviewed routes, alternate origins and authentication exclusions first.

Navigation verification correction: a timed delay still sometimes attributes
the previous document to a requested route. Subscribe to the browser's load
event and match its navigation identifier before reducing a newly requested
document. Bound the wait to twelve seconds; retain write guarding and report
an unverified navigation on timeout rather than counting it as coverage. Store
only transient navigation identifiers, not event URLs or document data.

The public client declares ``/people/saved`` as a saved-search view. Permit only
its exact query-free GET page, which the generic save-prefix heuristic otherwise
blocks. POSTs and action-query variants remain blocked. This is a reviewed view
exception, not permission to invoke saved-search mutations.

Use either matching DOMContentLoaded or load readiness: external frames/assets
can leave full load pending even when the inspected document is ready. The
fixed reducer inspects that document only after its matching readiness event;
asynchronous data loaders still require subsequent response observations.

Numeric-value privacy correction for broad schema observation: emit bounded
pagination integers only in root ``meta``/``pagination`` envelopes or reviewed
request paging fields. A record/custom field called ``count`` or ``total`` is
still record data and must return only its type. Nested filter objects do not
inherit request-paging value permission. Synthetic fixtures cover this boundary.

Frame response observation: preload in the isolated browser's document realms,
but check exact account origin and decoded Account/authentication exclusions
before installing any hooks. The session contains only this inspection window.
Reduce schemas from approved same-origin frames with a four-level, thirty-two-
frame traversal cap and a twenty-summary aggregate cap; report truncation.
Pause must stop hooks in every approved reachable frame and remove the preload.
Never access an excluded frame's DOM or observer. Cover these exclusions,
aggregation caps and cleanup with synthetic browser fixtures before live use.

The first verified traversal found an overbroad exclusion: event configuration
views contain a ``settings`` path segment, but are outside Account. Retain root
settings aliases and every Account/API-administration path exclusion; permit
ordinary event settings view navigation with all writes still blocked.

Further native read declarations distinguish ``get_notifications`` from
``update_notifications``, and history text loading, fundraiser/pledge summaries,
event chart loading and attendance searches from their save/delete operations.
Permit these exact loader POST paths only, retaining the cache-query restriction.
Response sinks and source declarations are read-intent evidence; do not claim
backend side-effect guarantees. Do not replay them with invented record IDs.

Final view and Giving checks GOTCHA, 2026-10-04
-----------------------------------------------

Goal: close read-only page-family gaps and determine the contribution collection
response contract. Review only exact query-free GET view routes for installed
extensions, add/edit/assignment forms, the merge selection view and the public
bulk-import landing pages. Merge execution and bulk processing stay blocked. These are
view exceptions; POSTs, action queries and processing/save/delete routes remain
blocked. Account and authentication exclusions always take precedence.

A fixed contribution probe may reuse the successful native Authorization header
inside the browser and request only the observed central contribution collection
on pages one and two with a twenty-five-record requested bound. Stop on any HTTP
failure, a two-MiB response, an unrecognized envelope or more than twenty-five
rows; do not request an unbounded collection. Return financial-redacted schema,
row counts and identifier-comparison booleans only. Use an eighteen-second total
deadline and spacing between requests. Synthetic fixtures must cover bound
failure, permission failure, no identifiers/amounts and write exclusions before
live use. This does not create an exporter or register an OAuth client.

GOTCHA specification, 2026-10-04
--------------------------------

Goal: settle the practical questions about a read-only exporter using the
operator's interactive Breeze session, without requiring our own OAuth client.

Success requires evidence for: (1) which UI generation and API origin serves
each export domain; (2) authentication/session renewal and login expiry;
(3) the requests needed for read-only page loading, including POST reads;
(4) response envelopes and export schema coverage; (5) page numbering, bounded
page size, ordering and termination; (6) permission failures; (7) download
behavior and coverage; (8) a supported operational decision and known limits.
Static code can settle implementation intent; runtime acceptance needs observed
requests or fixed reviewed reads. Unknown contracts remain explicitly open.

Use the existing isolated Firefox session and private local BiDi service.
Account/API settings and OAuth consent/registration, production
mutations and credential extraction are excluded. Never emit or save records,
token values, inline scripts, raw network errors, response bodies or full DOM.
Allow only reviewed public static assets with credentials omitted. Browser
request metadata retains generic paths, header-presence flags, fixed error
categories and status codes. Any response inspection must reduce data in browser
memory to approved schema identifiers/types and bounded counts before returning.
No automatic retries, login, logout or arbitrary request/evaluation interface.

Trigger: the operator requested investigation of the browser-session path.
End: every question above has a verified answer or an evidence-backed limit
that determines the transport decision. A missing login or permission does not
count as resolution. On login transition pause capture; preserve the window
and let the operator authenticate. No time/token budget; existing bounded
control deadlines, asset sizes and metadata limits apply. Test each privacy
boundary with synthetic input before using it against the account.

Initial evidence
----------------

The existing session was on Dashboard. Guarded People navigation produced a
307 followed by an HTTP 200 document, bearer-authenticated requests to the
central API, preflight failures and a blocked POST. The UI then reached Login.
After capture was paused, the window subsequently appeared on legacy People;
the reason for that transition is not yet established. These observations do
not distinguish stale authentication from inspection interference.

The earlier nine synthetic source-scanner checks were repeated and all passed
with zero account requests and no real DOM reads.

The operator subsequently confirmed that the browser had signed out for lack
of activity and logged in again. Add a small keepalive while capture is active:
every two minutes, fetch the observed same-account Dashboard document using the
browser's cookies, cancel its unread body and return only a fixed health result.
Do not navigate the visible window or extract credentials. Follow redirects
under the existing request guard; stop/pause on login, restricted page, changed
origin or failure. Pause disables keepalive before interactive login. Successful
requests establish liveness, not proof that the provider's idle timer resets;
the latter needs observation across the idle interval.

Open questions
--------------

* Authentication/guard interference: determine why initial authenticated reads
  failed and classify the blocked POST before considering an exact exception.
* Legacy/new UI mapping: establish which generation actually serves each page.
* Read-only request contracts and POST reads: inspect public implementation
  before allowing any new request shape.
* Schema, pagination, permissions and downloads: require runtime evidence after
  authentication and guard behavior are understood.
* Operational limits: determine what remains interactive and which data domains
  can feed the existing consumer-independent export format.

Static-source extension
-----------------------

Extensionless JavaScript URLs under ``/js/`` are a possible legacy asset shape;
none has yet been established as a required readable asset in this account. Permit
only URLs actually observed in external script tags or script/XHR resource
timing entries under ``/js/``, on the same account or
the observed shared public asset hosts, with a bounded identifier-only path.
Fetch without credentials, reject redirects and non-JavaScript MIME types,
and apply the existing bounded structural reduction. Only cache/version query
keys may qualify an extensionless source; fetch/data resources do not qualify.
Do not read inline scripts or
page data. Relative literal AJAX paths in public scripts are normalized to
generic route references; no script is executed by the scanner.

Page-specific contract reduction
--------------------------------

Legacy list loaders may be declared in page-specific inline code. Extend the
earlier public-only source boundary for this narrow purpose: scan scripts in
browser memory for literal jQuery AJAX option objects, returning only GET/POST,
account-relative ``/ajax/`` operation names and direct request parameter names.
Ignore cookies, storage, headers, response data, source snippets, strings/comments
containing code and computed URLs/methods. Do not execute the inspected code.
Cap script size, match count and field count. Synthetic tests must show that
embedded credentials/records, nested writes and spoofed code strings do not
escape or become top-level declarations. A match is implementation evidence,
not a server guarantee. Review a specific read operation and its parameters
before adding any guard exception; do not relax the default write block.

Forms contract review: the current page declares POST ``/ajax/get_forms_list``
with the sole request field ``options`` for the list loader. Mutations such as
restore/create/edit/save use separate endpoints. Permit only this exact POST
path, with no action/query parameters except an optional cache key. Other POSTs
remain blocked, including notification updates and real-time channel auth.
The tool exposes no arbitrary replay interface. This is frontend evidence of
read intent; backend side effects are not established by a method/name alone.

Response-schema reduction
-------------------------

For reviewed reads only, install a per-tab preload hook around native fetch/XHR.
Preserve website request arguments and authentication; issue no extra data
request and read no token/session storage. Reduce successful responses entirely
inside the browser to format, approved field names/types, bounded array counts
and pagination integers. Unknown field names become a count, never strings.
HTML responses return fixed tag counts only. Cap fetch-clone reads at 2 MiB,
nesting depth at four and array samples at three; retain at most twenty summaries
per document. Raw bodies must never leave browser memory or be cached by the
inspector. Exclude login/account/settings and all authentication/token responses.
Pause removes preload hooks and disables current-document collection. Synthetic
fixtures must cover private keys/values, HTML, oversized bodies, failure responses
and unreviewed routes before installation in the live tab.

Pagination inspection returns only conventional pagination labels and enabled
states. Programmatic Next is limited to Forms, requires guarded schema
observation and never clicks a submit button. Match only pagination containers;
do not expose record text or arbitrary control labels. After a click, verify
the observed loader request and result rather than assuming a page advanced.

People contract review: inline page code declares POST ``/ajax/list_all_people``
with no data or with the ``limit`` field, separately from filter persistence,
bulk updates, archive/delete and email endpoints. Permit this exact read POST
under the same no-action-query rule. A fixed browser probe requests limits two
and three through the page's existing jQuery/CSRF setup and returns only schema,
bounded counts and whether the first two IDs stay in the same order. IDs and
record values stay in the browser. There is no arbitrary endpoint, headers,
limit or payload input. This verifies prefix/limit behavior, not offset paging
or consistency under concurrent changes.

New frontend SDK probe
----------------------

The public main bundle exports the generated API-client factory as ``a``
(internal symbol ``_e``); its host parameter becomes the generated client's
``BASE``. The People service has ``getPeople`` with ``page``, ``pageSize``,
``sort`` and ``noLimit`` parameters. Use only the already-loaded exact main
module URL and its existing browser authentication middleware. Do not copy a
client ID, headers, cookies, storage or tokens into tooling. Instantiate that
frontend helper for its declared central API host and issue only fixed People
GETs with a page size of two. Stop on an HTTP/auth failure or oversized result.
Return sanitized schema, counts and ID-comparison booleans only. This verifies
browser SDK reuse, not a supported external API contract or OAuth registration.

Native authenticated request reuse
----------------------------------

The exported factory returns a helper whose service client is under ``api``.
The initial probe checked ``helper.people`` and passed a string instead of the
factory's configuration object; its failed contract check does not establish
that the API is uninitialized or needs authentication initialization. A later
public-source trace established that generated transport ``g1`` delegates to
the website's existing ``kn`` request instance. The factory's ``init`` installs
global call functions; it is not required merely to construct ``helper.api``.
Do not invoke initialization/impersonation helpers. The current alternative
retains an
opaque request-header collection from a successful, bearer-authenticated native
central GET inside the browser hook's private closure. Fetch Request headers
are copied as collections; XHR header arguments pass through to a private
Headers collection without interpretation or serialization. Reuse only for
fixed reviewed GET paths on the same central host. Never return headers, cookie
values or tokens, persist them, or send them to another origin. Clear references
and restore wrappers on pause. Report only template availability.

The first replay is People with page size two and pages zero, one and two,
spaced 3.5 seconds apart. Use a shared eighteen-second deadline, reject redirects,
and stop on non-success or a result exceeding the requested page size. Bound
response reads to 2 MiB before parsing and return only sanitized schema/counts
and identity-comparison booleans. HTTP 401 pauses investigation for interactive
reauthentication; HTTP 403 establishes a permission limit, not an instruction to
change roles. This remains browser-session reuse, not an independent OAuth app.

Bound correction after fresh login: the server accepted ``pageSize=2`` but
returned its default hundred-element collection. Stop at that first response.
The next fixed probe also sends the declared ``limit=2``; retain the same byte
cap and stop if the server ignores that bound. Do not silently accept the
default-size response or claim the code generator's page-size name is honored.

The ``limit=2`` probe returned two records on pages zero and one, then none on
page two. Metadata reported ``per_page=100``, ``total=2`` and ``last_page=1``:
``limit`` truncates the total collection before pagination. Next test the fixed
``per_page=2`` candidate, derived from that response and other declared client
collection parameters, retaining ``limit=4`` as a total safety cap. Stop if a
response contains more than two records. This experiment cannot establish full
collection coverage while the total cap remains enabled.

Native Tags loaded successfully with a JSON collection envelope, an empty
``data`` array and ``meta``/``links`` pagination. Inspect approved query field
schemas for native reviewed GETs, retaining only parameter names/types and
bounded pagination integers, to distinguish filtering from collection emptiness.
Also observe the statically reviewed ``GET /api/v2/tags/folders`` response;
issue no additional folder request. These observations do not establish that
an empty root list means the account has no tags.

Observed server-bound paging experiment: ``per_page=2`` was also ignored.
Responses consistently declare a hundred-record page size. Test that explicit
observed bound with ``pageSize=100`` and no total ``limit``; reject any response
over one hundred records. Initially request pages zero, one and two. If the
first response provides a safe ``last_page`` integer, also request that page
and its successor (at most five requests total), retaining 3.5-second spacing,
the eighteen-second shared deadline and 2 MiB per-response cap. Return only
schema/counts and ID/order comparison booleans. Never enumerate the intervening
pages or export values as part of this experiment. This verifies the endpoint's
observed fixed paging bound and termination, not support for smaller page sizes.

Person-detail experiment: add a separate fixed read using the successful native
header template. Request ``GET /people?limit=1``; reject a collection over one
record. Use its positive integer ID entirely inside browser memory for the
declared ``GET /people/{id}`` route, after 3.5 seconds. At most two requests,
eighteen-second deadline, no redirects, 2 MiB each. Reject non-numeric IDs and
return no record identity/path. Return only approved schema names/types and
fixed failure categories; HTTP 401 pauses capture and 403 is a permission limit.
Test these boundaries with synthetic responses before running the live probe.

The detail read succeeded but its field names were outside the fixed schema
vocabulary. To establish structure without disclosing custom field identifiers
or labels, summarize up to three unrecognized field values by the same bounded
schema reducer, without emitting their keys or scalar values. Add only familiar
profile-schema identifiers (``details``, ``field_type``, ``response``) to the
fixed vocabulary. Preserve the depth cap and synthetic private-key/value checks.

Giving navigation correction: the public main route registry explicitly declares
``/payments/reports`` and ``/payments/reports/list_people``. Once the account's
ordinary Giving navigation link has been observed, use only the fixed same-
account ``/payments/reports`` page for guarded Giving inspection. This avoids
the default redirect into a mutation-shaped path. Do not relax GET-action
blocking, construct arbitrary report paths, change report filters or invoke
exports. Verify the selected document after asynchronous navigation.

The Giving report loaded successfully and declares its list request as
``POST /ajax/payments_search_results`` with ``page`` and ``query``, separate
from add/update/refund operations. Permit only that exact native list POST,
with the existing optional-cache-query rule. Observe its response through the
bounded schema hook; do not construct report filters, replay searches, start
export jobs or permit contribution mutations. Preserve financial values and
person identifiers inside the browser.

Authentication renewal correction: a later trace established successful
authenticated GETs followed by HTTP 401 and native POST
``https://api.breezechms.com/api/v2/auth/refresh`` attempts. The guard blocked
those attempts, and the page lost ordinary navigation. A dashboard document
keepalive does not by itself keep the API access token valid. Permit only the
website's exact existing-session refresh POST on that HTTPS central host, with
no query arguments. The public SDK declares this refresh operation separately
from login/one-time-token/OAuth grants. Never inspect its response body or replay
it manually. Preserve normal website refresh and role constraints; wait for
operator reauthentication if the failed renewal already ended the session.

Observed results so far
-----------------------

* Fresh login restored bearer-authenticated central GETs with HTTP 200; the
  operator confirmed idle sign-out. Keepalive dashboard requests have returned
  307/200 without changing the visible page.
* The reviewed Forms POST returned HTTP 200 and an HTML table fragment. The
  initial ``options`` payload has no approved pagination fields, and no
  conventional pagination container was found. Do not infer completeness from
  table-row counts or assume JSON pagination for that loader.
* The reviewed legacy People read returned an HTML table for both limits two
  and three, with the same row count exceeding those limits. A bounded-record
  contract is therefore unverified; no further full-table probe is warranted.
* SDK construction returned a helper with ``api`` rather than a directly usable
  top-level People service. The probe's object-shape assumption was incorrect;
  this was a tooling error, not an established authentication limit. No SDK data
  read, auth initialization or impersonation helper was invoked. Native
  authenticated request reuse is the current investigation path.
* After the operator's next login, guarded native central GETs again succeeded.
  The five-read People experiment verified the observed hundred-record bound:
  page zero matched page one, pages one and two had disjoint IDs, the declared
  last page returned data, and its successor returned an empty collection.
  Pages were one-based in response metadata; zero normalized to one. The
  returned ``pagination`` envelope includes ``count``, ``current_page``,
  ``last_page``, ``per_page`` and ``total``. No intervening pages were enumerated
  and no IDs or records were exported. This verifies paging behavior for this
  session, not snapshot consistency during concurrent changes or complete
  person-field coverage.
* Tags uses a JSON ``data``/``meta``/``links`` envelope. The native request sends
  ``page=1`` and ``pageSize=25``; metadata reports a twenty-five-record page.
  Its current root list is empty while ``GET /tags/folders`` returns a populated
  collection with ``id``, ``name``, ``description`` and ``parent_id`` fields.
  A remaining unrecognized request parameter prevents declaring the root result
  to be all-account coverage. Folder traversal and membership remain open.
* Events uses the central JSON API: calendar objects include ``id``, ``name``
  and ``address``; event instances include ``id``, ``event_id``, ``name``,
  ``description``, ``start`` and ``end``. Native event queries contain three
  currently unrecognized fields; the visible calendar window is not a complete
  event-history export. No arbitrary event range was replayed.
* Giving navigation produced a redirect followed by a guard-rejected GET under
  ``/payments/``. The previous page remained visible. This is an unresolved
  guard/navigation contract, not a Giving permission denial; its target must
  be statically reviewed before any exception. Forms again returned its
  reviewed HTML list response successfully.
  The later fixed ``/payments/reports`` navigation loaded successfully. Its
  declared ``payments_search_results`` loader has a narrow read exception, but
  native loading did not invoke that loader or produce a reduced response.
  No report search, contribution mutation or export job was triggered; financial
  response coverage and the other blocked read dependencies remain open.
* A fixed one-record People list followed by ``GET /people/{id}`` both returned
  HTTP 200. Reduced detail structure contains nested name, email, phone and
  address objects, with city/state/zip string types. Unrecognized field keys
  remain hidden; only their bounded value-schema samples are retained. This
  establishes detail access for the session, not a complete custom-field map.
* Explicit Dashboard keepalive succeeded repeatedly after login without changing
  the visible page. No API renewal response or provider idle-time guarantee has
  yet been observed under the corrected guard.

Public authentication lifecycle
-------------------------------

The inspected main bundle's shared request instance ``kn`` inserts the existing
access token into native requests. Its renewal handler ``ah`` uses
``POST /auth/refresh`` when that access token is present. If it is absent but an
existing session key is present, it instead uses ``POST /auth/sessionkey``.
The latter remains blocked during inspection: no live evidence has established
that an exception is necessary for the current session. Interactive login takes
place with capture paused. Missing credentials or rejected renewal can lead to
logout/login; the tool must not turn those conditions into automatic login.

The browser sets its access-token cookie expiration to two weeks on successful
renewal and can update the session-key cookie to thirty days after
``GET /auth/sessionkey``. These are frontend cookie policies, not evidence for
server token lifetimes or permission to extend a server session. A layout also
checks the ``logout_automatically`` role prefix when the session key is missing.
Do not override that policy or infer it from a user's role values.

The public request instance retries HTTP 502 twice and has shared authentication
renewal handling; successful native API calls and cookie-backed Dashboard reads
therefore serve different functions. The fixed raw-fetch paging probe avoids
those SDK retries but also does not renew its own rejected token. On HTTP 401 it
pauses for interactive recovery. A usable browser exporter still needs observed
renewal and a deliberate policy for expired sessions; keepalive alone proves
neither. No account cookies, token values or role data were read for this trace.

Public paging contracts
-----------------------

The anonymously fetched main bundle declares People ``GET /people`` with
``page``, ``pageSize``, ``sort``, ``collection_filter``, ``exact``, ``limit``,
``ids_only`` and ``no_limit`` query fields. Its generated helper defaults
``limit`` to 100 and ``exact`` to false. The fixed native probe currently sends
``page``, ``pageSize`` and ``sort`` only. Their server-side precedence, valid
sort encoding and precedence were initially unverified. The observed paging
experiment above now establishes one-based numbering and the hundred-record
bound for this session; it does not prove a requested ID sort is honored or
establish consistency while account records change.

The same bundle declares ``GET /event-instances`` with ``page``, ``pageSize``,
``sort``, ``filter``, ``has_set_list`` and ``has_service_plan``, whereas
``GET /events/calendars`` declares only ``filter``. Both declare 401 and 403
failures. These are static candidate contracts, not observed account coverage
or approved extra replay operations. The source is the public
`main bundle <https://main.ddgv4rlrmu56c.amplifyapp.com/assets/main-BkBiSYb4.js>`_;
the existing source digest identifies the inspected version.

Additional static contracts: Tags ``GET /tags`` declares ``page``, ``pageSize``,
``filter`` and ``sort``. Tag folders ``GET /tags/folders`` declares ``filter``
and ``sort``; funds ``GET /contributions/funds`` declares only ``filter``.
Do not apply the People paging experiment to these collections without
reviewing their actual response contract. A bounded request parameter is not
declared for either folder or fund collection by this helper.

The public client distinguishes ``GET /people/export-config`` from creating
or deleting export configurations. Its People export uses
``POST /pusher/people/{exportKey}``, alongside other asynchronous export jobs.
That job is outside the approved list-read exceptions and was not invoked.
Public static code alone does not prove job behavior, download expiration,
file coverage or whether starting a job is acceptable within read-only scope.
Prefer verified bounded collection reads for the investigation; retain the
job path as a separately reviewed option rather than silently enabling it.

Initial ATLAS instrumentation report, 2026-10-04
------------------------------------------------

Edge cases tested: synthetic fixtures cover private field names and scalar
values, HTML responses, oversized bodies, cross-origin and authentication-route
exclusion, bounded query summaries, unavailable authentication templates,
permission failures, pagination controls and prototype restoration on pause.
The exact session-refresh exception rejects alternate hosts, protocols, query
arguments and other authentication operations.

Failure handling: fixed diagnostic categories replace raw browser errors.
Keepalive and an explicit People replay pause on detected login failure. Normal
website refresh is permitted without reading its response. The failed SDK
experiment stops at its contract check before a data request. Authentication
recovery after the earlier blocked refresh was verified after operator login.
A retained People URL alone remains insufficient evidence of authentication.

Concurrency and load: local control operations are serialized. Native People
replay has an eighteen-second shared deadline, a maximum of five requests with
3.5-second spacing, and an observed hundred-record page bound. The separate
person-detail probe has at most two requests and a one-record list bound.
Response reads stop
at 2 MiB; an oversized record count stops further requests. Observers retain
twenty reduced summaries per document. These limits bound the experiment;
they do not establish the central API's rate-limit contract.

Security: raw bodies and opaque authentication headers remain inside browser
memory. Tool responses contain approved schema names/types, bounded counts,
fixed status categories and comparison booleans. No credential, account record,
source snapshot or download was saved. Account/API settings remain excluded.
Source scanning executes no inspected code; synthetic browser tests use fake
requests and fixtures rather than account traffic.

Verification: ``uv tool run --from uv==0.12.22 bash scripts/check.sh`` passed
with 309 tests passing and one
opt-in live test skipped. Ruff formatting/lint, ty, dependency audit and wheel/
sdist builds passed. Sixty-seven tests exercise the Python inspection boundaries.
The system uv changed to 0.12.23 during this investigation; the exact project-
pinned version was selected through the tool runner, without changing the pin.
Fourteen native-probe and thirteen response-reducer synthetic browser checks
passed after their changes, without account requests or real DOM reads. These
include five-request termination, oversized-page stopping, private detail
schemas and rejection of malformed IDs. Repeat helper checks after changes
before live use.

Pass: local instrumentation checks and reviewed legacy read observations.
Verified live: native authenticated People paging and empty-page termination,
single-person detail access, Tags/folders and Events response envelopes, Forms
list loading and fixed Giving reports navigation. Unverified: session renewal
under the corrected guard, stable ordering under changes, remaining domain
schemas, role-specific coverage and export downloads. The browser-session
investigation is still active; this report does not certify an exporter.
Document recovery diagnostic
----------------------------

An Extensions navigation can leave the browsing-context URL at its requested
account route while the active document is a browser error document. Diagnose
this using only fixed booleans (account-origin match, browser-error protocol,
visible password input) and document readiness. Never emit the document URL,
title, content, or credential values. A mismatch must stop page classification;
it is not evidence of logout. Account remains excluded before evaluating DOM.

Intercept recovery: W3C BiDi defines ``no such request`` when an intercepted
request is no longer in the blocked-request map. Treat that exact response as
a completed/vanished request without replaying or continuing anything. Other
guard errors still stop inspection. Verify both cases synthetically. This
addresses a possible cancellation race; it does not establish the cause of
the observed debugging-session failures.
Source: https://www.w3.org/TR/webdriver-bidi/#command-network-continueRequest

Public dynamic-route gap: legacy links do not necessarily expose newer person
notes/tags/message views. Derive only their fixed public route templates from
person IDs already present in observed same-account profile links. Similarly,
derive an event's checked-out view from an observed attendance link, and an
instance's attachments view from its observed plan link. Never interchange
event and instance IDs, invent IDs, or accept caller-supplied IDs/URLs. URLs
stay in the private registry; return masked paths and fixed provenance only.
Reconcile these derived candidates into traversal after each link-discovery step.

Masked-path collision correction: distinct legacy route names can both reduce
to ``/{segment}/{segment}``. Do not use that display shape as a traversal key.
Assign an opaque family index to a private normalized path, replacing record
positions from the public templates. Preserve otherwise unknown route words
only inside the private process. Emit the family index, not words or a hash;
group record representatives by that family. Synthetic tests must distinguish
two masked legacy screens while grouping IDs in the same record-view template.

Aborted-document fallback: for an already observed eligible same-account page
index, permit one guarded browser GET with manual redirects and a ten-second
deadline. Refuse attachment/non-HTML/error bodies and stop reads at 2 MiB.
Reduce HTML in browser memory to inline request contracts, bounded tag counts
and eligible links; parse anchor attributes in an unattached inert template,
never execute page scripts or attach content. Raw HTML/records remain in the
browser. URLs can enter the private registry only and must be masked before
tool output. Report redirects/unavailable bodies rather than following them
blindly. This can distinguish a server document from a navigation failure.

The Giving screens also load a shared ``app.js`` from another Breeze service
origin. Include observed HTTPS Breeze script origins in static-source inspection,
while excluding credentials and all query keys except cache/version markers.
Revalidate cached sources, omit credentials, reject redirects and non-code MIME,
and preserve byte limits. Report an unknown Breeze host as a fixed category;
do not reveal an account-like hostname. This is public script inspection only,
not permission for external authenticated requests or Account navigation.

Supplemental Giving API: native requests establish successful central GETs for
``/contributions``, ``/contributions/overview``, ``/contributions/batches``,
``/contributions/funds/folders`` and ``/contributions/methods``. They are absent
from the main generated client, but appear as relative routes in shared public
application chunks. Extend observation to these exact GETs without issuing
extra API calls. Preserve private numeric/financial values: for contribution
responses, return types for all numeric metadata rather than assuming a field
named ``total`` is a record count. The shared client uses a ``config`` request
object; permit only bounded paging integers in that reviewed request envelope,
with nested filter values remaining private. Static source can return relative
finance route references as candidates; runtime evidence determines methods.

Contribution collection result, 2026-10-04
------------------------------------------

The Dashboard's native ``GET /api/v2/contributions`` responses are JSON envelopes
with ``api`` and ``data``. Reviewed row keys include ``id``, ``person_id``,
``fund_id``, ``batch_id``, ``amount`` (string), ``paid_on`` (string), ``method``
and ``note``. Only field types and counts were retained. Two native request
parameters are still unrecognized by the curated request reducer; their values
were never returned. Do not infer that the People paging contract applies here.

The fixed ``page=1&limit=25`` contribution probe exceeded its two-MiB bound and
stopped before a second request. No body was returned or saved. The website's
filtered native reads establish access and a row schema; they do not establish
a bounded full-export strategy. The future adapter must validate the actual
filters/paging rather than retry the same unsupported limit or request an
unbounded collection. Native batch reads show a twenty-five-row paginated
envelope when ``page=1`` is present, and an unpaginated envelope without it.

The reducer recognizes repeated/trailing separators in reviewed GET paths and
reports masked shapes for unknown parameters, preserving only curated code
field identifiers. Financial response metadata is type-only, including numeric
``total`` fields. Per-frame and aggregate twenty-summary caps both report
truncation; a cap must not be silently counted as complete observation.
