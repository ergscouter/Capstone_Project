export const MEETING_DAYS = [
  { value: "mon", label: "Mon" },
  { value: "tue", label: "Tue" },
  { value: "wed", label: "Wed" },
  { value: "thu", label: "Thu" },
  { value: "fri", label: "Fri" },
  { value: "sat", label: "Sat" },
  { value: "sun", label: "Sun" },
];

const TIME_PATTERN = /^([01]\d|2[0-3]):[0-5]\d$/;

function readText(value, label, maxLength, required = false) {
  if (value != null && typeof value !== "string") {
    throw new Error(`Use text for ${label}.`);
  }
  const text = typeof value === "string" ? value.trim() : "";
  if (required && !text) throw new Error(`Enter ${label}.`);
  if (text.length > maxLength) {
    throw new Error(`Keep ${label} to ${maxLength} characters or fewer.`);
  }
  return text;
}

function createMeeting(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("Enter valid class meeting details.");
  }
  if (!Array.isArray(input.days) || input.days.length === 0) {
    throw new Error("Choose at least one meeting day.");
  }
  if (input.days.some(day => !MEETING_DAYS.some(item => item.value === day))) {
    throw new Error("Choose valid meeting days.");
  }
  const days = MEETING_DAYS.filter(day => input.days.includes(day.value))
    .map(day => day.value);

  if (typeof input.startTime !== "string" || typeof input.endTime !== "string"
      || !TIME_PATTERN.test(input.startTime) || !TIME_PATTERN.test(input.endTime)) {
    throw new Error("Enter a start time and an end time.");
  }
  if (input.endTime <= input.startTime) {
    throw new Error("The end time must be later than the start time.");
  }

  return {
    days,
    // Store campus clock times without converting them to dates or UTC.
    startTime: input.startTime,
    endTime: input.endTime,
    buildingCode: readText(input.buildingCode, "a building", 20, true),
    room: readText(input.room, "the room", 30),
  };
}

function normalizeCourse(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("Enter valid course details.");
  }
  const normalizedCode = readText(input.courseCode, "a course code", 30, true)
    .replace(/\s+/g, " ").toUpperCase();
  const courseCode = readText(normalizedCode, "the course code", 30, true);
  if (!Array.isArray(input.meetings) || input.meetings.length === 0) {
    throw new Error("Add at least one class meeting.");
  }

  return {
    courseCode,
    title: readText(input.title, "the course title", 100),
    meetings: input.meetings.map(createMeeting),
  };
}

// Manual entry and future importers can produce the same course structure.
export function createCourse(input) {
  return { id: crypto.randomUUID(), ...normalizeCourse(input) };
}

export function restoreCourse(input) {
  const course = normalizeCourse(input);
  return { id: readText(input.id, "the saved course ID", 100, true), ...course };
}

export function sameMeeting(first, second) {
  return first.days.join(",") === second.days.join(",")
    && first.startTime === second.startTime
    && first.endTime === second.endTime
    && first.buildingCode === second.buildingCode
    && first.room.toLowerCase() === second.room.toLowerCase();
}

function findMeeting(courses, courseId, meetingIndex) {
  const course = courses.find(item => item.id === courseId);
  if (!course || !Number.isInteger(meetingIndex)
      || meetingIndex < 0 || meetingIndex >= course.meetings.length) {
    throw new Error("That class meeting could not be found.");
  }
  return course;
}

export function updateCourseMeeting(courses, courseId, meetingIndex, input) {
  const existing = findMeeting(courses, courseId, meetingIndex);
  const changes = normalizeCourse(input);
  if (changes.meetings.length !== 1) {
    throw new Error("Edit one meeting at a time.");
  }
  if (courses.some(course => course.id !== courseId && course.courseCode === changes.courseCode)) {
    throw new Error(`Another course already uses ${changes.courseCode}. Choose a different course code.`);
  }
  const meeting = changes.meetings[0];
  if (existing.meetings.some((item, index) => index !== meetingIndex && sameMeeting(item, meeting))) {
    throw new Error("That meeting is already on your schedule.");
  }

  // Keep the course ID and other meetings when updating this one.
  const updated = {
    ...existing,
    courseCode: changes.courseCode,
    title: changes.title,
    meetings: existing.meetings.map((item, index) => index === meetingIndex ? meeting : item),
  };
  return courses.map(course => course.id === courseId ? updated : course);
}

export function removeCourseMeeting(courses, courseId, meetingIndex) {
  const existing = findMeeting(courses, courseId, meetingIndex);
  const meetings = existing.meetings.filter((item, index) => index !== meetingIndex);
  if (meetings.length === 0) return courses.filter(course => course.id !== courseId);
  return courses.map(course => course.id === courseId ? { ...course, meetings } : course);
}
