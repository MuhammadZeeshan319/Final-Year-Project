# Screening verdicts (checklist items 1-6; item 7 = CV signal, step 3)

| Dataset | Verdict | Reasons |
|---|---|---|
| hsls09_16_student_pets_pear_v1_0.csv (NCES HSLS:09, USA) | Provisionally USABLE | Real govt survey, 1 row = 1 student, 0 duplicates, field of study (CIP) per student, pre-choice transcripts/interests/career goal. Caveat: US population. Post-HS columns (X4/X5/X6/S3/S4) excluded as leakage. |
| uci_dropout_academic_success.csv (Realinho et al. 2022, Portugal) | Provisionally BASELINE ONLY | Real, but target is dropout; Course = 17 programmes at one institution, poor coverage of 7 fields; no subjects/interests/skills/goals. Curricular-units, day/evening, macro columns = leakage. |
| career_path_in_all_field.csv | REJECTED (generated) | Every feature exactly discrete-uniform (0-4 skills: mean 2.0, sd 1.41 = theoretical uniform; 0-9 counts: mean 4.5, sd 2.87 = uniform); GPA continuous uniform 2.5-5.0 (KS p=0.34, impossible on 4.0 scale, 9000 unique 15-decimal floats); Field and Career unrelated (Chemistry->Art Director, Law->Education Administrator); 15 fields near-equal size. |
| student-scores-6k.csv | REJECTED (generated) | Source domain gslingacademy.com = Sling Academy sample-data site; Faker-style names; 4000/6000 rows (66.7%) are duplicates once id/name/email removed (2000 unique records x3); target is career aspiration, not field of study. |

## Item 7 signal check (scripts/01b_signal_check.py, 5x5 repeated stratified CV, mean [95% range])
- career_path, Field from features: RF top1 0.068 [0.059-0.082] vs shuffled 0.067, chance 0.067 -> NO signal. Field from Career: 0.067 -> columns unrelated. Confirms REJECTED.
- student-scores WITH duplicates: RF top1 0.951 -> inflated by copies leaking across folds.
- student-scores deduplicated (n=2000): RF top1 0.489 [0.454-0.530], top3 0.768 vs baseline 0.158 / 0.423, shuffled 0.143.
  Real signal exists, but on a generated sample-data set this is the generator's rule being recovered, not student behaviour.
  Stays REJECTED (item 4: sample-data site + Faker names + 3x duplication; item 2: target is aspiration, not study field).

## Batch 2 (inventory 2026-10-17) - all REJECTED; every one fails item 2 (target is IT roles / single field, not mappable to 7 fields)
| Dataset | Verdict | Reasons |
|---|---|---|
| Career Dataset.xlsx | REJECTED | 2 cols only (free-text Skill -> Career); 6 IT careers only; 1900/4076 (46.6%) exact duplicates; no grades/interests/goals. |
| cs_students.csv | REJECTED | Major constant (all 180 = Computer Science) -> nothing to predict; 89 Faker-style names for 180 rows; n=180. |
| Final_Updated_DMA_DATASET_Indian_Names (1).xlsx | REJECTED (generated) | Emails at tinypic.com / woothemes.com / xing.com / cornell.edu for Indian names = mock-data generator domains; 130 names for 500 rows; flat ratings; courses all IT/business (2-3 of 7 fields). |
| roo_data.csv | REJECTED (generated) | All 9 subject percentages exactly discrete-uniform 60-94 (sd 10.1 = theoretical uniform); 1-9 ratings sd 2.58 = uniform; 6 career areas each ~16.7%; target = 34 IT job roles. |
| Student_Employability_Dataset.csv | REJECTED (generated, duplicate source) | Same data as roo_data.csv (identical value counts in every shared column) + Student_ID + Placement; same uniform signals. |
| Student Data1.csv | REJECTED | Same generator family as roo_data (identical column set, uniform 1-9 ratings, flat interest/career-area classes); target = 12 IT job roles. |

## Item 7 for survivors (scripts/03_evaluate.py --quick, 3-fold x1; full 5x5 run pending)
| Dataset | Best top-1 vs baseline | Best top-3 vs baseline | macro-F1 vs baseline | Shuffled control | FINAL VERDICT |
|---|---|---|---|---|---|
| HSLS questionnaire set (259 cols) | 0.511 vs 0.252 | 0.800 vs 0.573 | 0.469 vs 0.057 | 0.244 / 0.556 (= baseline, no leak) | USABLE - selected |
| UCI (16 pre-enrolment cols) | 0.407 vs 0.269 | 0.813 vs 0.751 (+6 pts only) | 0.289 vs 0.061 | 0.259 / 0.745 | BASELINE ONLY - Engineering n=12 (recall 0), CS n=170 (recall 0.09), no questionnaire-type features, single Portuguese institution |
Note: HSLS 2013 vs 2016 field agreement = 0.778 -> students themselves change field ~22% of the time; no model can be near 100%.

## Full run (5-fold x 5 repeats) - confirms quick run
- HSLS questionnaire set, GradBoost: top1 0.513 [0.494-0.532], top3 0.803 [0.790-0.818], macroF1 0.473 [0.451-0.489] vs baseline 0.252 / 0.573 / 0.057; shuffled 0.247 / 0.565.
- UCI, GradBoost: top1 0.417 [0.393-0.437], top3 0.816 [0.801-0.828] vs baseline 0.269 / 0.751; shuffled 0.266 / 0.744.
Verdicts unchanged: HSLS = USABLE (selected), UCI = BASELINE ONLY.
