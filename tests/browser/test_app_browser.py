"""Browser checks use invented classes and do not access myUNT or personal data."""

import json
import os
import sys

import pytest

pytestmark = pytest.mark.browser
STORAGE_KEY = "eagle-eye.schedule"


def fill_meeting(page, code="TEST 1000", title="Sample course", days=("mon", "wed"),
                 start="09:00", end="09:50", building="0155", room="101"):
    page.locator("#course-code").fill(code)
    page.locator("#course-title").fill(title)
    for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
        page.locator(f'input[name="days"][value="{day}"]').set_checked(day in days)
    page.locator("#meeting-start").fill(start)
    page.locator("#meeting-end").fill(end)
    page.locator("#meeting-building").select_option(building)
    page.locator("#meeting-room").fill(room)


def add_meeting(page, **values):
    fill_meeting(page, **values)
    page.locator("#schedule-add").click()


def saved_schedule(page):
    raw = page.evaluate("key => localStorage.getItem(key)", STORAGE_KEY)
    return json.loads(raw) if raw is not None else None


def test_app_loads_without_javascript_errors(page, live_app, artifact_dir):
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(live_app, wait_until="networkidle")
    page.locator("#meeting-building:not([disabled])").wait_for()
    assert page.locator("#map .leaflet-interactive").count() > 100
    assert page.locator("#meeting-building option").count() == 165
    assert page.locator("#schedule-empty").is_visible()
    assert not errors
    page.screenshot(path=str(artifact_dir / "desktop-initial.png"), full_page=True)


def test_building_search_and_selection(app_page):
    app_page.locator("#search-input").fill("0155")
    app_page.locator('#search-form button').click()
    app_page.locator("#results button").click()
    assert app_page.locator("#details h2").inner_text() == "Student Union"
    assert app_page.locator("#map .leaflet-tooltip").inner_text() == "Student Union"


def test_add_save_and_restore(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    assert original["courses"][0]["meetings"][0]["buildingCode"] == "0155"
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#meeting-building:not([disabled])").wait_for()
    assert "TEST 1000" in app_page.locator("#schedule-list").inner_text()
    assert "Student Union, room 101" in app_page.locator("#schedule-list").inner_text()
    assert saved_schedule(app_page) == original


def test_schedule_map_selection(app_page):
    add_meeting(app_page)
    app_page.get_by_role("button", name="Show Student Union on the map for TEST 1000").click()
    app_page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()
    assert app_page.locator("#details h2").inner_text() == "Student Union"
    assert app_page.locator("#map .leaflet-tooltip").inner_text() == "Student Union"


def test_search_no_results(app_page):
    app_page.locator("#search-input").fill("no-such-building-9876")
    app_page.locator("#search-form button").click()
    app_page.get_by_text("No buildings match that search.", exact=True).wait_for()


def test_multiple_meetings_share_one_course(app_page):
    add_meeting(app_page)
    course_id = saved_schedule(app_page)["courses"][0]["id"]
    add_meeting(app_page, days=("fri",), start="13:00", end="14:00", building="0108", room="202")
    courses = saved_schedule(app_page)["courses"]
    assert len(courses) == 1
    assert courses[0]["id"] == course_id
    assert len(courses[0]["meetings"]) == 2
    assert app_page.locator("#schedule-list > li").count() == 1


def test_duplicate_meeting_rejected(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    add_meeting(app_page, code=" test 1000 ")
    assert app_page.locator("#schedule-feedback").inner_text() == "That meeting is already on your schedule."
    assert saved_schedule(app_page) == original


@pytest.mark.parametrize("values,message", [
    ({"days": ()}, "Choose at least one meeting day."),
    ({"end": "09:00"}, "The end time must be later than the start time."),
    ({"end": "08:00"}, "The end time must be later than the start time."),
    ({"code": "   "}, "Enter a course code."),
])
def test_invalid_meeting_is_not_saved(app_page, values, message):
    add_meeting(app_page, **values)
    assert app_page.locator("#schedule-feedback").inner_text() == message
    assert saved_schedule(app_page) is None
    assert app_page.locator("#schedule-empty").is_visible()


def test_browser_requires_empty_fields(app_page):
    app_page.locator("#schedule-add").click()
    assert not app_page.locator("#schedule-form").evaluate("form => form.checkValidity()")
    assert saved_schedule(app_page) is None


def test_edit_preserves_id_and_other_meetings(app_page):
    add_meeting(app_page)
    add_meeting(app_page, days=("fri",), start="13:00", end="14:00")
    original = saved_schedule(app_page)["courses"][0]
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).first.click()
    app_page.locator("#course-title").fill("Updated title")
    app_page.locator("#meeting-room").fill("999")
    app_page.locator("#schedule-add").click()
    updated = saved_schedule(app_page)["courses"][0]
    assert updated["id"] == original["id"]
    assert updated["title"] == "Updated title"
    assert updated["meetings"][0]["room"] == "999"
    assert updated["meetings"][1] == original["meetings"][1]
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_text("TEST 1000 - Updated title", exact=True).wait_for()


def test_cancel_edit_leaves_schedule_unchanged(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).click()
    app_page.locator("#meeting-room").fill("999")
    app_page.locator("#schedule-cancel").click()
    assert saved_schedule(app_page) == original
    assert app_page.locator("#schedule-add").inner_text() == "Add class meeting"
    assert not app_page.locator("#schedule-cancel").is_visible()


def test_edit_rejects_duplicate_meeting(app_page):
    add_meeting(app_page)
    add_meeting(app_page, days=("fri",), start="13:00", end="14:00")
    original = saved_schedule(app_page)
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).nth(1).click()
    fill_meeting(app_page)
    app_page.locator("#schedule-add").click()
    assert app_page.locator("#schedule-feedback").inner_text() == "That meeting is already on your schedule."
    assert saved_schedule(app_page) == original


