"""Synthetic privacy and read-only boundaries for the optional browser inspector."""

import asyncio
import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

spec = importlib.util.spec_from_file_location(
    "browser_inspect", Path(__file__).resolve().parents[1] / "scripts/browser_inspect.py"
)
assert spec is not None and spec.loader is not None
browser_inspect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(browser_inspect)
InspectionError = browser_inspect.InspectionError
Inspector = browser_inspect.Inspector
metadata = browser_inspect.metadata
safe_path = browser_inspect.safe_path
write_shaped = browser_inspect.write_shaped


def test_request_metadata_never_discloses_secret_values_or_records() -> None:
    entry = metadata(
        {
            "method": "network.beforeRequestSent",
            "params": {
                "isBlocked": True,
                "request": {
                    "method": "POST",
                    "url": "https://demo.breezechms.com/people/PrivateName?id=private-id&PrivateName=secret",
                    "headers": [
                        {"name": "Cookie", "value": "private-session"},
                        {"name": "Authorization", "value": "private-token"},
                        {"name": "X-CSRF-Token", "value": "private-csrf"},
                    ],
                    "body": "private-body",
                },
                "response": {"status": 403, "body": "private-records"},
            },
        },
        "https://demo.breezechms.com",
    )
    assert entry is not None
    assert entry["path"] == "/people/{segment}"
    assert entry["query_keys"] == ["id", "{field}"]
    assert entry["cookie_header"] is True
    assert entry["authorization_header"] is True
    assert entry["csrf_header"] is True
    assert entry["blocked"] is True
    assert "private" not in json.dumps(entry).lower()
    assert "PrivateName" not in json.dumps(entry)


def test_cross_origin_events_are_excluded() -> None:
    assert (
        metadata(
            {"params": {"request": {"url": "https://demo.breezechms.com.evil.example/people"}}},
            "https://demo.breezechms.com",
        )
        is None
    )
    assert safe_path("https://demo.breezechms.com/people/123?token=secret") == "/people/{segment}"
    assert safe_path("https://demo.breezechms.com/people/v2") == "/people/{segment}"
    assert safe_path("https://api.breezechms.com/api/v2/people") == "/api/v2/people"


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("/people/view/123", None),
        ("/forms/entries/123", None),
        ("/account/api", "account_excluded"),
        ("/events/settings/123", None),
        ("/settings.html", "account_excluded"),
        ("/api.php", "account_excluded"),
        ("/%61ccount/account_settings", "account_excluded"),
        ("/login", "authentication"),
        ("/oauth/authorize", "authentication"),
        ("/people/delete/123", "action_review_required"),
        ("/people/export", "action_review_required"),
        ("/extensions/install/123", "action_review_required"),
        ("/forms/entries/123?token=private-token", "credentials"),
    ],
)
def test_observed_link_exclusions(path: str, reason: str | None) -> None:
    origin = "https://demo.breezechms.com"
    assert browser_inspect.link_exclusion(origin + path, origin) == reason


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("/people/view/123", ["/people/123/notes", "/people/123/tags", "/people/view/123/message"]),
        ("/events/people/123", ["/events/people/123/out"]),
        ("/events/456/plan", ["/events/456/attachments"]),
        ("/events/view/123", []),
        ("/people/view/private-name", []),
        ("/people/view/123?token=private", []),
        ("/account/123", []),
    ],
)
def test_public_dynamic_routes_use_only_observed_typed_identifiers(
    path: str, expected: list[str]
) -> None:
    origin = "https://demo.breezechms.com"
    assert browser_inspect.derived_page_routes(origin + path, origin) == [
        origin + route for route in expected
    ]
    assert browser_inspect.derived_page_routes("https://other.breezechms.com" + path, origin) == []


def test_private_route_families_distinguish_masked_screens_and_group_record_ids() -> None:
    origin = "https://demo.breezechms.com"
    first, second = origin + "/communications/queued", origin + "/communications/scheduled"
    assert safe_path(first) == safe_path(second)
    assert browser_inspect.private_page_family(first) != browser_inspect.private_page_family(second)
    assert browser_inspect.private_page_family(origin + "/people/view/123/notes") == (
        browser_inspect.private_page_family(origin + "/people/view/456/notes")
    )


