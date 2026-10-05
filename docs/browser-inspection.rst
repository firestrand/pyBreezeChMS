Interactive browser inspection
==============================

Operator scope, 2026-10-04: investigate all reachable page types and subpages
except Manage Account and its API/settings pages. The six main navigation
labels remain available; additional navigation uses private observed-link
indices or fixed public route templates. Only the More menu may be opened by
the menu command. Account/root-settings URLs are rejected before DOM or source
inspection, and guarded capture blocks their requests. Event settings views
outside Account can be inspected without submitting changes.
The current browser-session extension is specified in
``docs/browser-session-investigation.rst``. It permits reviewed Forms/People
list POSTs and the website's exact central existing-session refresh POST;
other writes and OAuth grants remain blocked. Response reductions and opaque
request-header reuse stay inside the browser; only schema/count metadata is
returned. This restriction supersedes earlier exploration scope.

Expanded traversal commands::

    uv run --locked python scripts/browser_inspect.py links
    uv run --locked python scripts/browser_inspect.py routes
    uv run --locked python scripts/browser_inspect.py follow --link <index>
    uv run --locked python scripts/browser_inspect.py document-state
    uv run --locked python scripts/browser_inspect.py document-selftest
    uv run --locked python scripts/browser_inspect.py read-page --link <index>

``links`` scans approved same-account documents; ``routes`` adds fixed public
paths and typed aliases derived from IDs already in observed links. Both
return masked paths and opaque family indices, never raw URLs, names or IDs.
Family indices distinguish routes that have identical masked display paths.
They are ephemeral and must be refreshed after restarting the private service.
Query values and raw URLs stay in its working memory. Link scans/registries
report truncation; a zero frontier alone cannot establish coverage if truncated.
``follow`` requires the guard and a matching document readiness event.
``document-state`` returns only readiness/origin/protocol diagnostics.
``read-page`` performs a bounded browser GET and reduces inert HTML to request
contracts and eligible links; it executes no returned scripts, follows no
redirects and reads no attachment bodies. It can investigate aborted document
navigation. Account and authentication/action exclusions still apply.

JavaScript investigation GOTCHA, 2026-10-03
-------------------------------------------

Goal: understand browser API options from loaded external application scripts.
Success: inventory static assets, identify literal endpoint references and their
request methods/parameter identifiers, and distinguish observed evidence from
inferred contracts. Fetch loaded JavaScript assets on the account origin or
the observed public application CDN or an observed Breeze JavaScript origin,
with credentials omitted;
do not read inline scripts, storage, cookies, records, or API response bodies.
Keep script source transient in browser memory; return bounded code-derived
metadata only. No source archives, source maps, general evaluation interface,
or broad POST allowance. One level of directly referenced static dependencies
can be inspected on the same asset origin; analytics scripts are excluded.
Inspect main pages with the existing write guard. Static endpoint names are
application code identifiers; route queries, numeric IDs, account origins,
arbitrary string values and source snippets are excluded. Public service/CDN
origins are retained as source provenance. Stop authenticated inspection on login
expiry; public code inspection can continue. Stop on asset/type mismatch or
bounded fetch failure. Document
authentication, pagination and export evidence, including unresolved contracts.

GOTCHA specification
--------------------

Goal: let the operator log in interactively, then inspect read-only Breeze pages
and network contracts without exposing records or authentication values.
Success: an isolated visible Firefox session, local-only BiDi control, tested
metadata redaction, capture disabled during login, and resumable inspection after
operator login. Preserve existing browser profiles and the library's runtime API.
Use the installed Firefox 157 on the existing X11 desktop. The Docker daemon is
not accessible to this user; no daemon permission change is needed.
Network output contains method, generalized path, parameter/header names, status
and counts only. No cookies, token values, bodies, screenshots, full DOM or HARs.
Profile/session files are private and outside source; inspection summaries are
private and ignored. Programmatic inspection never submits forms or clicks
mutation controls. Capture starts only after the operator confirms login.
Remote navigation targets must be same-account recognized read pages. During
inspection, unreviewed non-GET traffic and known mutation-shaped requests stop
before dispatch; an endpoint cannot be presumed read-only from its HTTP verb.
No time/token budget; bounded messages, command deadlines and metadata limits.
On connection loss, report a fixed failure and reconnect only on operator action.
Browser login remains operator-controlled; passwords never enter tooling/chat.

Operation
---------

