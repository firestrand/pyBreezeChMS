"""Private Firefox BiDi inspection: approved navigation and redacted metadata only."""

import argparse
import asyncio
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path
from typing import cast
from urllib.parse import parse_qsl, unquote, urlsplit

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

ROOT = Path(__file__).resolve().parents[1] / ".breeze-runs" / "browser"
PAGES = frozenset(
    {
        "Dashboard",
        "People",
        "Events",
        "Tags",
        "Giving",
        "Forms",
    }
)
MENUS = frozenset({"More"})
PUBLIC_PAGE_ROUTES = (
    "/",
    "/dashboard",
    "/people",
    "/people/filter",
    "/people/saved",
    "/r/people",
    "/r/tags",
    "/r/events",
    "/events/blockout_dates",
    "/followups",
    "/followups/search",
    "/history",
    "/history/email",
    "/groups",
    "/songs",
    "/extensions",
    "/extensions/installed",
    "/extensions/search",
    "/payments/reports",
    "/payments/reports/list_people",
    "/payments/reports/graph",
    "/forms",
    "/timeline/v2/",
    "/roles/all",
    "/admin/members",
    "/admin/profile_mapping",
    "/admin/users",
    "/bulk/automated_tasks",
    "/extensions/mailchimp",
    "/extensions/pco",
    "/extensions/quickbooks",
    "/give",
)
READ_POST_ROUTES = frozenset(
    {
        "/ajax/get_forms_list",
        "/ajax/list_all_people",
        "/ajax/payments_search_results",
        "/ajax/list_filtered_people",
        "/ajax/people_tag_list",
        "/ajax/search_followups",
        "/ajax/load_form_entries",
        "/ajax/show_entry",
        "/ajax/get_person_from_id",
        "/ajax/get_family_id_by_person_id",
        "/ajax/get_profile_fields_json",
        "/ajax/load_archived_people",
        "/ajax/load_archived_forms",
        "/ajax/get_form_json_by_url_slug",
        "/ajax/grouped_payment_details",
        "/ajax/payment_details_by_payment_id",
        "/ajax/get_notifications",
        "/ajax/load_history_table_text",
        "/ajax/fundraisers_list",
        "/ajax/pledges_summary",
        "/ajax/load_event_chart",
        "/ajax/search_event_attendance",
    }
)
WORDS = frozenset(
    [
        "api",
        "auth",
        "sessionkey",
        "refresh",
        "config",
        "helm",
        "token",
        "access",
        "breeze",
        "ajax",
        "assets",
        "css",
        "js",
        "scripts",
        "images",
        "img",
        "fonts",
        "people",
        "persons",
        "profile",
        "profiles",
        "events",
        "tags",
        "giving",
        "contributions",
        "funds",
        "forms",
        "fields",
        "entries",
        "dashboard",
        "overview",
        "account",
        "summary",
        "attendance",
        "lists",
        "list",
        "get",
        "search",
        "filter",
        "fetch",
        "load",
        "read",
        "view",
        "reports",
        "calendars",
        "locations",
        "families",
        "groups",
        "pledges",
        "campaigns",
        "settings",
        "index",
        "php",
        "json",
        "html",
        "request",
        "requests",
        "data",
        "action",
        "actions",
        "payments",
        "payment",
        "donations",
        "donation",
        "public",
        "v1",
        "v2",
        "v3",
        "chms",
        "network",
        "extensions",
        "integrations",
        "applications",
        "authorized",
        "oauth",
        "developer",
        "developers",
        "manage",
        "users",
        "roles",
        "keys",
        "r",
        "notes",
        "files",
        "timeline",
        "followups",
        "text",
        "email",
        "songs",
        "song",
        "volunteers",
        "plan",
        "attachments",
        "blockout",
        "dates",
        "fundraiser",
        "fundraisers",
        "graph",
        "folders",
        "archives",
        "saved",
        "admin",
        "members",
        "mapping",
        "all",
        "installed",
        "recurring",
        "methods",
        "internal",
        "messages",
        "message",
        "photos",
        "changes",
        "assignments",
        "history",
        "messaging",
        "batches",
        "options",
        "out",
        "stripe",
    ]
)
READ_VIEW_PATHS = frozenset(
    [
        "/people/saved",
        "/extensions/installed",
        "/people/add",
        "/followups/add",
        "/followups/assign",
        "/bulk/merge_people",
        "/bulk/import_attendance",
        "/bulk/import_barcodes",
        "/bulk/import_giving/generic",
        "/bulk/import_notes",
        "/bulk/import_people",
        "/bulk/import_pledges",
        "/bulk/import_tags",
        "/bulk/import_users",
    ]
)


def read_view_url(url: str) -> bool:
    """Recognize only reviewed query-free form/landing-page GET paths."""
    parsed = urlsplit(url)
    return not parsed.query and (
        parsed.path in READ_VIEW_PATHS
        or re.fullmatch(r"/(people|events)/edit/[0-9]{1,16}", parsed.path) is not None
    )


WRITE = re.compile(
    r"^(add|edit|save|update|delete|remove|send|create|destroy|assign|unassign|checkin|checkout|import|upload|logout|impersonate|revoke|approve|install|uninstall|refund|generate|export|download)",
    re.IGNORECASE,
)
QUERY_FIELDS = frozenset(
    [
        "id",
        "person_id",
        "event_id",
        "tag_id",
        "form_id",
        "fund_id",
        "start",
        "end",
        "start_date",
        "end_date",
        "page",
        "limit",
        "offset",
        "action",
        "method",
        "op",
        "operation",
        "function",
        "task",
        "search",
        "query",
        "sort",
        "order",
        "filter",
        "fields",
        "format",
        "type",
        "date",
        "timestamp",
        "_",
        "cache",
        "cachebuster",
    ]
)


class InspectionError(ValueError):
    """Fixed operator messages only; never echo browser values."""


