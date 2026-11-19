import { restoreCourse } from "./schedule-model.js";

const SCHEDULE_STORAGE_KEY = "eagle-eye.schedule";
const STORAGE_VERSION = 1;

function validateCourses(courses) {
  if (!Array.isArray(courses)) throw new Error("Invalid saved course list.");
  const restored = courses.map(restoreCourse);
  const ids = new Set(restored.map(course => course.id));
  const codes = new Set(restored.map(course => course.courseCode));
  if (ids.size !== restored.length || codes.size !== restored.length) {
    throw new Error("The saved schedule contains duplicate courses.");
  }
  return restored;
}

export function loadSchedule() {
  const raw = localStorage.getItem(SCHEDULE_STORAGE_KEY);
  if (raw === null) return [];

  const saved = JSON.parse(raw);
  if (!saved || saved.version !== STORAGE_VERSION) {
    throw new Error("The saved schedule format is not supported.");
  }
  return validateCourses(saved.courses);
}

export function saveSchedule(courses) {
  // The version identifies the format if the course model changes later.
  const saved = { version: STORAGE_VERSION, courses: validateCourses(courses) };
  localStorage.setItem(SCHEDULE_STORAGE_KEY, JSON.stringify(saved));
}
