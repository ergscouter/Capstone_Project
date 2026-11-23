"""Building bookmarks use public campus data and isolated browser storage."""

import json
import os
import sys

import pytest

pytestmark = pytest.mark.browser
STORAGE_KEY = "eagle-eye.saved-places"


def select_building(page, code="0155"):
    page.locator("#search-input").fill(code)
    page.locator("#search-form button").click()
    page.locator("#results button").first.click()
    page.locator("#details .save-place-button").wait_for()


def save_building(page, code="0155"):
    select_building(page, code)
    page.locator("#details .save-place-button").click()


def saved_places(page):
    raw = page.evaluate("key => localStorage.getItem(key)", STORAGE_KEY)
    return json.loads(raw) if raw is not None else None


def test_save_building_and_restore_after_refresh(app_page):
    save_building(app_page)
    saved = saved_places(app_page)
    assert saved == {"version": 1, "places": [{"buildingCode": "0155", "name": "Student Union"}]}
    assert app_page.locator("#saved-places-list > li").count() == 1
    assert app_page.locator("#details .save-place-button").inner_text() == "Remove saved place"
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_role("button", name="Show Student Union on the map from Saved Places").wait_for()
    assert saved_places(app_page) == saved


def test_remove_bookmark_updates_selected_building(app_page):
    save_building(app_page)
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").click()
    assert saved_places(app_page)["places"] == []
    assert app_page.locator("#details .save-place-button").inner_text() == "Save place"
    assert app_page.locator("#saved-places-empty").is_visible()
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#meeting-building:not([disabled])").wait_for()
    assert app_page.locator("#saved-places-list > li").count() == 0


def test_details_button_can_remove_and_save_again(app_page):
    save_building(app_page)
    app_page.locator("#details .save-place-button").click()
    assert saved_places(app_page)["places"] == []
    app_page.locator("#details .save-place-button").click()
    assert len(saved_places(app_page)["places"]) == 1


def test_saved_list_is_alphabetical_and_unique(app_page):
    save_building(app_page, "0155")
    save_building(app_page, "0108")
    select_building(app_page, "0155")
    assert len(saved_places(app_page)["places"]) == 2
    assert app_page.locator("#saved-places-list .saved-place-link").all_text_contents() == [
        "General Academic Bldg", "Student Union"
    ]


def test_saved_building_opens_map(app_page):
    save_building(app_page)
    button = app_page.get_by_role("button", name="Show Student Union on the map from Saved Places")
    button.click()
    app_page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()
    assert app_page.locator("#details h2").inner_text() == "Student Union"
    assert app_page.locator("#map .leaflet-tooltip").inner_text() == "Student Union"
    assert app_page.locator("#details .save-place-button").inner_text() == "Remove saved place"


def test_building_without_coordinates_can_be_saved_and_removed(app_page):
    save_building(app_page, "0166")
    assert saved_places(app_page)["places"][0]["buildingCode"] == "0166"
    app_page.get_by_text("A map location is not available for this building.", exact=True).wait_for()
    assert app_page.get_by_role("button", name="Show Science and Technology on the map from Saved Places").is_disabled()
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove", exact=False).click()
    assert saved_places(app_page)["places"] == []


def test_removed_building_remains_visible_and_removable(app_page):
    value = {"version": 1, "places": [{"buildingCode": "9999", "name": "Former Building"}]}
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)", [STORAGE_KEY, json.dumps(value)])
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_text("This building is no longer in the campus building list.", exact=True).wait_for()
    assert app_page.get_by_role("button", name="Show Former Building on the map from Saved Places").is_disabled()
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove Former Building from Saved Places").click()
    assert saved_places(app_page)["places"] == []


@pytest.mark.parametrize("raw", ["not-json", '{"version": 2, "places": []}',
                                '{"version": 1, "places": [null]}'])