def test_public_route_discovery_keeps_observed_identifiers_private() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.origin = "https://demo.breezechms.com"
        inspector.capture = True
        inspector.page = AsyncMock(return_value={})
        inspector.discovered_links[inspector.origin + "/people/view/987654321"] = 0
        result = await inspector.operation({"op": "routes"})
        assert "987654321" not in json.dumps(result)
        assert any(link["path"] == "/people/{segment}/notes" for link in result["links"])
        assert all(isinstance(link["family"], int) for link in result["links"])
        assert inspector.origin + "/people/987654321/notes" in inspector.discovered_links
        assert all("account" not in link["path"] for link in result["links"])

    asyncio.run(exercise())


def test_link_inventory_keeps_names_ids_and_query_values_private() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.origin = "https://demo.breezechms.com"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            return_value={
                "result": {
                    "value": json.dumps(
                        {
                            "links": [
                                inspector.origin
                                + "/people/view/PrivatePerson?person_id=private-id",
                                inspector.origin + "/account/api",
                                "https://evil.example/people",
                            ],
                            "truncated": False,
                            "excluded_frames": 1,
                        }
                    )
                }
            }
        )
        result = await inspector.discover_links()
        assert result["registry_size"] == 1
        assert "PrivatePerson" not in json.dumps(result)
        assert "private-id" not in json.dumps(result)
        inspector.capture = True
        inspector.call = AsyncMock(return_value={"navigation": "synthetic-navigation"})
        inspector.loaded_navigations.append("synthetic-navigation")
        with pytest.raises(InspectionError):
            await inspector.follow_link(1)
        inspector.call.assert_not_awaited()
        await inspector.follow_link(0)
        assert inspector.call.await_args is not None
        assert inspector.call.await_args.args[1]["url"].endswith(
            "PrivatePerson?person_id=private-id"
        )
        inspector.origin = "https://changed.breezechms.com"
        inspector.call.reset_mock()
        with pytest.raises(InspectionError):
            await inspector.follow_link(0)
        inspector.call.assert_not_awaited()

    asyncio.run(exercise())


def test_document_read_requires_guard_and_redacts_links_before_returning() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock()
        with pytest.raises(InspectionError, match="Guarded"):
            await inspector.operation({"op": "read-page", "link": 0})
        inspector.call.assert_not_awaited()
        inspector.capture = True
        inspector.watcher = "synthetic-preload"
        inspector.origin = "https://demo.breezechms.com"
        inspector.discovered_links[inspector.origin + "/events/people/123/out"] = 0
        inspector.call = AsyncMock(
            return_value={
                "result": {
                    "value": json.dumps(
                        {
                            "state": "html_inspected",
                            "http_status": 200,
                            "declarations": [],
                            "links": [inspector.origin + "/people/view/PrivatePerson"],
                            "private_body": "SYNTHETIC_PRIVATE_RECORD",
                        }
                    )
                }
            }
        )
        result = await inspector.operation({"op": "read-page", "link": 0})
        assert result["state"] == "html_inspected"
        assert "PrivatePerson" not in json.dumps(result)
        assert "SYNTHETIC_PRIVATE" not in json.dumps(result)
        assert result["links"][0]["path"] == "/people/view/{segment}"
        inspector.call.reset_mock()
        with pytest.raises(InspectionError, match="observed"):
            await inspector.operation({"op": "read-page", "link": True})
        inspector.call.assert_not_awaited()

    asyncio.run(exercise())


def test_failure_metadata_keeps_only_fixed_error_categories() -> None:
    event = {
        "method": "network.fetchError",
        "params": {
            "request": {
                "url": "https://demo.breezechms.com/api/v2/auth/sessionkey",
                "method": "GET",
            },
            "errorText": "NS_ERROR_DOM_BAD_URI private-account private-token",
        },
    }
    result = metadata(event, "https://demo.breezechms.com")
    assert result is not None
    assert result["failure_kind"] == "NS_ERROR_DOM_BAD_URI"
    assert result["path"] == "/api/v2/auth/sessionkey"
    assert "private" not in json.dumps(result)


@pytest.mark.parametrize("state", ["healthy", "login_required", "request_failed"])
def test_keepalive_uses_approved_link_and_pauses_on_failure(state: str) -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.capture = True
        inspector.links = {"Dashboard": "https://demo.breezechms.com/dashboard"}
        inspector.navigation = AsyncMock(return_value={})
        inspector.pause = AsyncMock()
        inspector.call = AsyncMock(
            return_value={"result": {"value": json.dumps({"state": state, "http_status": 200})}}
        )
        result = await inspector.operation({"op": "keepalive"})
        assert result["state"] == state
        assert inspector.call.await_args is not None
        expression = inspector.call.await_args.args[1]["expression"]
        assert "credentials: 'same-origin'" in expression
        assert "response.body.cancel()" in expression
        assert "response.text(" not in expression
        assert "demo.breezechms.com/dashboard" in expression
        assert inspector.pause.await_count == (0 if state == "healthy" else 1)

    asyncio.run(exercise())


