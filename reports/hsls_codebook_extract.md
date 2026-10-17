# HSLS:09 codebook extract - variables used by Edu Path

Sources (in docs/):
- NCES 2014-361, Appendix I "Hard Copy Codebooks: Student and School" (X1/X2/S1/S2 variables)
- NCES 2015-036, student codebook (2013 update + high-school transcript, X3T* variables)

Missing codes (all variables): -9 Missing, -8 Unit non-response, -7 Item legitimate skip, -5 suppressed on public file.

## Career goal
**X2STU30OCC2 / X1STU30OCC2** - Student occupation at age 30, 2-digit O*NET (SOC major group). X2 = spring 2012 (11th grade), X1 = fall 2009 (9th grade).
| Code | Occupation group | Code | Occupation group |
|---|---|---|---|
| 11 | Management | 33 | Protective service |
| 13 | Business and financial operations | 35 | Food preparation and serving |
| 15 | Computer and mathematical | 39 | Personal care and service |
| 17 | Architecture and engineering | 41 | Sales |
| 19 | Life, physical, and social science | 43 | Office and administrative support (X2 only) |
| 21 | Community and social services | 45 | Farming, fishing, forestry (X1 only) |
| 23 | Legal | 47 | Construction and extraction |
| 25 | Education, training, and library | 49 | Installation, maintenance, repair |
| 27 | Arts, design, entertainment, sports, media | 51 | Production |
| 29 | Healthcare practitioners and technical | 53 | Transportation and material moving |
| 31 | Healthcare support (X1 only) | 55 | Military specific |
| 98 | **Don't know** | 99 | Uncodeable (X2 only) |

**X2STU30OCC_STEM1** - STEM sub-domain of the same job (derived from 6-digit code, not a separate question):
0 Not STEM; 1 Life/physical science, engineering, mathematics, IT; 4 Health; 5 Split across 2 sub-domains (public file: social science + architecture recoded here); 6 Unspecified sub-domain; 9 Uncodeable.

**S2OCC30THINK** - How much thought about job at 30: 1 Not at all, 2 A little, 3 Somewhat, 4 A lot.
**S2OCC30CERTAIN** - Certainty about that job: 1 Very certain, 2 Fairly certain, 3 Not certain.

**S2EDUEXP** - How far in school the student thinks they will get:
1 Less than HS; 2 HS diploma; 3 Start occupational certificate; 4 Complete occupational certificate; 5 Start Associate's; 6 Complete Associate's; 7 Start Bachelor's; 8 Complete Bachelor's; 9 Start Master's; 10 Complete Master's; 11 Start PhD/MD/law; 12 Complete PhD/MD/law/other high professional; 13 Don't know.

## Interests
**S2FAVSUBJ** (11th grade), **S1FAVSUBJ** / **S1LEASTSUBJ** (9th grade) - favourite / least favourite school subject:
1 English; 2 Foreign language; 3 Science; 4 Art; 5 Music; 6 Mathematics; 7 Physical education; 8 Religion; 9 Health education; 10 Computer science; 11 Social studies/history/government/civics; 12 Career preparation class; 13 Other.

**S1WEBINFO** - How often used the web for computer technology information: 1 Never, 2 Rarely, 3 Sometimes, 4 Often.

### Scales (standardised composites, mean 0 / sd 1, built by PCA from the raw items below)
Raw items are answered 1 Strongly agree, 2 Agree, 3 Disagree, 4 Strongly disagree.
| Scale | Raw items (codebook label) |
|---|---|
| X2SCIID science identity | S2SPERSON1 "sees himself/herself as a science person"; S2SPERSON2 "others see teenager as a science person" |
| X2MTHID math identity | S2MPERSON1, S2MPERSON2 (same wording, math) |
| X2SCIUTI science utility | S2SUSELIFE useful for everyday life; S2SUSECLG useful for college; S2SUSEJOB useful for future career |
| X2MTHUTI math utility | S2MUSELIFE, S2MUSECLG, S2MUSEJOB (same, math) |
| X2SCIINT interest in science course | S2SENJOYING, S2SWASTE, S2SBORING, S2FAVSUBJ, S2SENJOYS |
| X2MTHEFF math self-efficacy | S2MTESTS "confident can do excellent job on math tests"; S2MTEXTBOOK "certain can understand math textbook"; S2MSKILLS "certain can master skills taught"; S2MASSEXCL "confident can do excellent job on math assignments" |

PCA weights are not published in the codebook, so the tool cannot reproduce the composite from a new student's answers exactly. -> Step 5 uses the RAW items (all present in datasets/derived/hsls_prechoice.csv.gz) instead of the composites.

## Grades / subjects (high-school transcript)
**X3THIMATH** - Highest level mathematics course taken:
0 No math; 1 Basic math; 2 Other math; 3 Pre-algebra; 4 Algebra I; 5 Geometry; 6 Algebra II; 7 Trigonometry; 8 Other advanced math; 9 Probability and statistics; 10 Other AP/IB math; 11 Precalculus; 12 Calculus; 13 AP/IB Calculus.

**X3TCREDSCI / X3TCREDSTEM / X3TCREDCOMPSCI / X3TCREDART** - Carnegie credits earned in science / STEM / computer science / fine arts (1 credit = one year-long course).