def launch() -> dict[str, object]:
    """Open a separate Firefox profile; never replace an existing session."""
    if (ROOT / "browser.json").exists():
        raise InspectionError("Inspection browser state already exists; use status to attach.")
    if not os.environ.get("DISPLAY"):
        raise InspectionError("A visible desktop is required for interactive login.")
    ROOT.mkdir(parents=True, exist_ok=True, mode=0o700)
    ROOT.chmod(0o700)
    snap = Path.home() / "snap/firefox/common"
    profile = Path(tempfile.mkdtemp(prefix="breeze-inspect-", dir=snap if snap.is_dir() else ROOT))
    (profile / "user.js").write_text(
        "\n".join(
            [
                'user_pref("browser.shell.checkDefaultBrowser", false);',
                'user_pref("browser.startup.homepage_override.mstone", "ignore");',
                'user_pref("signon.rememberSignons", false);',
                'user_pref("remote.log.level", "Error");',
                'user_pref("browser.startup.page", 3);',
            ]
        )
        + "\n"
    )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [
            "firefox",
            "--new-instance",
            "--profile",
            str(profile),
            "--remote-debugging-port",
            str(port),
            "https://app.breezechms.com/login",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    state = ROOT / "browser.json"
    state.write_text(json.dumps({"pid": process.pid, "port": port, "profile": str(profile)}))
    state.chmod(0o600)
    return {"browser_opened": True, "capture": False, "login": "operator-controlled"}


def obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise InspectionError("Browser object contract changed.")
    return cast(dict[str, object], value)


def safe_path(url: str) -> str:
    """Keep only reviewed generic route words, never arbitrary IDs or names."""
    if read_view_url(url):
        return re.sub(r"/[0-9]{1,16}(?=/|$)", "/{segment}", urlsplit(url).path)
    if urlsplit(url).path in READ_POST_ROUTES:
        return urlsplit(url).path
    parts = unquote(urlsplit(url).path).split("/")
    result = []
    for index, part in enumerate(parts):
        if not part:
            continue
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", part)
        version = (
            (part == "volunteers2" and index > 0 and parts[index - 1] == "events")
            or part in {"v1", "v2"}
            and index > 0
            and parts[index - 1] in {"api", "helm"}
        )
        if version or (words and all(word.lower() in WORDS for word in words)):
            result.append(part)
        else:
            result.append("{segment}")
    return "/" + "/".join(result)


def restricted_page(url: str) -> bool:
    """Enforce the operator's exclusion of account/API administration pages."""
    path = unquote(urlsplit(url).path).lower()
    segments = {part.removesuffix(".php").removesuffix(".html") for part in path.split("/")}
    return (
        bool(segments & {"account", "account_settings", "api-auth", "api-key", "api-keys"})
        or path.strip("/").split("/", 1)[0].removesuffix(".php").removesuffix(".html") == "settings"
        or path.rstrip("/").removesuffix(".php").removesuffix(".html") == "/api"
    )


def write_shaped(method: str, url: str) -> bool:
    if restricted_page(url):
        return True
    parsed = urlsplit(url)
    if (
        method.upper() == "POST"
        and parsed.scheme == "https"
        and parsed.hostname == "api.breezechms.com"
        and parsed.path == "/api/v2/auth/refresh"
        and not parsed.query
    ):
        return False
    if (
        method.upper() == "POST"
        and parsed.path in READ_POST_ROUTES
        and all(key == "_" for key, _ in parse_qsl(parsed.query))
    ):
        return False
    if method.upper() not in {"GET", "HEAD", "OPTIONS"}:
        return True
    if method.upper() == "GET" and read_view_url(url):
        return False
    tokens = re.split(r"[/_.-]", unquote(parsed.path))
    if "oauth" in {token.lower() for token in tokens} and any(
        token.lower() in {"authorize", "accept", "callback", "token"} for token in tokens
    ):
        return True
    for key, value in parse_qsl(parsed.query):
        if key.lower() in {"action", "method", "op", "operation", "function", "task"}:
            tokens.extend(re.split(r"[/_.-]", value))
    return any(WRITE.match(token) for token in tokens)


def link_exclusion(url: str, origin: str) -> str | None:
    """Classify observed links without returning their values or labels."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or f"https://{parsed.netloc}" != origin:
        return "outside_account"
    if parsed.username or parsed.password:
        return "credentials"
    if restricted_page(url):
        return "account_excluded"
    tokens = re.split(r"[/_.-]", unquote(parsed.path).lower())
    if any(token in {"login", "logout", "oauth", "invite", "sso"} for token in tokens):
        return "authentication"
    if read_view_url(url):
        return None
    if any(
        token in {"export", "download", "print", "generate", "install", "uninstall", "refund"}
        for token in tokens
    ):
        return "action_review_required"
    if write_shaped("GET", url):
        return "action_review_required"
    if any(
        re.search(r"token|secret|password|session|auth|^key$", key, re.I)
        for key, _ in parse_qsl(parsed.query)
    ):
        return "credentials"
    if re.search(r"\.(?:js|css|png|jpg|jpeg|gif|svg|ico|pdf|csv|xlsx?|zip)$", parsed.path, re.I):
        return "asset_or_download"
    return None


def private_page_family(url: str) -> str:
    """Private structural key; never return this value through the inspector."""
    parts = [part for part in unquote(urlsplit(url).path).split("/") if part]
    if len(parts) >= 3 and (
        parts[0] in {"people", "tags", "forms", "events"}
        and parts[1] in {"view", "entries", "people", "reports", "settings", "volunteers2"}
    ):
        parts[2] = "{entity}"
    elif (
        len(parts) >= 3
        and (
            (parts[0] == "people" and parts[2] in {"notes", "tags"})
            or (parts[0] == "events" and parts[2] in {"plan", "attachments"})
        )
        or len(parts) >= 2
        and parts[0] in {"groups", "songs", "form"}
    ):
        parts[1] = "{entity}"
    elif len(parts) >= 4 and parts[:3] == ["payments", "pledges", "fundraiser"]:
        parts[3] = "{entity}"
    return "/" + "/".join("{entity}" if re.fullmatch(r"[0-9]+", part) else part for part in parts)


def derived_page_routes(url: str, origin: str) -> list[str]:
    """Bind public aliases only to identifiers in eligible observed links."""
    if link_exclusion(url, origin) is not None:
        return []
    path = urlsplit(url).path
    person = re.fullmatch(r"/people/view/([0-9]{1,16})(?:/[a-z_]+)?/?", path)
    attendance = re.fullmatch(r"/events/people/([0-9]{1,16})/?", path)
    plan = re.fullmatch(r"/events/([0-9]{1,16})/plan/?", path)
    if person:
        identifier = person[1]
        return [
            origin + route
            for route in (
                f"/people/{identifier}/notes",
                f"/people/{identifier}/tags",
                f"/people/view/{identifier}/message",
            )
        ]
    if attendance:
        return [origin + f"/events/people/{attendance[1]}/out"]
    if plan:
        return [origin + f"/events/{plan[1]}/attachments"]
    return []


def metadata(event: dict[str, object], origin: str) -> dict[str, object] | None:
    params = obj(event.get("params", {}))
    request = obj(params.get("request", {}))
    url = request.get("url")
    if not isinstance(url, str) or not url.startswith(origin + "/"):
        return None
    headers = request.get("headers", [])
    names = (
        {str(obj(header).get("name", "")).lower() for header in headers if isinstance(header, dict)}
        if isinstance(headers, list)
        else set()
    )
    response = obj(params.get("response", {}))
    method = request.get("method", "UNKNOWN")
    error = str(params.get("errorText", ""))
    error_codes = {
        "NS_ERROR_DOM_BAD_URI",
        "NS_ERROR_DOM_ABORT_ERR",
        "NS_BINDING_ABORTED",
        "NS_ERROR_NET_TIMEOUT",
        "NS_ERROR_FAILURE",
        "NS_ERROR_UNKNOWN_HOST",
        "NS_ERROR_CONNECTION_REFUSED",
        "NS_ERROR_NET_RESET",
    }
    return {
        "event": event.get("method")
        if event.get("method")
        in {"network.beforeRequestSent", "network.responseCompleted", "network.fetchError"}
        else "network.other",
        "method": method
        if method in {"GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"}
        else "OTHER",
        "path": safe_path(url),
        "query_keys": sorted(
            {key if key in QUERY_FIELDS else "{field}" for key, _ in parse_qsl(urlsplit(url).query)}
        )[:64],
        "cookie_header": "cookie" in names or bool(request.get("cookies")),
        "authorization_header": "authorization" in names,
        "csrf_header": bool(names & {"x-csrf-token", "x-xsrf-token", "csrf-token"}),
        "status": response.get("status") if isinstance(response.get("status"), int) else None,
        "blocked": bool(params.get("isBlocked")) and write_shaped(str(method), url),
        "failure_kind": next((code for code in sorted(error_codes) if code in error), "other")
        if event.get("method") == "network.fetchError"
        else None,
    }


class Inspector:
    def __init__(self, websocket: ClientConnection) -> None:
        self.websocket = websocket
        self.sequence = 0
        self.pending: dict[int, asyncio.Future[dict[str, object]]] = {}
        self.commands: dict[int, str] = {}
        self.guards: set[int] = set()
        self.events: deque[dict[str, object]] = deque(maxlen=2000)
        self.capture = False
        self.keepalive_state = "inactive"
        self.watcher = ""
        self.origin = ""
        self.context = ""
        self.links: dict[str, str] = {}
        self.dashboard_target = ""
        self.discovered_links: dict[str, int] = {}
        self.link_families: dict[str, int] = {}
        self.intercept = ""
        self.subscriptions: list[str] = []
        self.lock = asyncio.Lock()
        self.loaded_navigations: deque[str] = deque(maxlen=100)
        self.navigation_loaded = asyncio.Event()

    async def call(self, method: str, params: dict[str, object]) -> dict[str, object]:
        self.sequence += 1
        identifier = self.sequence
        future = asyncio.get_running_loop().create_future()
        self.pending[identifier] = future
        self.commands[identifier] = method
        try:
            await self.websocket.send(
                json.dumps({"id": identifier, "method": method, "params": params})
            )
            return await asyncio.wait_for(future, timeout=25)
        finally:
            self.pending.pop(identifier, None)
            self.commands.pop(identifier, None)

    async def receive(self) -> None:
        try:
            async for raw in self.websocket:
                message = obj(json.loads(raw))
                identifier = message.get("id")
                if isinstance(identifier, int) and identifier in self.guards:
                    self.guards.remove(identifier)
                    if message.get("type") == "error" and message.get("error") != "no such request":
                        raise InspectionError("Request guard failed; inspection stopped.")
                elif isinstance(identifier, int) and identifier in self.pending:
                    future = self.pending[identifier]
                    if not future.done():
                        if message.get("type") == "error":
                            future.set_exception(
                                InspectionError(
                                    "Browser command failed: " + self.commands[identifier]
                                )
                            )
                        else:
                            future.set_result(obj(message.get("result", {})))
                elif message.get("method") in {
                    "browsingContext.load",
                    "browsingContext.domContentLoaded",
                }:
                    params = obj(message.get("params", {}))
                    identifier = params.get("navigation")
                    if params.get("context") == self.context and isinstance(identifier, str):
                        self.loaded_navigations.append(identifier)
                        self.navigation_loaded.set()
                elif self.capture and str(message.get("method", "")).startswith("network."):
                    entry = metadata(message, self.origin)
                    origin_kind = "account"
                    if entry is None:
                        entry = metadata(message, "https://api.breezechms.com")
                        origin_kind = "central_api"
                    if entry is not None:
                        entry["origin_kind"] = origin_kind
                        self.events.append(entry)
                    params = obj(message.get("params", {}))
                    if params.get("isBlocked"):
                        request = obj(params.get("request", {}))
                        # Send without waiting in the receiver; its response is
                        # consumed here normally. Never replay a blocked request.
                        self.sequence += 1
                        self.guards.add(self.sequence)
                        method = (
                            "network.failRequest"
                            if write_shaped(
                                str(request.get("method", "")), str(request.get("url", ""))
                            )
                            else "network.continueRequest"
                        )
                        await self.websocket.send(
                            json.dumps(
                                {
                                    "id": self.sequence,
                                    "method": method,
                                    "params": {"request": request.get("request")},
                                }
                            )
                        )
            raise InspectionError("Browser connection ended; inspection stopped.")
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(
                        InspectionError("Browser connection ended; inspection stopped.")
                    )

    async def page(self) -> dict[str, object]:
        tree = await self.call("browsingContext.getTree", {"maxDepth": 0})
        contexts = tree.get("contexts")
        if not isinstance(contexts, list) or len(contexts) != 1:
            raise InspectionError("Keep exactly one tab in the isolated inspection window.")
        context = obj(contexts[0])
        self.context = str(context.get("context", ""))
        parsed = urlsplit(str(context.get("url", "")))
        valid = parsed.scheme == "https" and bool(
            re.fullmatch(r"[a-z0-9-]+\.breezechms\.com", parsed.hostname or "")
        )
        if not valid:
            raise InspectionError("Open your Breeze account in the inspection window.")
        if restricted_page(str(context.get("url", ""))):
            raise InspectionError("Account and API settings are excluded from inspection.")
        origin = f"https://{parsed.hostname}"
        if self.capture and origin != self.origin:
            raise InspectionError("Inspection account changed; pause capture first.")
        self.origin = origin
        return {
            "path": safe_path(str(context.get("url", ""))),
            "capture": self.capture,
            "events": len(self.events),
            "keepalive": self.keepalive_state,
        }

    async def navigation(self) -> dict[str, object]:
        await self.page()
        expression = (
            "JSON.stringify(Array.from(document.querySelectorAll('a[href]')).map(a=>({label:"
            "a.textContent.replace(/\\s+/g,' ').trim(),url:a.href})).filter(a=>"
            + json.dumps(sorted(PAGES))
            + ".includes(a.label)))"
        )
        response = await self.call(
            "script.evaluate",
            {"expression": expression, "target": {"context": self.context}, "awaitPromise": False},
        )
        value = obj(response.get("result", {})).get("value")
        if not isinstance(value, str):
            raise InspectionError("Navigation contract changed.")
        self.links = {}
        global_paths = {
            "Dashboard": {"/dashboard", "/r/dashboard"},
            "People": {"/people", "/r/people"},
            "Giving": {"/payments", "/payments/reports"},
            "Tags": {"/tags", "/r/tags"},
            "Events": {"/events", "/r/events"},
            "Forms": {"/forms", "/forms/all"},
        }
        for raw in json.loads(value):
            link = obj(raw)
            label, url = link.get("label"), link.get("url")
            if (
                isinstance(label, str)
                and label in PAGES
                and isinstance(url, str)
                and url.startswith(self.origin + "/")
                and not write_shaped("GET", url)
                and urlsplit(url).path in global_paths[label]
                and not urlsplit(url).query
            ):
                self.links[label] = url
                if label == "Dashboard":
                    self.dashboard_target = url
        return {
            "pages": [{"label": label, "path": safe_path(url)} for label, url in self.links.items()]
        }

    async def discover_links(self) -> dict[str, object]:
        """Discover observed page links; keep URLs private and emit route shapes."""
        await self.page()
        expression = "JSON.stringify((()=>{const docs=[document];let excluded=0;for(const frame of Array.from(window.frames).slice(0,20)){try{if(frame.location.origin!==location.origin)continue;const path=decodeURIComponent(frame.location.pathname).toLowerCase().split('/').map(p=>p.replace(/\\.(php|html)$/,''));if(path.some(p=>['account','account_settings','api-auth','api-key','api-keys','login','logout'].includes(p))||path.filter(Boolean)[0]==='settings'||path.join('/')==='/api'){excluded++;continue;}docs.push(frame.document);}catch{}}const links=[];let truncated=window.frames.length>20;for(const doc of docs){for(const a of doc.querySelectorAll('a[href]')){if(links.length>=20000){truncated=true;break;}if(a.hasAttribute('download'))continue;const href=a.href;if(href.length>4096)continue;try{const u=new URL(href);if(u.username||u.password||Array.from(u.searchParams.keys()).some(k=>/token|secret|password|session|auth|^key$/i.test(k)))continue;if(u.origin===location.origin){u.hash='';links.push(u.href);}}catch{}}}return {links:Array.from(new Set(links)),truncated,excluded_frames:excluded};})())"
        response = await self.call(
            "script.evaluate",
            {"expression": expression, "target": {"context": self.context}, "awaitPromise": False},
        )
        value = obj(response.get("result", {})).get("value")
        if not isinstance(value, str) or len(value) > 2 * 1024 * 1024:
            raise InspectionError("Link inventory contract changed.")
        return self.register_link_inventory(obj(json.loads(value)))

    def register_link_inventory(self, payload: dict[str, object]) -> dict[str, object]:
        """Keep document URLs private and return only masked link metadata."""
        links = payload.get("links")
        if not isinstance(links, list):
            raise InspectionError("Link inventory contract changed.")
        summaries = []
        family_counts = Counter(
            private_page_family(url) for url in self.discovered_links if not urlsplit(url).query
        )
        for url in links:
            if not isinstance(url, str) or len(url) > 4096:
                continue
            reason = link_exclusion(url, self.origin)
            index = None
            if reason is None:
                if not urlsplit(url).query:
                    family = private_page_family(url)
                    if family_counts[family] >= 3 and url not in self.discovered_links:
                        continue
                if url not in self.discovered_links and len(self.discovered_links) < 5000:
                    self.discovered_links[url] = len(self.discovered_links)
                    if not urlsplit(url).query:
                        family_counts[private_page_family(url)] += 1
                index = self.discovered_links.get(url)
            summaries.append(
                {
                    "index": index,
                    "family": self.link_families.setdefault(
                        private_page_family(url), len(self.link_families)
                    ),
                    "path": safe_path(url),
                    "query_keys": sorted(
                        {
                            key if key in QUERY_FIELDS else "{field}"
                            for key, _ in parse_qsl(urlsplit(url).query)
                        }
                    ),
                    "excluded": reason,
                    "action_tokens": sorted(
                        {
                            match.group(1).lower()
                            for token in re.split(r"[/_.-]", unquote(urlsplit(url).path))
                            if (match := WRITE.match(token)) is not None
                        }
                    )
                    if reason == "action_review_required"
                    else [],
                }
            )
        return {
            "links": summaries,
            "truncated": bool(payload.get("truncated")) or len(self.discovered_links) >= 5000,
            "excluded_frames": payload.get("excluded_frames", 0),
            "registry_size": len(self.discovered_links),
        }

    async def follow_link(self, index: object) -> dict[str, object]:
        if not self.capture:
            raise InspectionError("Start guarded capture before following page links.")
        await self.page()
        if type(index) is not int or not 0 <= index < len(self.discovered_links):
            raise InspectionError("Select an observed page-link index.")
        url = next(url for url, identifier in self.discovered_links.items() if identifier == index)
        if link_exclusion(url, self.origin) is not None:
            raise InspectionError("Link no longer qualifies for read-only page inspection.")
        await self.navigate_to(url)
        return await self.page()

    async def navigate_to(self, url: str) -> None:
        result = await self.call(
            "browsingContext.navigate", {"context": self.context, "url": url, "wait": "interactive"}
        )
        identifier = result.get("navigation")
        if not isinstance(identifier, str):
            raise InspectionError("Navigation identifier unavailable; document is unverified.")
        try:
            async with asyncio.timeout(12):
                while identifier not in self.loaded_navigations:
                    self.navigation_loaded.clear()
                    await self.navigation_loaded.wait()
        except TimeoutError:
            raise InspectionError("Navigation load was not verified before its deadline.") from None

    async def start(self) -> dict[str, object]:
        await self.page()
        if self.capture:
            return {"capture": True}
        response = await self.call(
            "script.evaluate",
            {
                "expression": "Array.from(document.querySelectorAll('input[type=password]')).filter(e=>e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden').length",
                "target": {"context": self.context},
                "awaitPromise": False,
            },
        )
        if obj(response.get("result", {})).get("value") != 0:
            raise InspectionError("Login must finish before capture starts.")
        result = await self.call(
            "session.subscribe",
            {
                "events": [
                    "browsingContext.load",
                    "browsingContext.domContentLoaded",
                    "network.beforeRequestSent",
                    "network.responseCompleted",
                    "network.fetchError",
                ]
            },
        )
        identifier = result.get("subscription")
        if isinstance(identifier, str):
            self.subscriptions.append(identifier)
        self.capture = True
        try:
            result = await self.call(
                "network.addIntercept",
                {
                    "phases": ["beforeRequestSent"],
                    "urlPatterns": [
                        {
                            "type": "pattern",
                            "protocol": "https",
                            "hostname": urlsplit(self.origin).hostname,
                        },
                        {"type": "pattern", "protocol": "https", "hostname": "api.breezechms.com"},
                    ],
                },
            )
            identifier = result.get("intercept")
            if not isinstance(identifier, str) or not identifier:
                raise InspectionError("Browser intercept contract changed.")
            self.intercept = identifier
            self.keepalive_state = "pending"
        except InspectionError, TimeoutError, ConnectionClosed:
            self.capture = False
            await self.unsubscribe()
            raise
        return {"capture": True, "write_guard": True, "response_bodies": False}

    async def unsubscribe(self) -> None:
        if self.subscriptions:
            await self.call("session.unsubscribe", {"subscriptions": self.subscriptions})
            self.subscriptions = []

    async def pause(self) -> dict[str, object]:
        if self.watcher:
            try:
                await self.page()
            except InspectionError:
                pass
            else:
                await self.call(
                    "script.evaluate",
                    {
                        "expression": "globalThis[Symbol.for('breezeInspectionReadSchemas')]?.stop();null",
                        "target": {"context": self.context},
                        "awaitPromise": False,
                    },
                )
            await self.call("script.removePreloadScript", {"script": self.watcher})
            self.watcher = ""
        if self.intercept:
            await self.call("network.removeIntercept", {"intercept": self.intercept})
            self.intercept = ""
        await self.unsubscribe()
        self.capture = False
        return {"capture": False}

    async def keepalive(self) -> dict[str, object]:
        """Probe the approved Dashboard document without reading its body."""
        if not self.capture:
            raise InspectionError("Start guarded capture before a session keepalive.")
        await self.navigation()
        target = self.links.get("Dashboard") or self.dashboard_target
        if not target or not re.fullmatch(r"/(?:[a-z0-9_-]+/)?dashboard/?", urlsplit(target).path):
            raise InspectionError("An approved Dashboard link is required for keepalive.")
        source = Path(__file__).with_name("browser_session.js").read_text()
        response = await self.call(
            "script.evaluate",
            {
                "expression": source + "\ninspectBrowserSession(" + json.dumps(target) + ")",
                "target": {"context": self.context},
                "awaitPromise": True,
            },
        )
        encoded = obj(response.get("result", {})).get("value")
        if not isinstance(encoded, str):
            raise InspectionError("Session keepalive contract changed.")
        result = obj(json.loads(encoded))
        state = result.get("state")
        if state not in {"healthy", "login_required", "request_failed", "target_rejected"}:
            raise InspectionError("Session keepalive contract changed.")
        self.keepalive_state = str(state)
        if state != "healthy":
            await self.pause()
        status = result.get("http_status")
        return {
            "state": state,
            "http_status": status if type(status) is int else None,
            "interval_seconds": 120,
            "capture": self.capture,
        }

    async def maintain_session(self) -> None:
        while True:
            await asyncio.sleep(120)
            async with self.lock:
                if self.capture:
                    try:
                        await self.keepalive()
                    except InspectionError, TimeoutError, ConnectionClosed:
                        self.keepalive_state = "request_failed"
                        await self.pause()

    async def watch_reads(self) -> dict[str, object]:
        if not self.capture:
            raise InspectionError("Start guarded capture before observing read schemas.")
        await self.page()
        if self.watcher:
            return {"watching": True}
        source = Path(__file__).with_name("browser_read_schemas.js").read_text()
        install = (
            "(() => {"
            + source
            + "\nreturn installBreezeReadSchemas("
            + json.dumps(self.origin)
            + ");})()"
        )
        result = await self.call(
            "script.addPreloadScript",
            {
                "functionDeclaration": "() => {" + install + "}",
            },
        )
        identifier = result.get("script")
        if not isinstance(identifier, str) or not identifier:
            raise InspectionError("Read-schema preload contract changed.")
        self.watcher = identifier
        result = await self.call(
            "script.evaluate",
            {
                "expression": install,
                "target": {"context": self.context},
                "awaitPromise": False,
            },
        )
        value = obj(result.get("result", {})).get("value")
        if not isinstance(value, str) or obj(json.loads(value)).get("installed") is not True:
            await self.pause()
            raise InspectionError("Read-schema hook was not installed.")
        return {"watching": True, "raw_bodies": False, "limit": 20}

    async def read_schemas(self) -> dict[str, object]:
        if not self.capture or not self.watcher:
            raise InspectionError("Start guarded read-schema observation first.")
        await self.page()
        result = await self.call(
            "script.evaluate",
            {
                "expression": "JSON.stringify(globalThis[Symbol.for('breezeInspectionReadSchemas')]?.summarize()||{observer_installed:false,samples:[],frames:[],truncated:false})",
                "target": {"context": self.context},
                "awaitPromise": False,
            },
        )
        value = obj(result.get("result", {})).get("value")
        if not isinstance(value, str) or len(value) > 128 * 1024:
            raise InspectionError("Read-schema summary contract changed.")
        return obj(json.loads(value))

    async def operation(self, request: dict[str, object]) -> dict[str, object]:
        async with self.lock:
            operation = request.get("op")
            if operation == "status":
                return await self.page()
            if operation == "document-state":
                await self.page()
                response = await self.call(
                    "script.evaluate",
                    {
                        "expression": "JSON.stringify({account_origin:globalThis.location.origin==="
                        + json.dumps(self.origin)
                        + ",protocol:/^[a-z-]{1,32}:$/.test(globalThis.location.protocol)?globalThis.location.protocol:'other',location_type:typeof globalThis.location.origin,browser_error:globalThis.location.protocol==='about:',https_document:globalThis.location.protocol==='https:',breeze_document:/^[a-z0-9-]+\\.breezechms\\.com$/.test(globalThis.location.hostname),opaque_origin:globalThis.location.origin==='null',ready_state:document.readyState,visible_password:Array.from(document.querySelectorAll('input[type=password]')).some(e=>e.getClientRects().length>0&&getComputedStyle(e).visibility!=='hidden')})",
                        "target": {"context": self.context, "sandbox": "breezeDiagnostic"},
                        "awaitPromise": False,
                    },
                )
                value = obj(response.get("result", {})).get("value")
                if not isinstance(value, str):
                    raise InspectionError("Document diagnostic unavailable.")
                return obj(json.loads(value))
            if operation == "reload":
                if not self.capture:
                    raise InspectionError("Start guarded capture before reloading.")
                await self.page()
                await self.call("browsingContext.reload", {"context": self.context, "wait": "none"})
                return {"reload_requested": True, "document_verified": False}
            if operation == "pages":
                return await self.navigation()
            if operation == "links":
                return await self.discover_links()
            if operation == "routes":
                if not self.capture:
                    raise InspectionError("Start guarded capture before public-route discovery.")
                await self.page()
                routes = []
                candidates = [
                    self.origin + path for path in (*PUBLIC_PAGE_ROUTES, *sorted(READ_VIEW_PATHS))
                ]
                candidates.extend(
                    derived
                    for observed in tuple(self.discovered_links)
                    for derived in derived_page_routes(observed, self.origin)
                )
                for url in dict.fromkeys(candidates):
                    path = urlsplit(url).path
                    if link_exclusion(url, self.origin) is not None:
                        continue
                    if url not in self.discovered_links:
                        if len(self.discovered_links) >= 5000:
                            raise InspectionError("Page-link registry reached its bound.")
                        self.discovered_links[url] = len(self.discovered_links)
                    if path == "/dashboard":
                        self.dashboard_target = url
                    routes.append(
                        {
                            "index": self.discovered_links[url],
                            "family": self.link_families.setdefault(
                                private_page_family(url), len(self.link_families)
                            ),
                            "path": safe_path(url),
                            "query_keys": [],
                            "excluded": None,
                            "source": "public_client_route"
                            if path in PUBLIC_PAGE_ROUTES
                            else "public_route_from_observed_identifier",
                        }
                    )
                return {"links": routes, "truncated": False}
            if operation == "read-page":
                if not self.capture or not self.watcher:
                    raise InspectionError(
                        "Guarded schema observation is required for document reads."
                    )
                await self.page()
                index = request.get("link")
                if type(index) is not int or not 0 <= index < len(self.discovered_links):
                    raise InspectionError("Select an observed page-link index.")
                url = next(
                    url for url, identifier in self.discovered_links.items() if identifier == index
                )
                if link_exclusion(url, self.origin) is not None:
                    raise InspectionError(
                        "Link no longer qualifies for read-only document inspection."
                    )
                source = (
                    Path(__file__)
                    .with_name("browser_document_read.js")
                    .read_text()
                    .replace(
                        "// PAGE_SCANNER",
                        Path(__file__).with_name("browser_page_contracts.js").read_text(),
                    )
                )
                source = (
                    Path(__file__).with_name("browser_read_schemas.js").read_text() + "\n" + source
                )
                response = await self.call(
                    "script.evaluate",
                    {
                        "expression": "(()=>{"
                        + source
                        + "\nreturn inspectReadonlyBrowserDocument("
                        + json.dumps(url)
                        + ","
                        + json.dumps(self.origin)
                        + ");})()",
                        "target": {"context": self.context},
                        "awaitPromise": True,
                    },
                )
                value = obj(response.get("result", {})).get("value")
                if not isinstance(value, str) or len(value) > 2 * 1024 * 1024:
                    raise InspectionError("Document summary contract changed.")
                payload = obj(json.loads(value))
                summary = self.register_link_inventory(payload)
                summary.update(
                    {
                        key: payload[key]
                        for key in (
                            "state",
                            "http_status",
                            "declarations",
                            "contract_truncated",
                            "tag_counts",
                        )
                        if key in payload
                    }
                )
                if payload.get("state") == "login_required":
                    await self.pause()
                return summary
            if operation == "follow":
                return await self.follow_link(request.get("link"))
            if operation == "menu":
                if not self.capture:
                    raise InspectionError("Start guarded capture before opening navigation.")
                await self.page()
                label = request.get("menu_label") or "More"
                if not isinstance(label, str) or label not in MENUS:
                    raise InspectionError("Select an approved navigation menu.")
                result = await self.call(
                    "script.evaluate",
                    {
                        "expression": "JSON.stringify((()=>{const label="
                        + json.dumps(label)
                        + ";const norm=s=>(s||'').replace(/\\s+/g,' ').trim();const items=Array.from(document.querySelectorAll('button,[role=button]')).filter(e=>[e.textContent,e.getAttribute('aria-label'),e.getAttribute('title')].some(s=>norm(s)===label)&&e.getClientRects().length>0&&!e.closest('form'));if(items.length!==1)return {opened:false,matches:items.length};items[0].click();return {opened:true}})())",
                        "target": {"context": self.context},
                        "awaitPromise": False,
                    },
                )
                value = obj(result.get("result", {})).get("value")
                if not isinstance(value, str):
                    raise InspectionError("Navigation menu contract changed.")
                return obj(json.loads(value))
            if operation == "controls":
                await self.page()
                expression = (
                    "JSON.stringify(Array.from(document.querySelectorAll('a,button,[role=button],[title],[aria-label]')).flatMap(e=>{const labels="
                    + json.dumps(sorted(PAGES | MENUS))
                    + ";const norm=s=>(s||'').replace(/\\s+/g,' ').trim();const label=[e.textContent,e.getAttribute('aria-label'),e.getAttribute('title')].map(norm).find(s=>labels.includes(s));return label?[{label,tag:e.tagName,visible:e.getClientRects().length>0,link:e.hasAttribute('href')}]:[]}).slice(0,100))"
                )
                result = await self.call(
                    "script.evaluate",
                    {
                        "expression": expression,
                        "target": {"context": self.context},
                        "awaitPromise": False,
                    },
                )
                value = obj(result.get("result", {})).get("value")
                if not isinstance(value, str):
                    raise InspectionError("Control inspection contract changed.")
                controls = json.loads(value)
                buttons = await self.call(
                    "script.evaluate",
                    {
                        "expression": "JSON.stringify(Array.from(document.querySelectorAll('button')).filter(e=>e.getClientRects().length>0&&e.getBoundingClientRect().top<120).map(e=>({has_image:!!e.querySelector('img'),has_svg:!!e.querySelector('svg'),in_navigation:!!e.closest('header,nav'),is_more:e.textContent.trim()==='More',expanded:e.getAttribute('aria-expanded')==='true'})).slice(0,20))",
                        "target": {"context": self.context},
                        "awaitPromise": False,
                    },
                )
                encoded = obj(buttons.get("result", {})).get("value")
                if not isinstance(encoded, str):
                    raise InspectionError("Navigation structure contract changed.")
                return {"controls": controls, "navigation_buttons": json.loads(encoded)}
            if operation == "capture":
                return await self.start()
            if operation == "pause":
                return await self.pause()
            if operation == "keepalive":
                return await self.keepalive()
            if operation == "watch-reads":
                return await self.watch_reads()
            if operation == "read-schemas":
                return await self.read_schemas()
            if operation in {
                "probe-native-people",
                "probe-native-person",
                "probe-native-contributions",
            }:
                if not self.capture or not self.watcher:
                    raise InspectionError(
                        "Guarded schema observation is required for native replay."
                    )
                await self.page()
                method = {
                    "probe-native-person": "probePerson",
                    "probe-native-people": "probePeople",
                    "probe-native-contributions": "probeContributions",
                }[str(operation)]
                result = await self.call(
                    "script.evaluate",
                    {
                        "expression": "(async()=>{const state=globalThis[Symbol.for('breezeInspectionReadSchemas')];return state?."
                        + method
                        + "?await state."
                        + method
                        + "():JSON.stringify({state:'template_unavailable'});})()",
                        "target": {"context": self.context},
                        "awaitPromise": True,
                    },
                )
                value = obj(result.get("result", {})).get("value")
                if not isinstance(value, str) or len(value) > 128 * 1024:
                    raise InspectionError("Native replay summary contract changed.")
                summary = obj(json.loads(value))
                if summary.get("state") == "login_required":
                    await self.pause()
                return summary
            if operation in {"probe-people", "probe-v2-people"}:
                if not self.capture:
                    raise InspectionError("Start guarded capture before the reviewed People probe.")
                await self.page()
                source = Path(__file__).with_name("browser_read_schemas.js").read_text()
                filename = (
                    "browser_v2_probe.js"
                    if operation == "probe-v2-people"
                    else "browser_read_probe.js"
                )
                function = (
                    "probeBreezeV2People" if operation == "probe-v2-people" else "probeBreezePeople"
                )
                source += "\n" + Path(__file__).with_name(filename).read_text()
                result = await self.call(
                    "script.evaluate",
                    {
                        "expression": "(async () => {"
                        + source
                        + "\nreturn await "
                        + function
                        + "();})()",
                        "target": {"context": self.context},
                        "awaitPromise": True,
                    },
                )
                value = obj(result.get("result", {})).get("value")
                if not isinstance(value, str) or len(value) > 128 * 1024:
                    raise InspectionError("People probe summary contract changed.")
                return obj(json.loads(value))
            if operation in {"list-controls", "next-page"}:
                await self.page()
                if operation == "next-page":
                    if not self.capture or not self.watcher:
                        raise InspectionError(
                            "Guarded schema observation is required for pagination."
                        )
                    tree = await self.call("browsingContext.getTree", {"maxDepth": 0})
                    contexts = tree.get("contexts")
                    if not isinstance(contexts, list) or not contexts:
                        raise InspectionError("Pagination page contract changed.")
                    path = urlsplit(str(obj(contexts[0]).get("url", ""))).path
                    if not path.startswith("/forms/"):
                        raise InspectionError("Only the reviewed Forms pagination is enabled.")
                expression = Path(__file__).with_name("browser_list_controls.js").read_text()
                result = await self.call(
                    "script.evaluate",
                    {
                        "expression": expression
                        + "\ninspectBreezeListControls("
                        + json.dumps(operation == "next-page")
                        + ")",
                        "target": {"context": self.context},
                        "awaitPromise": False,
                    },
                )
                value = obj(result.get("result", {})).get("value")
                if not isinstance(value, str):
                    raise InspectionError("List control contract changed.")
                return obj(json.loads(value))
            if operation == "events":
                return {"events": list(self.events), "limit": 2000}
            if operation in {
                "assets",
                "source",
                "source-selftest",
                "session-selftest",
                "page-contracts",
                "page-selftest",
                "read-selftest",
                "list-selftest",
                "probe-selftest",
                "v2-selftest",
                "native-selftest",
                "document-selftest",
            }:
                return await self.source(request)
            if operation == "navigate":
                if not self.capture:
                    raise InspectionError("Start guarded capture before navigation.")
                await self.navigation()
                label = request.get("page")
                if not isinstance(label, str) or label not in self.links:
                    raise InspectionError("Requested page is not an approved navigation link.")
                target = (
                    self.origin + "/payments/reports" if label == "Giving" else self.links[label]
                )
                await self.navigate_to(target)
                return await self.page()
            raise InspectionError("Unsupported inspection command.")

    async def source(self, request: dict[str, object]) -> dict[str, object]:
        """Fixed static-source scanner; no caller-provided expressions or URLs."""
        await self.page()
        operation = request.get("op")
        index = request.get("asset")
        if operation == "source" and (type(index) is not int or not 0 <= index <= 1000):
            raise InspectionError("Select a listed asset index.")
        dependency = request.get("dependency")
        if dependency is not None and (type(dependency) is not int or not 0 <= dependency <= 1000):
            raise InspectionError("Select a listed dependency index.")
        source = Path(__file__).with_name("browser_source.js").read_text()
        if operation == "native-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_native_probe_test.js")
                .read_text()
                .replace(
                    "// READ_SCANNER",
                    Path(__file__).with_name("browser_read_schemas.js").read_text(),
                )
            )
        elif operation == "v2-selftest":
            scanner = (
                Path(__file__)
                .with_name("browser_v2_probe.js")
                .read_text()
                .replace("await import(moduleUrl)", "await loadSyntheticFrontend(moduleUrl)")
            )
            expression = (
                Path(__file__)
                .with_name("browser_v2_probe_test.js")
                .read_text()
                .replace(
                    "// READ_SCANNER",
                    Path(__file__).with_name("browser_read_schemas.js").read_text(),
                )
                .replace("// V2_SCANNER", scanner)
            )
        elif operation == "probe-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_read_probe_test.js")
                .read_text()
                .replace(
                    "// READ_SCANNER",
                    Path(__file__).with_name("browser_read_schemas.js").read_text(),
                )
                .replace(
                    "// PROBE_SCANNER",
                    Path(__file__).with_name("browser_read_probe.js").read_text(),
                )
            )
        elif operation == "list-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_list_controls_test.js")
                .read_text()
                .replace(
                    "// LIST_SCANNER",
                    Path(__file__).with_name("browser_list_controls.js").read_text(),
                )
            )
        elif operation == "read-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_read_schemas_test.js")
                .read_text()
                .replace(
                    "// READ_SCANNER",
                    Path(__file__).with_name("browser_read_schemas.js").read_text(),
                )
            )
        elif operation in {"page-contracts", "page-selftest"}:
            scanner = Path(__file__).with_name("browser_page_contracts.js").read_text()
            expression = scanner + "\ninspectPageContracts()"
            if operation == "page-selftest":
                expression = (
                    Path(__file__)
                    .with_name("browser_page_contracts_test.js")
                    .read_text()
                    .replace("// PAGE_SCANNER", scanner)
                )
        elif operation == "document-selftest":
            scanner = (
                Path(__file__)
                .with_name("browser_document_read.js")
                .read_text()
                .replace(
                    "// PAGE_SCANNER",
                    Path(__file__).with_name("browser_page_contracts.js").read_text(),
                )
            )
            expression = (
                Path(__file__)
                .with_name("browser_document_read_test.js")
                .read_text()
                .replace(
                    "// READ_SCANNER",
                    Path(__file__).with_name("browser_read_schemas.js").read_text(),
                )
                .replace("// DOCUMENT_SCANNER", scanner)
            )
        elif operation == "session-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_session_test.js")
                .read_text()
                .replace(
                    "// SESSION_SCANNER", Path(__file__).with_name("browser_session.js").read_text()
                )
            )
        elif operation == "source-selftest":
            expression = (
                Path(__file__)
                .with_name("browser_source_test.js")
                .read_text()
                .replace("// SOURCE_SCANNER", source)
            )
        else:
            expression = (
                source
                + "\ninspectBrowserSource("
                + json.dumps(operation)
                + ","
                + json.dumps(index)
                + ","
                + json.dumps(dependency)
                + ")"
            )
        response = await self.call(
            "script.evaluate",
            {"expression": expression, "target": {"context": self.context}, "awaitPromise": True},
        )
        value = obj(response.get("result", {})).get("value")
        if not isinstance(value, str) or len(value) > 512 * 1024:
            raise InspectionError("Static source inspection contract changed.")
        return obj(json.loads(value))

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=5)
            result = await self.operation(obj(json.loads(raw)))
            payload = {"ok": True, "result": result}
        except InspectionError as error:
            payload = {"ok": False, "error": str(error)}
        except ValueError, OSError, TimeoutError, ConnectionClosed:
            payload = {"ok": False, "error": "Inspection stopped; check browser and capture state."}
        try:
            writer.write(json.dumps(payload).encode() + b"\n")
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


async def serve() -> None:
    info = obj(json.loads((ROOT / "browser.json").read_text()))
    port = info.get("port")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise InspectionError("Invalid local debugger port.")
    path = ROOT / "control.sock"
    if path.exists():
        raise InspectionError(
            "Inspection socket already exists; check its process before restarting."
        )
    async with connect(
        f"ws://127.0.0.1:{port}/session",
        proxy=None,
        open_timeout=5,
        close_timeout=2,
        max_size=2 * 1024 * 1024,
    ) as websocket:
        inspector = Inspector(websocket)
        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(inspector.receive())
            await inspector.call("session.new", {"capabilities": {}})
            tasks.create_task(inspector.maintain_session())
            server = await asyncio.start_unix_server(inspector.handle, path=path, limit=8192)
            path.chmod(0o600)
            try:
                async with server:
                    current = asyncio.current_task()
                    if current is not None:
                        asyncio.get_running_loop().add_signal_handler(
                            signal.SIGTERM, current.cancel
                        )
                    await server.serve_forever()
            finally:
                path.unlink(missing_ok=True)
                try:
                    await inspector.pause()
                    await inspector.call("session.end", {})
                except InspectionError, ConnectionClosed, TimeoutError:
                    pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=[
            "launch",
            "serve",
            "status",
            "document-state",
            "reload",
            "pages",
            "links",
            "routes",
            "follow",
            "read-page",
            "menu",
            "controls",
            "capture",
            "pause",
            "events",
            "navigate",
            "assets",
            "source",
            "source-selftest",
            "session-selftest",
            "keepalive",
            "page-contracts",
            "page-selftest",
            "read-selftest",
            "watch-reads",
            "read-schemas",
            "list-controls",
            "next-page",
            "list-selftest",
            "probe-people",
            "probe-selftest",
            "probe-v2-people",
            "v2-selftest",
            "probe-native-people",
            "probe-native-person",
            "probe-native-contributions",
            "native-selftest",
            "document-selftest",
        ],
    )
    parser.add_argument("--page", choices=sorted(PAGES))
    parser.add_argument("--menu-label", choices=sorted(MENUS))
    parser.add_argument("--asset", type=int)
    parser.add_argument("--dependency", type=int)
    parser.add_argument("--link", type=int)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.operation == "launch":
            print(json.dumps(launch(), sort_keys=True))
        elif args.operation == "serve":
            asyncio.run(serve())
        else:
            with socket.socket(socket.AF_UNIX) as connection:
                connection.settimeout(30)
                connection.connect(str(ROOT / "control.sock"))
                connection.sendall(
                    json.dumps(
                        {
                            "op": args.operation,
                            "page": args.page,
                            "asset": args.asset,
                            "dependency": args.dependency,
                            "link": args.link,
                            "menu_label": args.menu_label,
                        }
                    ).encode()
                    + b"\n"
                )
                content = bytearray()
                while not content.endswith(b"\n"):
                    chunk = connection.recv(65536)
                    if not chunk or len(content) + len(chunk) > 2 * 1024 * 1024:
                        raise InspectionError("Incomplete or excessive inspection response.")
                    content.extend(chunk)
                payload = obj(json.loads(content))
                print(json.dumps(payload, sort_keys=True))
                return 0 if payload.get("ok") else 1
        return 0
    except ValueError, OSError, TimeoutError, ConnectionClosed, InvalidStatus, ExceptionGroup:
        print("Browser inspection failed; no raw browser values are printed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
