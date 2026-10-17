"""
Extra curated data for the career/program stage - typical values, NOT verified official rules.

  MIN_PCT : usual minimum intermediate marks per program (PMDC/PEC/HEC-style rules; many universities ask
            more). Shown to students as "usual minimum - check each university".
  SKILLS  : 4 core skills per career for the skill-gap check, each with a tip for building it and optional
            evidence from the field questionnaire that pre-ticks it ("from your answers").
Review both with your supervisor; replace with verified values per university next semester.
"""
from career_bank import BANK, PROGRAMS

MIN_PCT_DEFAULT = 45
MIN_PCT = {
    "mbbs": 60, "bds": 60, "pharmd": 60, "dpt": 60, "bsn": 50, "mlt": 50, "nutrition": 50,
    "ee": 60, "me": 60, "ce": 60, "che": 60, "mte": 60, "arch": 50,
    "bscs": 50, "bsse": 50, "bsai": 50, "bsds": 50, "bscyber": 50, "bsit": 50,
    "llb": 45,
}
for _pid, _p in PROGRAMS.items():
    _p["min_pct"] = MIN_PCT.get(_pid, MIN_PCT_DEFAULT)


def S(name, tip, **evidence):
    return {"name": name, "tip": tip, "evidence": evidence}


_AGREE = ["Strongly agree", "Agree"]
MATHS = S("Maths", "Practise past papers and a free online calculus/statistics course.",
          math_confident=_AGREE, math_person=_AGREE)
SCIENCE = S("Science foundations", "Revise intermediate physics, chemistry and biology concepts.", science_person=_AGREE)
BIOLOGY = S("Biology", "Strengthen anatomy and physiology basics; MDCAT preparation books help.", fav_subject=["Biology"])
CHEM = S("Chemistry", "Revise organic, inorganic and physical chemistry.", fav_subject=["Chemistry"])
COMMS = S("Communication", "Join a debate or presentation club; practise explaining topics to others.")
PROGRAMMING = S("Programming", "Start with Python - build one small project every week.", fav_subject=["Computer Science"])
ENGLISH = S("English reading & writing", "Read one long article a day and write a short summary.", fav_subject=["English"])
STATS = S("Statistics & probability", "Take a free introductory statistics course.")
SHEETS = S("Spreadsheets", "Analyse a small dataset or budget in Excel or Google Sheets.")
DETAIL = S("Attention to detail", "Practise careful, step-by-step work and double-check your answers.")
TEAM = S("Teamwork", "Join group projects, clubs or volunteering teams.")
CALM = S("Calm under pressure", "Take a first-aid course (e.g. Red Crescent) or volunteer at a hospital.")
LAB = S("Lab techniques", "Do extra practicals carefully; learn to use a microscope well.")
CREATIVE = S("Creativity", "Keep a scrapbook of designs and ideas you like and try your own versions.")
DRAW = S("Drawing & sketching", "Sketch something every day.")
NEWS = S("Current affairs", "Follow national and international news every day.")
DEBATE = S("Debating & public speaking", "Join a debating society or Model United Nations.")
NETWORK = S("Networking basics", "Learn how the internet works: IP addresses, DNS, routers, HTTP.")
EMPATHY = S("Listening & empathy", "Volunteer with a welfare organisation or peer-support group.")
ELECTRONICS = S("Electronics tinkering", "Build simple circuits or a small robot with an Arduino kit.")
MECHANICS = S("Physics (mechanics)", "Revise forces, motion and energy; solve extra problems.", fav_subject=["Physics"])

