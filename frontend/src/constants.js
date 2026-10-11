// Everything the questionnaire and sidebar need. Keys match the backend feature names exactly
// (backend/features.py), so don't rename them without changing the backend too.

// Grades. The numbers are the GPA values the model was trained on (4.0 scale);
// the percentages are only approximate hints for students -- adjust them to your grading scale.
export const GRADES = [
  ["3.9", "Mostly A's (about 80% or more)"],
  ["3.5", "A's and B's (about 70 to 80%)"],
  ["3.0", "Mostly B's (about 60 to 70%)"],
  ["2.5", "B's and C's (about 55 to 60%)"],
  ["2.0", "Mostly C's (about 50 to 55%)"],
  ["1.3", "Below C (under about 50%)"],
];
export const GRADE_FIELDS = [
  ["gpa_english", "English"],
  ["gpa_math", "Math"],
  ["gpa_science", "Science"],
  ["gpa_social", "Social studies / history"],
  ["gpa_overall", "Overall"],
];

export const LEVELS = [
  ["0", "None"],
  ["1", "A year or less"],
  ["2", "More than a year and a half"],
];
export const ELECTIVES = [
  ["lvl_cs", "Computer science / coding"],
  ["lvl_engineering", "Engineering / technology"],
  ["lvl_art", "Art / design"],
  ["lvl_business", "Business / marketing"],
  ["lvl_health", "Health science"],
  ["lvl_media", "Media / communications"],
  ["lvl_agriculture", "Agriculture"],
  ["lvl_language", "Foreign languages"],
  ["lvl_architecture", "Architecture / construction"],
  ["lvl_publicservice", "Law / public safety / government"],
  ["lvl_humanservices", "Cooking, hospitality or personal services"],
];

export const ACTIVITIES = [
  ["act_music", "Music (band, choir)"],
  ["act_art", "Art"],
  ["act_drama", "Drama / theatre"],
  ["act_sports", "Sports"],
  ["act_club", "School clubs"],
  ["act_academic", "Academic clubs or competitions"],
  ["act_hosa", "Health or medical society / first-aid club"],
  ["act_ffa", "Agriculture or farming club"],
];

export const OCCUPATIONS = [
  ["11", "Leading or managing a business"],
  ["13", "Business, finance, accounting"],
  ["15", "Computers and math"],
  ["17", "Engineering and architecture"],
  ["19", "Science research"],
  ["21", "Counselling, social or community work"],
  ["23", "Law"],
  ["25", "Teaching"],
  ["27", "Arts, design, media, entertainment or sports"],
  ["29", "Doctor, nurse or other health professional"],
  ["31", "Healthcare support (assistant, technician)"],
  ["33", "Police, fire or protective services"],
  ["35", "Food and hospitality"],
  ["39", "Personal care and services"],
  ["41", "Sales"],
  ["45", "Farming and forestry"],
  ["47", "Construction"],
  ["49", "Repair and maintenance"],
  ["51", "Manufacturing and production"],
  ["53", "Transportation"],
  ["55", "Military"],
  ["98", "I'm not sure yet"],
];

export const INITIAL_FORM = {
  ...Object.fromEntries(GRADE_FIELDS.map(([k]) => [k, ""])),
  ...Object.fromEntries(ELECTIVES.map(([k]) => [k, ""])),
  ...Object.fromEntries(ACTIVITIES.map(([k]) => [k, false])),
  occupation: "",
};

// Left sidebar. status "ready" = built; "soon" = placeholder page for a teammate's module.
export const FEATURES = [
  { to: "/app", label: "Field recommendation", status: "ready", end: true },
  { to: "/app/careers", label: "Career guidance", status: "ready" },
  {
    to: "/app/programs",
    label: "Program recommendation",
    status: "soon",
    description: "Degree programs that match your recommended field, your interests and your career goals.",
  },
  {
    to: "/app/eligibility",
    label: "Eligibility checker",
    status: "soon",
    description: "Checks your marks and subjects against each program's admission requirements.",
  },
  {
    to: "/app/universities",
    label: "University ranking",
    status: "soon",
    description: "Ranks the universities you are eligible for using your own priorities (budget, location, scholarships).",
  },
  {
    to: "/app/compare",
    label: "University comparison",
    status: "soon",
    description: "Compare shortlisted universities side by side on fees, eligibility, location and scholarships.",
  },
  {
    to: "/app/skills",
    label: "Skill gap analysis",
    status: "soon",
    description: "Shows which skills you already have and which you need for your chosen career.",
  },
];