def test_unreadable_bookmarks_are_not_overwritten(app_page, raw):
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)", [STORAGE_KEY, raw])
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#meeting-building:not([disabled])").wait_for()
    assert "could not be opened" in app_page.locator("#saved-places-storage-status").inner_text()
    save_building(app_page)
    assert "could not be saved" in app_page.locator("#saved-places-feedback").inner_text()
    assert app_page.evaluate("key => localStorage.getItem(key)", STORAGE_KEY) == raw


def test_failed_write_does_not_claim_bookmark_was_added(app_page):
    select_building(app_page)
    app_page.evaluate("""() => {
        Storage.prototype.setItem = () => { throw new DOMException('Full', 'QuotaExceededError'); };
    }""")
    app_page.locator("#details .save-place-button").click()
    assert "could not be saved" in app_page.locator("#saved-places-feedback").inner_text()
    assert saved_places(app_page) is None
    assert app_page.locator("#saved-places-list > li").count() == 0
    assert app_page.locator("#details .save-place-button").inner_text() == "Save place"


def test_failed_removal_keeps_existing_bookmark(app_page):
    save_building(app_page)
    original = saved_places(app_page)
    app_page.evaluate("""() => {
        Storage.prototype.setItem = () => { throw new DOMException('Full', 'QuotaExceededError'); };
    }""")
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").click()
    assert saved_places(app_page) == original
    assert app_page.locator("#saved-places-list > li").count() == 1


def test_bookmarks_and_schedules_use_separate_storage(app_page):
    schedule = app_page.evaluate("() => localStorage.getItem('eagle-eye.schedule')")
    save_building(app_page)
    assert app_page.evaluate("() => localStorage.getItem('eagle-eye.schedule')") == schedule


def test_two_tabs_keep_each_others_bookmarks(app_page, context, live_app):
    other = context.new_page()
    other.goto(live_app, wait_until="domcontentloaded")
    other.locator("#meeting-building:not([disabled])").wait_for()
    save_building(app_page, "0155")
    save_building(other, "0108")
    assert {place["buildingCode"] for place in saved_places(other)["places"]} == {"0155", "0108"}
    app_page.locator("#saved-places-list").get_by_role("button", name="Show General Academic Bldg", exact=False).wait_for()
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").click()
    other.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").wait_for(state="detached")
    assert saved_places(other)["places"][0]["buildingCode"] == "0108"


def test_metadata_failure_keeps_bookmarks_available_for_removal(app_page):
    save_building(app_page)
    app_page.route("**/api/buildings", lambda route: route.fulfill(status=503, body="Unavailable"))
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_text("Building locations are unavailable. Refresh to try again.", exact=True).wait_for()
    assert app_page.get_by_role("button", name="Show Student Union on the map from Saved Places").is_disabled()
    app_page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").click()
    assert saved_places(app_page)["places"] == []


def test_current_building_name_is_used(app_page):
    value = {"version": 1, "places": [{"buildingCode": "0155", "name": "Old Union Name"}]}
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)", [STORAGE_KEY, json.dumps(value)])
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_role("button", name="Show Student Union on the map from Saved Places").wait_for()
    assert app_page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").is_visible()


@pytest.mark.parametrize("width", [360, 390, 768, 1280])
def test_saved_places_fit_screen(app_page, width, artifact_dir):
    app_page.set_viewport_size({"width": width, "height": 844})
    save_building(app_page)
    assert app_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    app_page.screenshot(path=str(artifact_dir / f"saved-places-{width}.png"), full_page=True)


@pytest.fixture
def model_page(page, live_app):
    page.goto(f"{live_app}/api/health")
    return page


def test_model_keeps_building_codes_and_rejects_duplicates(model_page):
    result = model_page.evaluate("""async () => {
        const model = await import('/saved-places-model.js');
        const place = {buildingCode: '0155', name: 'Student Union'};
        const original = model.addSavedPlace([], place);
        const duplicate = model.addSavedPlace(original, {...place, name: 'Other name'});
        return {code: original[0].buildingCode, count: duplicate.length,
            removed: model.removeSavedPlace(original, '0155'), originalCount: original.length};
    }""")
    assert result == {"code": "0155", "count": 1, "removed": [], "originalCount": 1}


