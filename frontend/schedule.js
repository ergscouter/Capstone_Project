import { createCourse, MEETING_DAYS } from "./schedule-model.js";

const courses = [];
const buildingsByCode = new Map();
const form = document.getElementById("schedule-form");
const buildingSelect = document.getElementById("meeting-building");
const buildingStatus = document.getElementById("schedule-buildings-status");
const addButton = document.getElementById("schedule-add");
const feedback = document.getElementById("schedule-feedback");
const courseList = document.getElementById("schedule-list");
const emptyMessage = document.getElementById("schedule-empty");

function formatTime(time) {
  const [hours, minutes] = time.split(":");
  const hour = Number(hours);
  return `${hour % 12 || 12}:${minutes} ${hour < 12 ? "AM" : "PM"}`;
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

    for (const meeting of course.meetings) {
      const row = document.createElement("li");
      const days = MEETING_DAYS.filter(day => meeting.days.includes(day.value))
        .map(day => day.label).join(", ");
      const when = document.createElement("p");
      when.textContent = `${days} | ${formatTime(meeting.startTime)} - ${formatTime(meeting.endTime)}`;
      const where = document.createElement("p");
      const building = buildingsByCode.get(meeting.buildingCode);
      const location = building?.name ?? `Building ${meeting.buildingCode}`;
      where.textContent = meeting.room ? `${location}, room ${meeting.room}` : location;
      row.append(when, where);
      meetings.append(row);
    }

    item.append(heading, meetings);
    courseList.append(item);
  }
}

function sameMeeting(first, second) {
  return first.days.join(",") === second.days.join(",")
    && first.startTime === second.startTime
    && first.endTime === second.endTime
    && first.buildingCode === second.buildingCode
    && first.room.toLowerCase() === second.room.toLowerCase();
}

form.addEventListener("submit", event => {
  event.preventDefault();
  feedback.textContent = "";
  feedback.classList.remove("error");
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

    renderSchedule();
    form.reset();
    feedback.textContent = `Added a meeting for ${course.courseCode}.`;
    document.getElementById("course-code").focus();
  } catch (error) {
    feedback.textContent = error.message;
    feedback.classList.add("error");
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
}

loadScheduleBuildings().catch(() => {
  buildingSelect.options[0].textContent = "Buildings unavailable";
  buildingStatus.textContent = "Could not load buildings. Refresh the page to try again.";
  buildingStatus.classList.add("error");
});