SKILLS = {
    # Medical & Health
    "doctor": [BIOLOGY, S("Long-term study discipline", "Plan a weekly study timetable for MDCAT and keep to it."), CALM, COMMS],
    "dentist": [BIOLOGY, S("Fine hand skills", "Try drawing, model making or any precise craft."), DETAIL, COMMS],
    "pharmacist": [CHEM, BIOLOGY, DETAIL, COMMS],
    "physio": [BIOLOGY, S("Fitness & human movement", "Play a sport and learn basic exercise science."), EMPATHY, COMMS],
    "nurse": [BIOLOGY, TEAM, CALM, EMPATHY],
    "lab": [BIOLOGY, LAB, DETAIL, CHEM],
    "nutritionist": [BIOLOGY, CHEM, COMMS, S("Interest in food & health", "Track your own diet for a week and read nutrition labels.")],
    # Engineering & Tech
    "electrical": [MATHS, S("Physics (electricity & magnetism)", "Revise circuits and electromagnetism chapters.", fav_subject=["Physics"]), ELECTRONICS, PROGRAMMING],
    "mechanical": [MATHS, MECHANICS, S("Hands-on building", "Repair or build something mechanical; try a free CAD tutorial."), S("Problem solving", "Solve one challenging physics problem set a week.")],
    "civil": [MATHS, MECHANICS, S("Technical drawing / CAD", "Learn basic AutoCAD from free tutorials."), TEAM],
    "chemical": [MATHS, CHEM, S("Problem solving", "Practise numerical chemistry and physics problems."), S("Safety mindset", "Read about lab and industrial safety rules.")],
    "mechatronics": [MATHS, PROGRAMMING, ELECTRONICS, MECHANICS],
    "architect": [DRAW, CREATIVE, MATHS, S("3D / CAD software", "Try SketchUp or Blender with free tutorials.")],
    # CS & IT
    "software": [PROGRAMMING, S("Problem solving", "Solve beginner problems on a coding practice website."), TEAM, MATHS],
    "web_mobile": [PROGRAMMING, S("Web basics (HTML, CSS, JavaScript)", "Build your own personal website."), S("Design sense", "Recreate the layout of an app you like."), TEAM],
    "ai": [MATHS, PROGRAMMING, STATS, S("Research curiosity", "Read one AI article a week and summarise it.")],
    "data": [MATHS, STATS, PROGRAMMING, SHEETS],
    "cyber": [PROGRAMMING, NETWORK, S("Puzzle solving", "Try beginner capture-the-flag (CTF) challenges."), S("Ethics & responsibility", "Learn where ethical hacking ends and illegal hacking begins.")],
    "network": [NETWORK, S("Troubleshooting", "Fix computer problems for family and friends."), PROGRAMMING, S("Linux basics", "Install Linux in a virtual machine and learn basic commands.")],
    # Business
    "accountant": [MATHS, SHEETS, DETAIL, ENGLISH],
    "finance": [MATHS, SHEETS, S("Interest in markets", "Follow the stock exchange and business news weekly."), COMMS],
    "marketing": [COMMS, CREATIVE, S("Understanding people", "Ask friends why they buy what they buy."), ENGLISH],
    "entrepreneur": [S("Leadership", "Lead a club, event or small team project."), COMMS, S("Resilience", "Start a small online project and learn from what goes wrong."), S("Money basics", "Track the costs and profit of a small sale or event.")],
    "hr": [COMMS, EMPATHY, S("Organisation", "Plan and run an event from start to finish."), ENGLISH],
    "analyst": [MATHS, SHEETS, STATS, COMMS],
    # Natural Sciences
    "biotech": [BIOLOGY, CHEM, LAB, S("Research curiosity", "Read popular science articles on genetics.")],
    "microbiologist": [BIOLOGY, LAB, DETAIL, CHEM],
    "chemist": [CHEM, LAB, MATHS, S("Safety mindset", "Learn and follow lab safety rules.")],
    "physicist": [MATHS, S("Physics", "Solve physics problems beyond the syllabus.", fav_subject=["Physics"]), S("Problem solving", "Try physics olympiad-style questions."), PROGRAMMING],
    "mathematician": [MATHS, S("Logical proofs", "Work through a beginner's book or course on proofs."), S("Problem solving", "Try maths olympiad problems."), PROGRAMMING],
    "environmental": [SCIENCE, S("Fieldwork & observation", "Join a tree-planting or clean-up campaign and record what you see."), S("Report writing", "Write a short report on a local environmental issue."), S("Maps & data (GIS)", "Explore Google Earth and simple map data.")],
    # Social Sci / Law / Psych
    "lawyer": [ENGLISH, DEBATE, S("Logical reasoning", "Practise LAT-style reasoning questions."), S("Reading stamina", "Read a long newspaper editorial every day.")],
    "psychologist": [EMPATHY, S("Curiosity about people", "Read an introductory psychology book."), ENGLISH, S("Research basics", "Learn how surveys and experiments are designed.")],
    "economist": [MATHS, STATS, S("Following the economy", "Read business news and State Bank updates."), ENGLISH],
    "diplomat": [ENGLISH, NEWS, DEBATE, S("Languages", "Start learning a foreign language with an app.")],
    "civil_servant": [ENGLISH, NEWS, S("General knowledge", "Practise CSS-style general knowledge questions."), COMMS],
    "social_worker": [EMPATHY, COMMS, S("Community organising", "Help organise a community event."), ENGLISH],
    # Education / Humanities / Arts
    "teacher": [COMMS, S("Patience", "Tutor younger students or siblings regularly."), S("Subject knowledge", "Master one subject you would like to teach."), S("Planning", "Plan a short lesson and teach it to friends.")],
    "journalist": [ENGLISH, S("Writing to deadlines", "Write a short news story every week."), S("Interviewing", "Interview people about a local issue."), S("Photo & video basics", "Shoot and edit short reports on your phone.")],
    "designer": [DRAW, S("Design software", "Learn Canva, then Figma or Photoshop from free tutorials."), CREATIVE, S("Portfolio", "Collect your 10 best designs in one place.")],
    "writer": [ENGLISH, S("Regular writing", "Write 300 words every day - stories, blogs or poems."), S("Reading widely", "Read one book a month in different genres."), S("Editing", "Rewrite and improve something you wrote last week.")],
    "filmmaker": [S("Video shooting & editing", "Make short films on your phone and edit them with free software."), S("Storytelling", "Write short scripts or storyboards."), CREATIVE, TEAM],
    "linguist": [ENGLISH, S("Second language", "Start learning another language with an app."), S("Urdu reading & writing", "Read Urdu literature and write short pieces.", fav_subject=["Urdu"]), S("Translation practice", "Translate short articles between Urdu and English.")],
}

_all = [c for b in BANK.values() for c in b["careers"]]
assert set(SKILLS) == set(_all), f"SKILLS out of sync: missing {set(_all) - set(SKILLS)}, extra {set(SKILLS) - set(_all)}"


def skill_gap(career_id, profile=None):
    """Skills for a career; 'suggested' = pre-ticked because the student's questionnaire answers show it."""
    profile = profile or {}
    out = []
    for s in SKILLS.get(career_id, []):
        hit = next((f"{q}: {profile[q]}" for q, ok in s["evidence"].items() if profile.get(q) in ok), None)
        out.append({"name": s["name"], "tip": s["tip"], "suggested": bool(hit), "evidence": hit})
    return out