On this desktop, Firefox 157 uses WebDriver BiDi directly. There is no container,
geckodriver, Selenium, Chrome, or runtime library dependency for this path.
``websockets==17.1`` is a locked development dependency from PyPI, with
BSD-3-Clause licensing and source at https://github.com/python-websockets/websockets.
The installed package metadata and official versioned documentation were checked.

For a fresh inspection session::

    uv sync --locked --group dev --extra operator
    uv run --locked python scripts/browser_inspect.py launch
    uv run --locked python scripts/browser_inspect.py serve

Keep ``serve`` running in its terminal. In another terminal, after interactive
login::

    uv run --locked python scripts/browser_inspect.py status
    uv run --locked python scripts/browser_inspect.py pages
    uv run --locked python scripts/browser_inspect.py capture
    uv run --locked python scripts/browser_inspect.py navigate --page People
    uv run --locked python scripts/browser_inspect.py events
    uv run --locked python scripts/browser_inspect.py pause

While capture is active, the inspector requests the observed Dashboard document
every two minutes without changing the visible page. It cancels the unread body
and pauses on failure or login. ``keepalive`` runs one immediate check. This
maintains ordinary activity but is not proof that API access tokens remain
valid; native token refresh is a separate website operation.

For reviewed schema investigation::

    uv run --locked python scripts/browser_inspect.py page-selftest
    uv run --locked python scripts/browser_inspect.py read-selftest
    uv run --locked python scripts/browser_inspect.py native-selftest
    uv run --locked python scripts/browser_inspect.py page-contracts
    uv run --locked python scripts/browser_inspect.py watch-reads
    uv run --locked python scripts/browser_inspect.py read-schemas
    uv run --locked python scripts/browser_inspect.py probe-native-people
    uv run --locked python scripts/browser_inspect.py probe-native-person
    uv run --locked python scripts/browser_inspect.py probe-native-contributions

``page-contracts`` returns only literal AJAX method/path/request-key declarations
from page code. ``watch-reads`` installs bounded reducers for reviewed responses
and privately retains a successful native central GET's header collection.
``probe-native-people`` can use that collection for fixed People GETs. Tokens and
headers never leave the browser. ``pause`` removes preload hooks, disables
current collection in root and approved frames, clears retained header
references and stops keepalive. Hook installation checks decoded Account and
authentication exclusions before touching any frame's DOM or network methods.
Frame observers are capped at thirty-two, with a twenty-summary aggregate;
schema summaries report truncation.
The People probe checks at most five hundred-record pages, including the
declared collection end. The separate person probe uses a one-record list and
one numeric-ID detail read; it returns reduced schemas only. Giving navigation
uses the publicly declared same-account reports page after its ordinary menu
link is observed. Exact reviewed Forms, People and Giving list POSTs are allowed;
mutations and unreviewed POSTs remain blocked.

Static-code inspection also works while logged out, with credentials omitted::

    uv run --locked python scripts/browser_inspect.py assets
    uv run --locked python scripts/browser_inspect.py source --asset <index>
    uv run --locked python scripts/browser_inspect.py source --asset <index> --dependency <index>
    uv run --locked python scripts/browser_inspect.py source-selftest

Use the asset filename and SHA-256 to identify a bundle. Dependency indices refer
to its returned ``import_paths`` array. Asset indices stay stable as chunks load
within one document; refresh the inventory after navigation. Source summaries
contain static routes, directly matched declarations, approximate nearby code
identifiers, public service bases, imports and marker counts. Marker presence
alone does not verify an authentication protocol or a response schema.
See docs/browser-api-findings.rst for the newer API and OAuth evidence.

``launch`` refuses to replace existing browser state. This inspection window is
already open and signed in; use its running service instead of launching again.
Pause capture before logging in again or using the window interactively. Ctrl-C
or SIGTERM ends the inspection service and its BiDi session; Firefox stays open.
No automatic reconnect or request replay occurs. Direct Firefox BiDi sessions
cannot be reattached after an abrupt client disconnect in the tested version.
An abandoned session requires restarting only the isolated Firefox profile;
the normal browser is unaffected. Use graceful service shutdown when possible.

The debugger was verified listening on 127.0.0.1 only. The Unix control socket
has mode 0600 inside a mode-0700 ignored directory, ``.breeze-runs/browser``.
Firefox's private profile is outside the repository, in its Snap-compatible
profile directory. Protect these files as authenticated browser state. No
browser response bodies or authentication values are written to inspection logs.
Only generic allowlisted route words and query field names are retained; other
segments/fields are placeholders. Metadata is held in a bounded in-memory deque.
Navigation is limited to recognized same-account main-section links.