def test_rename_conflict_does_not_merge_courses(app_page):
    add_meeting(app_page)
    add_meeting(app_page, code="TEST 2000")
    original = saved_schedule(app_page)
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).click()
    app_page.locator("#course-code").fill("TEST 2000")
    app_page.locator("#schedule-add").click()
    assert "Another course already uses TEST 2000" in app_page.locator("#schedule-feedback").inner_text()
    assert saved_schedule(app_page) == original


def test_delete_cancel_and_last_meeting(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    app_page.once("dialog", lambda dialog: dialog.dismiss())
    app_page.get_by_role("button", name="Delete TEST 1000", exact=False).click()
    assert saved_schedule(app_page) == original
    app_page.once("dialog", lambda dialog: dialog.accept())
    app_page.get_by_role("button", name="Delete TEST 1000", exact=False).click()
    assert saved_schedule(app_page)["courses"] == []
    assert app_page.locator("#schedule-empty").is_visible()
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#meeting-building:not([disabled])").wait_for()
    assert app_page.locator("#schedule-list > li").count() == 0


def test_delete_one_meeting_keeps_other(app_page):
    add_meeting(app_page)
    add_meeting(app_page, days=("fri",), start="13:00", end="14:00")
    original = saved_schedule(app_page)["courses"][0]
    app_page.once("dialog", lambda dialog: dialog.accept())
    app_page.get_by_role("button", name="Delete TEST 1000", exact=False).first.click()
    updated = saved_schedule(app_page)["courses"][0]
    assert updated["id"] == original["id"]
    assert updated["meetings"] == [original["meetings"][1]]


def test_missing_coordinates_disable_map_button(app_page):
    add_meeting(app_page, building="0166")
    button = app_page.get_by_role("button", name="Show Science and Technology on the map", exact=False)
    assert button.is_disabled()
    app_page.get_by_text("A map location is not available for this building.", exact=True).wait_for()


@pytest.mark.parametrize("stored", ["not json", '{"version": 999, "courses": []}',
                                     '{"version": 1, "courses": [null]}'])
def test_unreadable_storage_is_kept(app_page, stored):
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)", [STORAGE_KEY, stored])
    app_page.reload(wait_until="domcontentloaded")
    app_page.locator("#meeting-building:not([disabled])").wait_for()
    assert "Saving is paused" in app_page.locator("#schedule-storage-status").inner_text()
    add_meeting(app_page)
    assert app_page.evaluate("key => localStorage.getItem(key)", STORAGE_KEY) == stored


