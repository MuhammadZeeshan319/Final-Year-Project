"""
Documented target mappings -> 7 broad fields. Every rule here is a decision that must be
reported; codes mapped to None are DROPPED (and counted in reports/cleaning_log.md).
"""
FIELDS = [
    "Medical & Health",
    "Engineering & Tech",
    "CS & IT",
    "Business",
    "Natural Sciences",
    "Social Sci/Law/Psych",
    "Education/Humanities/Arts",
]

# HSLS:09 S3FIELD2 / S4FIELD2 = 2-digit CIP 2010 family of the student's major.
# Negative codes = NCES missing codes (-1 don't know, -3 carry-through, -4 nonresponse,
# -5 suppressed, -6 not applicable, -7 legitimate skip, -8 unit nonresponse, -9 missing).
CIP2_TO_FIELD = {
    51: "Medical & Health",          # Health professions (nursing, pharmacy, pre-med...)
    60: "Medical & Health",          # Health professions residency programs
    14: "Engineering & Tech",        # Engineering
    15: "Engineering & Tech",        # Engineering technologies
    4:  "Engineering & Tech",        # Architecture
    10: "Engineering & Tech",        # Communications technologies (AV/broadcast tech)   [AMBIGUOUS]
    11: "CS & IT",                   # Computer & information sciences
    52: "Business",                  # Business, management, marketing
    26: "Natural Sciences",          # Biological & biomedical sciences
    40: "Natural Sciences",          # Physical sciences
    27: "Natural Sciences",          # Mathematics & statistics
    1:  "Natural Sciences",          # Agriculture
    3:  "Natural Sciences",          # Natural resources & conservation
    41: "Natural Sciences",          # Science technologies
    42: "Social Sci/Law/Psych",      # Psychology
    45: "Social Sci/Law/Psych",      # Social sciences
    22: "Social Sci/Law/Psych",      # Legal professions & studies
    43: "Social Sci/Law/Psych",      # Homeland security, law enforcement (criminal justice)
    44: "Social Sci/Law/Psych",      # Public administration & social service
    5:  "Social Sci/Law/Psych",      # Area, ethnic, gender studies
    19: "Social Sci/Law/Psych",      # Family & consumer / human sciences   [AMBIGUOUS]
    13: "Education/Humanities/Arts", # Education
    50: "Education/Humanities/Arts", # Visual & performing arts
    23: "Education/Humanities/Arts", # English language & literature
    16: "Education/Humanities/Arts", # Foreign languages
    38: "Education/Humanities/Arts", # Philosophy & religious studies
    39: "Education/Humanities/Arts", # Theology
    54: "Education/Humanities/Arts", # History   [AMBIGUOUS: could be Social Sci]
    9:  "Education/Humanities/Arts", # Communication, journalism   [AMBIGUOUS]
    31: "Medical & Health",          # Parks, recreation, fitness (mostly kinesiology/exercise sci)   [AMBIGUOUS]
    # --- DROPPED: not a field choice (undeclared / general) ---
    24: None,                        # Liberal arts & general studies = US "undecided" track
    30: None,                        # Multi/interdisciplinary - cannot be assigned
    99: None,                        # Undeclared / other
    # --- DROPPED: vocational trades, outside the 7 fields (user decision 2026-10-17) ---
    12: None,                        # Personal & culinary services
    46: None,                        # Construction trades
    47: None,                        # Mechanic & repair technologies
    48: None,                        # Precision production
    49: None,                        # Transportation & materials moving
    28: None, 29: None,              # ROTC / military technologies
    32: None, 33: None, 34: None, 35: None, 36: None, 37: None,  # basic skills / leisure / personal
}

# UCI "Predict students' dropout and academic success" Course codes (from UCI documentation).
UCI_COURSE_TO_FIELD = {
    33:   "Engineering & Tech",        # Biofuel Production Technologies
    171:  "Education/Humanities/Arts", # Animation and Multimedia Design
    8014: "Social Sci/Law/Psych",      # Social Service (evening)
    9003: "Natural Sciences",          # Agronomy
    9070: "Education/Humanities/Arts", # Communication Design
    9085: "Medical & Health",          # Veterinary Nursing
    9119: "CS & IT",                   # Informatics Engineering
    9130: "Natural Sciences",          # Equinculture
    9147: "Business",                  # Management
    9238: "Social Sci/Law/Psych",      # Social Service
    9254: "Business",                  # Tourism
    9500: "Medical & Health",          # Nursing
    9556: "Medical & Health",          # Oral Hygiene
    9670: "Business",                  # Advertising and Marketing Management
    9773: "Education/Humanities/Arts", # Journalism and Communication (same rule as CIP 09)
    9853: "Education/Humanities/Arts", # Basic Education
    9991: "Business",                  # Management (evening)
}
