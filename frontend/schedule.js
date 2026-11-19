import {
  createCourse, MEETING_DAYS, removeCourseMeeting, sameMeeting, updateCourseMeeting,
} from "./schedule-model.js";
import { loadSchedule, saveSchedule } from "./schedule-storage.js";
import { showBuildingOnMap } from "./map-navigation.js";

let courses = [];
let savingPaused = false;
let editing = null;
let buildingsLoaded = false;
let buildingLoadFailed = false;
const buildingsByCode = new Map();
const form = document.getElementById("schedule-form");
const buildingSelect = document.getElementById("meeting-building");
const buildingStatus = document.getElementById("schedule-buildings-status");
const addButton = document.getElementById("schedule-add");
const feedback = document.getElementById("schedule-feedback");
const courseList = document.getElementById("schedule-list");
const emptyMessage = document.getElementById("schedule-empty");
const storageStatus = document.getElementById("schedule-storage-status");
const editStatus = document.getElementById("schedule-edit-status");
const cancelButton = document.getElementById("schedule-cancel");

function showFeedback(message, isError = false) {
  feedback.textContent = message;
  feedback.classList.toggle("error", isError);
}

function resetScheduleForm() {
  editing = null;
  form.reset();
  addButton.textContent = "Add class meeting";
  cancelButton.hidden = true;
  editStatus.hidden = true;
  editStatus.textContent = "";
}

function showStorageStatus(message, isError = false) {
  storageStatus.textContent = message;
  storageStatus.classList.toggle("error", isError);
}

function restoreSavedSchedule() {
  try {
    courses = loadSchedule();
    savingPaused = false;
    showStorageStatus("Classes save automatically in this browser on this device.");
  } catch {
    // Leave the stored value untouched if it cannot be read or validated.
    savingPaused = true;
    showStorageStatus(
      "Saved classes could not be opened. Existing saved data has been kept. "
      + "Saving is paused; classes added here will be lost on refresh. "
      + "Check that browser storage is allowed, then refresh to try again.",
      true,
    );
  }
  renderSchedule();
}

function saveCurrentSchedule() {
  if (savingPaused) return;
  try {
    saveSchedule(courses);
    showStorageStatus("Schedule saved in this browser on this device.");
  } catch {
    showStorageStatus(
      "Your latest changes could not be saved. They will be lost on refresh. "
      + "Check that browser storage is allowed and has space available.",
      true,
    );
  }
}

function formatTime(time) {
  const [hours, minutes] = time.split(":");
  const hour = Number(hours);
  return `${hour % 12 || 12}:${minutes} ${hour < 12 ? "AM" : "PM"}`;
}

function createMapControls(buildingCode, courseCode, building) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Show building on map";
  const name = building?.name ?? `Building ${buildingCode}`;
  button.setAttribute("aria-label", `Show ${name} on the map for ${courseCode}`);
  const hasMapLocation = Number.isFinite(building?.lat) && Number.isFinite(building?.lon);
  button.disabled = !hasMapLocation;

  const notice = document.createElement("p");
  notice.className = "schedule-note";
  notice.setAttribute("role", "status");
  notice.hidden = hasMapLocation;
  if (!hasMapLocation) {
    if (buildingLoadFailed) {
      notice.textContent = "Building locations could not be loaded. Refresh to try again.";
    } else if (!buildingsLoaded) {
      notice.textContent = "Loading building location...";
    } else {
      notice.textContent = building
        ? "A map location is not available for this building."
        : "This building is no longer in the campus building list.";
    }
  }

  button.addEventListener("click", async () => {
    button.disabled = true;
    notice.hidden = false;
    notice.classList.remove("error");
    notice.textContent = "Opening building on the map...";
    try {
      const buildingName = await showBuildingOnMap(buildingCode);
      notice.textContent = `Showing ${buildingName} on the map.`;
    } catch (error) {
      notice.textContent = error.message;
      notice.classList.add("error");
    } finally {
      button.disabled = false;
    }
  });
  return { button, notice };
}

function renderSchedule() {
  courseList.replaceChildren();
  emptyMessage.hidden = courses.length > 0;

  for (const course of courses) {
    const item = document.createElement("li");
    const heading = document.createElement("h4");
    heading.textContent = course.title
      ? `${course.courseCode} - ${course.title}` : course.courseCode;
    const meetings = document.createElement("ul");

    for (const [meetingIndex, meeting] of course.meetings.entries()) {
      const row = document.createElement("li");
      const days = MEETING_DAYS.filter(day => meeting.days.includes(day.value))
        .map(day => day.label).join(", ");
      const when = document.createElement("p");
      when.textContent = `${days} | ${formatTime(meeting.startTime)} - ${formatTime(meeting.endTime)}`;
      const where = document.createElement("p");
      const building = buildingsByCode.get(meeting.buildingCode);
      const location = building?.name ?? `Building ${meeting.buildingCode}`;
      where.textContent = meeting.room ? `${location}, room ${meeting.room}` : location;
      const actions = document.createElement("div");
      actions.className = "meeting-actions";
      const mapControls = createMapControls(meeting.buildingCode, course.courseCode, building);
      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.textContent = "Edit meeting";
      editButton.setAttribute("aria-label", `Edit ${course.courseCode}, ${when.textContent}`);
      editButton.disabled = editing !== null || buildingsByCode.size === 0;
      editButton.addEventListener("click", () => startEditing(course.id, meetingIndex));
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.textContent = "Delete meeting";
      deleteButton.className = "delete-meeting";
      deleteButton.setAttribute("aria-label", `Delete ${course.courseCode}, ${when.textContent}`);
      deleteButton.disabled = editing !== null;
      deleteButton.addEventListener("click", () => deleteMeeting(course.id, meetingIndex));
      actions.append(mapControls.button, editButton, deleteButton);
      row.append(when, where, actions, mapControls.notice);
      meetings.append(row);
    }

    item.append(heading, meetings);
    courseList.append(item);
  }
}

