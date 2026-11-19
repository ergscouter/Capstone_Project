import { restoreCourse } from "./schedule-model.js";

export const SCHEDULE_STORAGE_KEY = "eagle-eye.schedule";
const STORAGE_VERSION = 1;

export class ScheduleConflictError extends Error {
  constructor() {
    super("The saved schedule changed in another tab.");
    this.name = "ScheduleConflictError";
  }
}

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

export function loadScheduleState() {
  const raw = localStorage.getItem(SCHEDULE_STORAGE_KEY);
  if (raw === null) return { courses: [], snapshot: null };

  const saved = JSON.parse(raw);
  if (!saved || saved.version !== STORAGE_VERSION) {
    throw new Error("The saved schedule format is not supported.");
  }
  return { courses: validateCourses(saved.courses), snapshot: raw };
}

export function loadSchedule() {
  return loadScheduleState().courses;
}

export function saveSchedule(courses, expectedSnapshot = undefined) {
  // The version identifies the format if the course model changes later.
  const saved = { version: STORAGE_VERSION, courses: validateCourses(courses) };
  const serialized = JSON.stringify(saved);
  if (expectedSnapshot !== undefined
      && localStorage.getItem(SCHEDULE_STORAGE_KEY) !== expectedSnapshot) {
    throw new ScheduleConflictError();
  }
  localStorage.setItem(SCHEDULE_STORAGE_KEY, serialized);
  return serialized;
}
