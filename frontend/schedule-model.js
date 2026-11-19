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
  const courseCode = readText(input.courseCode, "a course code", 30, true)
    .replace(/\s+/g, " ").toUpperCase();
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