function startEditing(courseId, meetingIndex) {
  const course = courses.find(item => item.id === courseId);
  const meeting = course?.meetings[meetingIndex];
  if (!meeting || editing !== null) return;

  editing = { courseId, meetingIndex };
  form.elements.namedItem("courseCode").value = course.courseCode;
  form.elements.namedItem("title").value = course.title;
  form.elements.namedItem("startTime").value = meeting.startTime;
  form.elements.namedItem("endTime").value = meeting.endTime;
  buildingSelect.value = meeting.buildingCode;
  form.elements.namedItem("room").value = meeting.room;
  for (const checkbox of form.querySelectorAll('input[name="days"]')) {
    checkbox.checked = meeting.days.includes(checkbox.value);
  }

  editStatus.textContent = `Editing a meeting for ${course.courseCode}. `
    + "Course code and title changes apply to all meetings for this course. "
    + "Day, time, building, and room changes apply to this meeting.";
  editStatus.hidden = false;
  addButton.textContent = "Save changes";
  cancelButton.hidden = false;
  showFeedback("");
  renderSchedule();
  document.getElementById("course-code").focus();
}

function deleteMeeting(courseId, meetingIndex) {
  const course = courses.find(item => item.id === courseId);
  const meeting = course?.meetings[meetingIndex];
  if (!meeting || editing !== null) return;
  const days = MEETING_DAYS.filter(day => meeting.days.includes(day.value))
    .map(day => day.label).join(", ");
  const message = `Delete the ${days}, ${formatTime(meeting.startTime)} - `
    + `${formatTime(meeting.endTime)} meeting for ${course.courseCode}?`
    + (course.meetings.length === 1 ? " This will also remove the course from your schedule." : "");
  if (!window.confirm(message)) return;

  courses = removeCourseMeeting(courses, courseId, meetingIndex);
  saveCurrentSchedule();
  renderSchedule();
  showFeedback(`Deleted the meeting for ${course.courseCode}.`);
  document.getElementById("course-code").focus();
}

cancelButton.addEventListener("click", () => {
  resetScheduleForm();
  renderSchedule();
  showFeedback("Editing canceled.");
  document.getElementById("course-code").focus();
});

form.addEventListener("submit", event => {
  event.preventDefault();
  showFeedback("");
  const values = new FormData(form);

  try {
    const course = createCourse({
      courseCode: values.get("courseCode"),
      title: values.get("title"),
      meetings: [{
        days: values.getAll("days"),
        startTime: values.get("startTime"),
        endTime: values.get("endTime"),
        buildingCode: values.get("buildingCode"),
        room: values.get("room"),
      }],
    });
    const meeting = course.meetings[0];
    if (!buildingsByCode.has(meeting.buildingCode)) {
      throw new Error("Choose a building from the list.");
    }

    const wasEditing = editing !== null;
    if (wasEditing) {
      courses = updateCourseMeeting(courses, editing.courseId, editing.meetingIndex, course);
    } else {
      const existing = courses.find(item => item.courseCode === course.courseCode);
      if (existing) {
        if (existing.meetings.some(item => sameMeeting(item, meeting))) {
          throw new Error("That meeting is already on your schedule.");
        }
        existing.meetings.push(meeting);
        if (course.title) existing.title = course.title;
      } else {
        courses.push(course);
      }
    }

    saveCurrentSchedule();
    resetScheduleForm();
    renderSchedule();
    showFeedback(`${wasEditing ? "Updated" : "Added"} a meeting for ${course.courseCode}.`);
    document.getElementById("course-code").focus();
  } catch (error) {
    showFeedback(error.message, true);
  }
});

async function loadScheduleBuildings() {
  const response = await fetch("/api/buildings");
  if (!response.ok) throw new Error("The building list could not be loaded.");
  const buildings = await response.json();
  if (!Array.isArray(buildings) || buildings.length === 0) {
    throw new Error("No buildings are available yet.");
  }

  const placeholder = document.createElement("option");
  placeholder.value = "";
  placeholder.textContent = "Choose a building";
  buildingSelect.replaceChildren(placeholder);

  for (const building of buildings.sort((first, second) => first.name.localeCompare(second.name))) {
    buildingsByCode.set(building.code, building);
    const option = document.createElement("option");
    option.value = building.code;
    option.textContent = `${building.name} (${building.code})`;
    buildingSelect.append(option);
  }

  buildingSelect.disabled = false;
  addButton.disabled = false;
  buildingsLoaded = true;
  renderSchedule();
}

restoreSavedSchedule();
loadScheduleBuildings().catch(() => {
  buildingLoadFailed = true;
  buildingSelect.options[0].textContent = "Buildings unavailable";
  buildingStatus.textContent = "Could not load buildings. Refresh the page to try again.";
  buildingStatus.classList.add("error");
  renderSchedule();
});
