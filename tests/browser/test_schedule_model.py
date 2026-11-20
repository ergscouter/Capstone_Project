"""Exercise the shared JavaScript model in a real browser without the map UI."""

from copy import deepcopy

import pytest

pytestmark = pytest.mark.browser
COURSE = {
    "courseCode": "TEST 1000", "title": "Sample course",
    "meetings": [{"days": ["mon", "wed"], "startTime": "09:00", "endTime": "09:50",
                  "buildingCode": "0155", "room": "101"}],
}


@pytest.fixture
def model_page(page, live_app):
    page.goto(f"{live_app}/api/health")
    return page


def test_create_and_restore_preserve_course(model_page):
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        const course = model.createCourse(input);
        return {course, restored: model.restoreCourse(course)};
    }""", COURSE)
    assert result["course"] == result["restored"]
    assert result["course"]["meetings"][0]["buildingCode"] == "0155"


def test_days_are_deduplicated_and_ordered(model_page):
    source = deepcopy(COURSE)
    source["meetings"][0]["days"] = ["fri", "mon", "mon"]
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js'); return model.createCourse(input);
    }""", source)
    assert result["meetings"][0]["days"] == ["mon", "fri"]


@pytest.mark.parametrize("field,value", [
    ("days", []), ("days", ["not-a-day"]), ("days", "mon"),
    ("startTime", "25:00"), ("startTime", ["09:00"]),
    ("endTime", "09:00"), ("endTime", "08:00"),
    ("buildingCode", 155), ("buildingCode", ""), ("room", {}),
])
def test_model_rejects_invalid_meeting(model_page, field, value):
    source = deepcopy(COURSE)
    source["meetings"][0][field] = value
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        try { model.createCourse(input); return false; } catch { return true; }
    }""", source)
    assert result


@pytest.mark.parametrize("code", [" test   1000 ", "X" * 30, "ß" * 15])
def test_created_course_can_always_be_restored(model_page, code):
    source = deepcopy(COURSE)
    source["courseCode"] = code
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        try {
            const course = model.createCourse(input);
            return {valid: true, same: JSON.stringify(course) === JSON.stringify(model.restoreCourse(course))};
        } catch (error) { return {valid: false, message: error.message}; }
    }""", source)
    assert result["valid"] and result["same"], result


def test_expanded_course_code_is_rejected_before_saving(model_page):
    source = deepcopy(COURSE)
    source["courseCode"] = "ß" * 30
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        try { model.createCourse(input); return ''; } catch (error) { return error.message; }
    }""", source)
    assert "30 characters" in result


@pytest.mark.parametrize("index", [-1, 1.5, 99, None])
def test_invalid_meeting_position_does_not_change_source(model_page, index):
    result = model_page.evaluate("""async ({input, index}) => {
        const model = await import('/schedule-model.js');
        const source = [model.createCourse(input)];
        const before = JSON.stringify(source);
        const errors = [];
        for (const operation of [
            () => model.updateCourseMeeting(source, source[0].id, index, input),
            () => model.removeCourseMeeting(source, source[0].id, index),
        ]) { try { operation(); errors.push(false); } catch { errors.push(true); } }
        return {errors, unchanged: JSON.stringify(source) === before};
    }""", {"input": COURSE, "index": index})
    assert result == {"errors": [True, True], "unchanged": True}


def test_updates_are_immutable_and_keep_course_id(model_page):
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        const original = [model.createCourse(input)];
        const before = JSON.stringify(original);
        const changed = structuredClone(input); changed.meetings[0].room = '999';
        const updated = model.updateCourseMeeting(original, original[0].id, 0, changed);
        return {unchanged: JSON.stringify(original) === before,
            sameId: updated[0].id === original[0].id, room: updated[0].meetings[0].room};
    }""", COURSE)
    assert result == {"unchanged": True, "sameId": True, "room": "999"}


def test_storage_round_trip_and_validation(model_page):
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        const storage = await import('/schedule-storage.js');
        const course = model.createCourse(input);
        storage.saveSchedule([course]);
        const restored = storage.loadSchedule();
        let duplicateRejected = false;
        try { storage.saveSchedule([course, course]); } catch { duplicateRejected = true; }
        return {same: JSON.stringify(restored) === JSON.stringify([course]), duplicateRejected,
            preserved: JSON.stringify(storage.loadSchedule()) === JSON.stringify([course])};
    }""", COURSE)
    assert result == {"same": True, "duplicateRejected": True, "preserved": True}


def test_storage_refuses_to_overwrite_a_newer_snapshot(model_page):
    result = model_page.evaluate("""async input => {
        const model = await import('/schedule-model.js');
        const storage = await import('/schedule-storage.js');
        const first = model.createCourse(input);
        const oldSnapshot = storage.saveSchedule([first]);
        const second = model.createCourse({...input, courseCode: 'TEST 2000'});
        const newerSnapshot = storage.saveSchedule([first, second]);
        let conflict = false;
        try { storage.saveSchedule([], oldSnapshot); }
        catch (error) { conflict = error instanceof storage.ScheduleConflictError; }
        return {conflict, preserved: storage.loadScheduleState().snapshot === newerSnapshot};
    }""", COURSE)
    assert result == {"conflict": True, "preserved": True}


def test_map_connector_reports_missing_map(model_page):
    result = model_page.evaluate("""async () => {
        const navigation = await import('/map-navigation.js');
        try { await navigation.showBuildingOnMap('0155'); return ''; }
        catch (error) { return error.message; }
    }""")
    assert "map is not available" in result


def test_map_connector_passes_only_building_code(model_page):
    result = model_page.evaluate("""async () => {
        const navigation = await import('/map-navigation.js');
        let received;
        navigation.registerBuildingNavigator(async code => { received = code; return 'Student Union'; });
        const name = await navigation.showBuildingOnMap('0155');
        return {received, name};
    }""")
    assert result == {"received": "0155", "name": "Student Union"}