Observed findings, 2026-10-03
-----------------------------

After the operator logged in, all six main-section links were available.
People, Tags, Events, Forms and Dashboard document requests completed with HTTP
200. Giving's ``/payments`` request returned a 307 redirect; final Giving content
was not confirmed during the guarded pass. Page navigation itself does not
establish that all asynchronous lists have loaded.

Captured account requests carried cookies, and AJAX requests also carried a CSRF
header. None of the observed account requests carried an Authorization header.
This is evidence of browser session authentication, not evidence of an OAuth
integration or a supported token contract. Authentication values were not read.

Data-loading requests included POST ``/ajax/get_forms_list`` and other generalized
AJAX routes. Six POST requests were stopped before dispatch during this pass.
Consequently some page lists could not populate. A future website adapter needs
endpoint-specific evidence before permitting a POST read, plus session-expiry,
CSRF and pagination contracts. No such adapter or credential extraction is
implemented here; the supported export path still uses the documented API.

The guard blocks unreviewed non-GET/HEAD/OPTIONS requests and known write-shaped
paths/actions on the account origin. It is a conservative inspection aid, not
proof that every allowed GET is side-effect free. Third-party traffic is outside
its interception scope. Inspection never submits forms or clicks write controls.

ATLAS hardness report
---------------------

Edge cases: synthetic tests cover secret-bearing headers, query values, names,
IDs and bodies; cross-origin exclusion; POST and mutation-shaped GET rejection;
login-screen refusal; unguarded navigation refusal; and intercept-install failure
cleanup. Metadata and raw browser values are separate throughout the control path.

Failures: fixed operator errors replace raw browser errors. Failed intercept
installation clears capture readiness and unsubscribes. Guard acknowledgement
failures or connection loss stop the service. SIGTERM cleanup was exercised
against the isolated browser. An abrupt-disconnect recovery test exposed the
reattachment limitation; restarting the isolated profile restored the signed-in
session, and unsupported reattachment logic was removed. Firefox requires
structured URL patterns for this intercept; a glob string was rejected, and the
implementation now supplies protocol and hostname separately.

Concurrency/load: control operations are serialized; command deadlines are 25
seconds, socket input is bounded, WebSocket messages are capped at 2 MiB, and
metadata retains at most 2,000 events. Guard acknowledgements are handled by the
receiver so intercepted traffic cannot deadlock command replies. Navigation
completion may precede asynchronous page loading; verify status/events afterward.

Security: private profile and state permissions, loopback-only debugger, local
Unix socket, restricted navigation, no general script-evaluation or replay API,
allowlisted output fields, and no login capture. Sensitive session/profile state
remains outside tracked source and build artifacts.

Initial verification: thirty-one synthetic inspector tests passed; Ruff and ty passed.
Nine fixed browser-scanner checks passed in the earlier Firefox run without
account requests or real DOM reads; they were not repeated on the excluded page.
The project's locked check script passed with 273 tests passing and one opt-in live
test skipped, including dependency audit and package build. Clean wheel/sdist
installation checks passed. Live read-only document/request observations are described above;
no production fixtures or write API acceptance checks were performed.

Pass: interactive browser integration and metadata-only inspection work.
The subsequent browser-session investigation verified the reviewed Forms and
People POST list loaders and exposed blocked native session renewal. Its
current scope, results, 309-test project check and remaining schema/coverage
limits are recorded in ``browser-session-investigation.rst``. Giving reports
navigation works, but its data response remains unverified. No claim is made that undocumented endpoints are stable
or supported for production export.

Reviewed view exceptions
-------------------------

The exact query-free installed-extension, add-person/followup, bulk-import
landing-page and numeric person/event edit paths are view exceptions to the
mutation-prefix heuristic. They do not permit POSTs, action queries, saving,
import processing, installation or deletion. Account exclusions take precedence.
Global navigation labels are bound to reviewed main-page paths, preventing a
person's Giving tab from replacing the account's main Giving destination.

The fixed contribution probe has at most two reads, an eighteen-second deadline,
a two-MiB response cap and a twenty-five-row bound. It returns financial-redacted
schemas and counts only and stops if the server ignores the requested bound.
It is an investigation helper, not a supported full-export implementation.