def test_keepalive_refuses_unguarded_or_changed_dashboard() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.call = AsyncMock()
        with pytest.raises(InspectionError, match="guarded"):
            await inspector.operation({"op": "keepalive"})
        inspector.capture = True
        inspector.navigation = AsyncMock(return_value={})
        inspector.links = {"Dashboard": "https://demo.breezechms.com/account"}
        with pytest.raises(InspectionError, match="approved Dashboard"):
            await inspector.operation({"op": "keepalive"})
        inspector.call.assert_not_awaited()

    asyncio.run(exercise())


def test_read_schema_hooks_require_capture_and_use_only_the_inspected_tab() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.call = AsyncMock()
        with pytest.raises(InspectionError, match="guarded"):
            await inspector.operation({"op": "watch-reads"})
        inspector.call.assert_not_awaited()
        inspector.capture = True
        inspector.context = "synthetic-tab"
        inspector.origin = "https://demo.breezechms.com"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            side_effect=[
                {"script": "synthetic-preload"},
                {"result": {"value": '{"installed":true}'}},
            ]
        )
        assert (await inspector.watch_reads())["watching"] is True
        assert inspector.watcher == "synthetic-preload"
        call = inspector.call.await_args_list[0]
        assert call.args[0] == "script.addPreloadScript"
        assert "contexts" not in call.args[1]
        assert "installBreezeReadSchemas" in call.args[1]["functionDeclaration"]
        assert "document.cookie" not in call.args[1]["functionDeclaration"]
        assert "localStorage" not in call.args[1]["functionDeclaration"]

    asyncio.run(exercise())


def test_pausing_removes_schema_preload_and_disables_document_hooks() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.watcher = "synthetic-preload"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(return_value={})
        await inspector.pause()
        assert inspector.watcher == ""
        assert inspector.call.await_args_list[0].args[0] == "script.evaluate"
        assert "stop()" in inspector.call.await_args_list[0].args[1]["expression"]
        assert inspector.call.await_args_list[1].args == (
            "script.removePreloadScript",
            {"script": "synthetic-preload"},
        )

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("method", "route", "blocked"),
    [
        ("GET", "/people", False),
        ("POST", "/people", True),
        ("POST", "/ajax/get_forms_list", False),
        ("POST", "/ajax/list_all_people", False),
        ("POST", "/ajax/payments_search_results", False),
        ("POST", "/ajax/payments_search_results?action=refund", True),
        ("POST", "/ajax/update_contribution", True),
        ("POST", "/ajax/refund_charge", True),
        ("POST", "/ajax/list_filtered_people", False),
        ("POST", "/ajax/list_all_people?action=delete", True),
        ("POST", "/ajax/get_forms_list?action=save", True),
        ("POST", "/ajax/get_forms_list/extra", True),
        ("POST", "/ajax/get_form_json_by_url_slug", False),
        ("POST", "/ajax/restore_archived_form", True),
        ("GET", "/deletePerson.php", True),
        ("GET", "/ajax?action=savePerson", True),
        ("GET", "/ajax?task=sendEmail", True),
        ("GET", "/ajax?operation=remove", True),
        ("GET", "/api/v2/oauth/token", True),
        ("GET", "/api/v2/oauth/authorize", True),
        ("GET", "/api/v2/users/impersonate/123", True),
        ("GET", "/account", True),
        ("GET", "/account/account_settings", True),
        ("GET", "/%61ccount/api", True),
        ("GET", "/settings.php", True),
        ("GET", "/api", True),
        ("GET", "/api/v2/api-auth/tokens", True),
        ("GET", "/api/v2/people", False),
    ],
)
def test_write_guard(method: str, route: str, blocked: bool) -> None:
    assert write_shaped(method, "https://demo.breezechms.com" + route) is blocked


@pytest.mark.parametrize(
    "route",
    [
        "/ajax/load_form_entries",
        "/ajax/show_entry",
        "/ajax/people_tag_list",
        "/ajax/search_followups",
        "/ajax/get_profile_fields_json",
        "/ajax/grouped_payment_details",
        "/ajax/payment_details_by_payment_id",
    ],
)
def test_expanded_native_reads_keep_mutation_query_and_subpath_blocked(route: str) -> None:
    origin = "https://demo.breezechms.com"
    assert write_shaped("POST", origin + route) is False
    assert write_shaped("POST", origin + route + "?action=update") is True
    assert write_shaped("POST", origin + route + "/update") is True
    assert write_shaped("PUT", origin + route) is True