def test_failed_write_keeps_previous_saved_value(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    app_page.evaluate("""() => {
        Storage.prototype.setItem = () => { throw new DOMException('Full', 'QuotaExceededError'); };
    }""")
    add_meeting(app_page, code="TEST 2000")
    assert "could not be saved" in app_page.locator("#schedule-storage-status").inner_text()
    assert saved_schedule(app_page) == original
    assert app_page.locator("#schedule-list > li").count() == 2


def test_blocked_storage_keeps_form_usable(page, live_app):
    page.add_init_script("""Storage.prototype.getItem = () => {
        throw new DOMException('Blocked', 'SecurityError');
    };""")
    page.goto(live_app, wait_until="domcontentloaded")
    page.locator("#meeting-building:not([disabled])").wait_for()
    add_meeting(page)
    assert page.locator("#schedule-list > li").count() == 1
    assert "Saving is paused" in page.locator("#schedule-storage-status").inner_text()


def test_api_failure_keeps_restored_classes_visible(app_page):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    app_page.route("**/api/buildings", lambda route: route.fulfill(status=503, body="Unavailable"))
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_text("Could not load buildings. Refresh the page to try again.", exact=True).wait_for()
    assert "TEST 1000" in app_page.locator("#schedule-list").inner_text()
    assert app_page.locator("#schedule-add").is_disabled()
    assert saved_schedule(app_page) == original


def test_map_library_failure_keeps_schedule_usable(page, live_app):
    page.route("https://unpkg.com/**/leaflet.js", lambda route: route.abort())
    page.goto(live_app, wait_until="domcontentloaded")
    page.locator("#meeting-building:not([disabled])").wait_for()
    add_meeting(page)
    page.get_by_role("button", name="Show Student Union on the map for TEST 1000").click()
    page.get_by_text("The map is not available yet. Wait for it to load, or refresh to try again.", exact=True).wait_for()
    assert saved_schedule(page)["courses"][0]["courseCode"] == "TEST 1000"


def test_user_text_is_rendered_as_text(app_page):
    title = '<img src=x onerror="window.injected=true">'
    add_meeting(app_page, title=title)
    assert title in app_page.locator("#schedule-list").inner_text()
    assert app_page.locator("#schedule-list img").count() == 0
    assert not app_page.evaluate("Boolean(window.injected)")


def test_schedule_data_is_not_submitted(app_page, live_app):
    requests = []
    app_page.on("request", lambda request: requests.append((request.method, request.url)))
    add_meeting(app_page)
    assert not any(method != "GET" for method, url in requests if url.startswith(live_app))
    assert not any("TEST" in url for method, url in requests)


def test_saved_schedule_survives_reopening_page(app_page, context, live_app):
    add_meeting(app_page)
    original = saved_schedule(app_page)
    app_page.close()
    reopened = context.new_page()
    reopened.goto(live_app, wait_until="domcontentloaded")
    reopened.get_by_text("TEST 1000 - Sample course", exact=True).wait_for()
    assert saved_schedule(reopened) == original


def test_new_browser_profile_has_separate_schedule(app_page, browser, live_app):
    add_meeting(app_page)
    with browser.new_context() as separate:
        other = separate.new_page()
        other.goto(live_app, wait_until="domcontentloaded")
        other.locator("#meeting-building:not([disabled])").wait_for()
        assert other.locator("#schedule-empty").is_visible()
        assert saved_schedule(other) is None


def test_two_tabs_do_not_overwrite_each_other(app_page, context, live_app):
    other = context.new_page()
    other.goto(live_app, wait_until="domcontentloaded")
    other.locator("#meeting-building:not([disabled])").wait_for()
    add_meeting(app_page)
    add_meeting(other, code="TEST 2000")
    assert {course["courseCode"] for course in saved_schedule(other)["courses"]} == {
        "TEST 1000", "TEST 2000"
    }


def test_edit_merges_unrelated_changes_from_another_tab(app_page, context, live_app):
    add_meeting(app_page)
    other = context.new_page()
    other.goto(live_app, wait_until="domcontentloaded")
    other.locator("#meeting-building:not([disabled])").wait_for()
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).click()
    app_page.locator("#meeting-room").fill("999")
    add_meeting(other, code="TEST 2000")
    app_page.locator("#schedule-add").click()
    courses = saved_schedule(app_page)["courses"]
    assert {course["courseCode"] for course in courses} == {"TEST 1000", "TEST 2000"}
    assert courses[0]["meetings"][0]["room"] == "999"