@pytest.mark.parametrize("place", [None, {}, {"buildingCode": 155, "name": "Union"},
                                  {"buildingCode": "0155", "name": ""},
                                  {"buildingCode": "X" * 21, "name": "Union"}])
def test_model_rejects_invalid_records(model_page, place):
    assert model_page.evaluate("""async input => {
        const model = await import('/saved-places-model.js');
        try { model.createSavedPlace(input); return false; } catch { return true; }
    }""", place)


def test_storage_checks_saved_version_and_conflicts(model_page):
    result = model_page.evaluate("""async () => {
        const storage = await import('/saved-places-storage.js');
        const first = storage.loadSavedPlaces();
        const place = {buildingCode: '0155', name: 'Student Union'};
        storage.saveSavedPlaces([place], first.snapshot);
        const current = storage.loadSavedPlaces();
        let conflict = false;
        try { storage.saveSavedPlaces([], first.snapshot); } catch { conflict = true; }
        let duplicate = false;
        try { storage.saveSavedPlaces([place, place], current.snapshot); } catch { duplicate = true; }
        return {conflict, duplicate, code: storage.loadSavedPlaces().places[0].buildingCode};
    }""")
    assert result == {"conflict": True, "duplicate": True, "code": "0155"}


def test_saved_name_is_rendered_as_text(app_page):
    value = {"version": 1, "places": [{"buildingCode": "9999", "name": '<img src=x onerror="window.injected=true">'}]}
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)", [STORAGE_KEY, json.dumps(value)])
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#saved-places-list > li").wait_for()
    assert app_page.locator("#saved-places-list img").count() == 0
    assert not app_page.evaluate("Boolean(window.injected)")


def test_blocked_storage_does_not_create_a_false_bookmark(page, live_app):
    page.add_init_script("""Storage.prototype.getItem = () => {
        throw new DOMException('Blocked', 'SecurityError');
    };""")
    page.goto(live_app, wait_until="domcontentloaded")
    page.locator("#meeting-building:not([disabled])").wait_for()
    save_building(page)
    assert "could not be saved" in page.locator("#saved-places-feedback").inner_text()
    assert page.locator("#saved-places-list > li").count() == 0


def test_bookmarks_survive_browser_restart(browser, live_app, tmp_path):
    channel = os.environ.get(
        "EAGLE_EYE_BROWSER_CHANNEL", "msedge" if sys.platform == "win32" else "chromium"
    )
    options = {} if channel == "chromium" else {"channel": channel}
    profile = tmp_path / "bookmark-browser-profile"
    with browser.browser_type.launch_persistent_context(str(profile), headless=True, **options) as first:
        page = first.pages[0]
        page.goto(live_app, wait_until="domcontentloaded")
        page.locator("#meeting-building:not([disabled])").wait_for()
        save_building(page)
        original = saved_places(page)
    with browser.browser_type.launch_persistent_context(str(profile), headless=True, **options) as second:
        page = second.pages[0]
        page.goto(live_app, wait_until="domcontentloaded")
        page.get_by_role("button", name="Show Student Union on the map from Saved Places").wait_for()
        assert saved_places(page) == original


def test_bookmarks_work_with_touch_input(browser, live_app, artifact_dir):
    with browser.new_context(viewport={"width": 390, "height": 844},
                             is_mobile=True, has_touch=True) as mobile:
        page = mobile.new_page()
        page.goto(live_app, wait_until="domcontentloaded")
        page.locator("#meeting-building:not([disabled])").wait_for()
        select_building(page)
        page.locator("#details .save-place-button").tap()
        page.get_by_role("button", name="Show Student Union on the map from Saved Places").tap()
        page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()
        page.screenshot(path=str(artifact_dir / "saved-places-touch.png"), full_page=True)
        page.locator("#saved-places-list").get_by_role("button", name="Remove Student Union from Saved Places").tap()
        assert saved_places(page)["places"] == []