@pytest.mark.parametrize(
    ("url", "blocked"),
    [
        ("https://api.breezechms.com/api/v2/auth/refresh", False),
        ("https://api.breezechms.com/api/v2/auth/refresh?action=change", True),
        ("https://demo.breezechms.com/api/v2/auth/refresh", True),
        ("http://api.breezechms.com/api/v2/auth/refresh", True),
        ("https://api.breezechms.com.evil.example/api/v2/auth/refresh", True),
        ("https://api.breezechms.com/api/v2/auth/login", True),
        ("https://api.breezechms.com/api/v2/oauth/token", True),
    ],
)
def test_native_session_refresh_exception_is_exact(url: str, blocked: bool) -> None:
    assert write_shaped("POST", url) is blocked


def test_failed_intercept_install_cannot_leave_capture_marked_ready() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            side_effect=[
                {"result": {"value": 0}},
                {"subscription": "synthetic-subscription"},
                InspectionError("Synthetic failure"),
                {},
            ]
        )
        with pytest.raises(InspectionError):
            await inspector.start()
        assert inspector.capture is False
        assert inspector.intercept == ""
        assert inspector.subscriptions == []
        inspector.call.assert_awaited_with(
            "session.unsubscribe", {"subscriptions": ["synthetic-subscription"]}
        )

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "operation",
    [
        "status",
        "document-state",
        "reload",
        "read-page",
        "pages",
        "controls",
        "capture",
        "assets",
        "page-contracts",
        "watch-reads",
        "read-schemas",
        "list-controls",
        "next-page",
        "probe-people",
        "probe-v2-people",
        "probe-native-people",
        "probe-native-person",
        "probe-native-contributions",
    ],
)
def test_settings_are_rejected_before_dom_or_source_access(operation: str) -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.capture = True
        inspector.watcher = "synthetic-preload"
        inspector.call = AsyncMock(
            return_value={
                "contexts": [
                    {
                        "context": "synthetic-tab",
                        "url": "https://demo.breezechms.com/account/account_settings",
                    }
                ]
            }
        )
        with pytest.raises(InspectionError, match="excluded"):
            await inspector.operation({"op": operation})
        inspector.call.assert_awaited_once_with("browsingContext.getTree", {"maxDepth": 0})

    asyncio.run(exercise())


def test_settings_link_cannot_be_disguised_as_an_approved_page() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.origin = "https://demo.breezechms.com"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            return_value={
                "result": {
                    "value": json.dumps(
                        [
                            {"label": "People", "url": "https://demo.breezechms.com/account"},
                            {"label": "Events", "url": "https://demo.breezechms.com/events"},
                        ]
                    )
                }
            }
        )
        assert await inspector.navigation() == {"pages": [{"label": "Events", "path": "/events"}]}
        assert "People" not in inspector.links
        assert {"Dashboard", "People", "Events", "Tags", "Giving", "Forms"} == browser_inspect.PAGES
        assert {"More"} == browser_inspect.MENUS

    asyncio.run(exercise())


def test_login_and_unguarded_navigation_are_rejected() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(return_value={"result": {"value": 1}})
        with pytest.raises(InspectionError, match="Login"):
            await inspector.start()
        assert inspector.capture is False
        with pytest.raises(InspectionError, match="guarded"):
            await inspector.operation({"op": "navigate", "page": "People"})

    asyncio.run(exercise())


def test_giving_navigation_requires_observed_link_and_uses_fixed_read_report() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.capture = True
        inspector.origin = "https://demo.breezechms.com"
        inspector.context = "synthetic-tab"
        inspector.navigation = AsyncMock(return_value={})
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(return_value={"navigation": "synthetic-navigation"})
        inspector.loaded_navigations.append("synthetic-navigation")
        with pytest.raises(InspectionError, match="approved navigation link"):
            await inspector.operation({"op": "navigate", "page": "Giving"})
        inspector.call.assert_not_awaited()
        inspector.links = {"Giving": inspector.origin + "/payments"}
        await inspector.operation({"op": "navigate", "page": "Giving"})
        inspector.call.assert_awaited_once_with(
            "browsingContext.navigate",
            {
                "context": "synthetic-tab",
                "url": inspector.origin + "/payments/reports",
                "wait": "interactive",
            },
        )

    asyncio.run(exercise())