def test_stale_edit_does_not_overwrite_another_tab(app_page, context, live_app):
    add_meeting(app_page)
    other = context.new_page()
    other.goto(live_app, wait_until="domcontentloaded")
    other.locator("#meeting-building:not([disabled])").wait_for()
    app_page.get_by_role("button", name="Edit TEST 1000", exact=False).click()
    app_page.locator("#meeting-room").fill("999")
    other.get_by_role("button", name="Edit TEST 1000", exact=False).click()
    other.locator("#meeting-room").fill("222")
    other.locator("#schedule-add").click()
    app_page.locator("#schedule-add").click()
    assert "changed in another tab" in app_page.locator("#schedule-feedback").inner_text()
    assert saved_schedule(app_page)["courses"][0]["meetings"][0]["room"] == "222"
    assert app_page.locator("#meeting-room").input_value() == "999"
    app_page.locator("#schedule-cancel").click()
    assert "room 222" in app_page.locator("#schedule-list").inner_text()


def test_map_request_waits_for_building_markers(page, live_app):
    pending = []
    requests = []

    def handle(route):
        requests.append(route)
        # Saved Places loads first as a map dependency; the map loads second.
        if len(requests) == 2:
            pending.append(route)
        else:
            route.continue_()

    page.route("**/api/buildings", handle)
    page.goto(live_app, wait_until="domcontentloaded")
    page.locator("#meeting-building:not([disabled])").wait_for()
    add_meeting(page)
    page.get_by_role("button", name="Show Student Union on the map for TEST 1000").click()
    page.get_by_text("Opening building on the map...", exact=True).wait_for()
    pending[0].continue_()
    page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()


def test_stale_building_code_has_clear_message(app_page):
    add_meeting(app_page)
    saved = saved_schedule(app_page)
    saved["courses"][0]["meetings"][0]["buildingCode"] = "9999"
    app_page.evaluate("([key, value]) => localStorage.setItem(key, value)",
                      [STORAGE_KEY, json.dumps(saved)])
    app_page.reload(wait_until="domcontentloaded")
    app_page.get_by_text("This building is no longer in the campus building list.", exact=True).wait_for()
    assert app_page.get_by_role("button", name="Show Building 9999", exact=False).is_disabled()


def test_external_basemap_tiles_load(app_page):
    app_page.wait_for_function("""() => [...document.querySelectorAll('#map img.leaflet-tile')]
        .some(image => image.complete && image.naturalWidth > 0)""", timeout=20000)


def test_schedule_survives_browser_restart(browser, live_app, tmp_path):
    channel = os.environ.get(
        "EAGLE_EYE_BROWSER_CHANNEL", "msedge" if sys.platform == "win32" else "chromium"
    )
    options = {} if channel == "chromium" else {"channel": channel}
    profile = tmp_path / "test-browser-profile"
    with browser.browser_type.launch_persistent_context(str(profile), headless=True, **options) as first:
        page = first.pages[0]
        page.goto(live_app, wait_until="domcontentloaded")
        page.locator("#meeting-building:not([disabled])").wait_for()
        add_meeting(page)
        original = saved_schedule(page)
    with browser.browser_type.launch_persistent_context(str(profile), headless=True, **options) as second:
        page = second.pages[0]
        page.goto(live_app, wait_until="domcontentloaded")
        page.get_by_text("TEST 1000 - Sample course", exact=True).wait_for()
        assert saved_schedule(page) == original


def test_touch_layout(browser, live_app, artifact_dir):
    with browser.new_context(viewport={"width": 390, "height": 844},
                             is_mobile=True, has_touch=True) as mobile:
        page = mobile.new_page()
        page.goto(live_app, wait_until="domcontentloaded")
        page.locator("#meeting-building:not([disabled])").wait_for()
        add_meeting(page)
        page.get_by_role("button", name="Show Student Union on the map for TEST 1000").tap()
        page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()
        page.wait_for_function("""() => [...document.querySelectorAll('#map img.leaflet-tile')]
            .some(image => image.complete && image.naturalWidth > 0)""", timeout=20000)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(artifact_dir / "mobile-touch-map.png"), full_page=True)


@pytest.mark.parametrize("width", [360, 390, 768, 1280])
def test_responsive_layout_and_map(app_page, width, artifact_dir):
    app_page.set_viewport_size({"width": width, "height": 844})
    add_meeting(app_page)
    assert app_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    app_page.screenshot(path=str(artifact_dir / f"schedule-{width}.png"), full_page=True)
    app_page.get_by_role("button", name="Show Student Union on the map for TEST 1000").click()
    app_page.get_by_text("Showing Student Union on the map.", exact=True).wait_for()
    assert app_page.locator("#map").evaluate("el => el.getBoundingClientRect().top") < 844