def test_navigation_waits_for_its_own_load_identifier() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.call = AsyncMock(return_value={"navigation": "new-document"})
        inspector.loaded_navigations.append("old-document")
        task = asyncio.create_task(inspector.navigate_to("https://demo.breezechms.com/people"))
        await asyncio.sleep(0)
        assert not task.done()
        inspector.loaded_navigations.append("new-document")
        inspector.navigation_loaded.set()
        await task
        inspector.call = AsyncMock(return_value={})
        with pytest.raises(InspectionError, match="identifier unavailable"):
            await inspector.navigate_to("https://demo.breezechms.com/people")

    asyncio.run(exercise())


@pytest.mark.parametrize(
    ("error", "message"),
    [("no such request", "connection ended"), ("invalid argument", "guard failed")],
)
def test_cancelled_intercept_never_replays_and_other_guard_errors_stop(
    error: str, message: str
) -> None:
    async def exercise() -> None:
        websocket = AsyncMock()
        websocket.__aiter__.return_value = [json.dumps({"id": 1, "type": "error", "error": error})]
        inspector = Inspector(websocket)
        inspector.guards.add(1)
        with pytest.raises(InspectionError, match=message):
            await inspector.receive()
        assert not inspector.guards
        websocket.send.assert_not_awaited()

    asyncio.run(exercise())


def test_capture_checks_visible_login_and_guards_both_api_origins() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.origin = "https://demo.breezechms.com"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            side_effect=[
                {"result": {"value": 0}},
                {"subscription": "synthetic-subscription"},
                {"intercept": "synthetic-intercept"},
            ]
        )
        assert (await inspector.start())["write_guard"] is True
        calls = inspector.call.await_args_list
        expression = calls[0].args[1]["expression"]
        assert "getClientRects().length>0" in expression
        assert "visibility!=='hidden'" in expression
        patterns = calls[2].args[1]["urlPatterns"]
        assert {pattern["hostname"] for pattern in patterns} == {
            "demo.breezechms.com",
            "api.breezechms.com",
        }

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "selection",
    [
        {"op": "source", "asset": True},
        {"op": "source", "asset": 0, "dependency": "private-value"},
        {"op": "source", "asset": -1},
    ],
)
def test_source_selection_refuses_arbitrary_input(selection: dict[str, object]) -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock()
        with pytest.raises(InspectionError, match="Select"):
            await inspector.source(selection)
        inspector.call.assert_not_awaited()

    asyncio.run(exercise())


def test_public_assets_can_be_inspected_without_login_capture() -> None:
    async def exercise() -> None:
        inspector = Inspector(AsyncMock())
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(return_value={"result": {"value": '{"assets":[],"count":0}'}})
        assert await inspector.operation({"op": "assets"}) == {"assets": [], "count": 0}
        assert inspector.capture is False
        assert inspector.call.await_args is not None
        expression = inspector.call.await_args.args[1]["expression"]
        assert "credentials: 'omit'" in expression
        assert "awaitPromise" in inspector.call.await_args.args[1]

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "path", sorted(browser_inspect.READ_VIEW_PATHS) + ["/people/edit/123", "/events/edit/123"]
)
def test_reviewed_view_get_exceptions_never_allow_writes_or_action_queries(path: str) -> None:
    url = "https://demo.breezechms.com" + path
    assert not write_shaped("GET", url)
    assert browser_inspect.link_exclusion(url, "https://demo.breezechms.com") is None
    assert write_shaped("POST", url)
    assert write_shaped("GET", url + "?action=delete")
    assert (
        browser_inspect.link_exclusion(url + "?action=delete", "https://demo.breezechms.com")
        == "action_review_required"
    )


def test_global_navigation_does_not_select_person_giving_tab() -> None:
    async def run() -> None:
        inspector = Inspector(1)
        inspector.origin = "https://demo.breezechms.com"
        inspector.page = AsyncMock(return_value={})
        inspector.call = AsyncMock(
            return_value={
                "result": {
                    "value": json.dumps(
                        [
                            {"label": "Giving", "url": inspector.origin + "/payments"},
                            {
                                "label": "Giving",
                                "url": inspector.origin + "/people/view/123/payments",
                            },
                        ]
                    )
                }
            }
        )
        assert await inspector.navigation() == {"pages": [{"label": "Giving", "path": "/payments"}]}
        assert inspector.links["Giving"] == inspector.origin + "/payments"

    asyncio.run(run())
