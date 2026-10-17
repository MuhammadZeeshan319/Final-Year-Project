# Edu Path - question contribution (XGBoost) (2026-10-17)

n=10585 HSLS:09 students, CV 5-fold x 3. Ablation and top-N use the same folds. Top-N selection is nested (SHAP ranking on training folds only).

## Group ablation

```
                                   config  questions                top1                top3             macroF1               NDCG3  delta_top1_vs_ALL  delta_top3_vs_ALL
                            ALL questions        179 0.519 [0.504-0.535] 0.810 [0.798-0.825] 0.478 [0.462-0.493] 0.689 [0.677-0.703]              0.000              0.000
                               ONLY goals          9 0.484 [0.468-0.498] 0.764 [0.751-0.776] 0.441 [0.422-0.453] 0.647 [0.636-0.659]             -0.035             -0.046
                              ONLY grades         88 0.352 [0.329-0.367] 0.714 [0.702-0.726] 0.291 [0.274-0.302] 0.560 [0.544-0.570]             -0.168             -0.097
                           ONLY interests         34 0.351 [0.335-0.366] 0.724 [0.712-0.733] 0.305 [0.292-0.316] 0.566 [0.559-0.572]             -0.169             -0.086
                              ONLY skills         48 0.263 [0.251-0.282] 0.624 [0.614-0.636] 0.171 [0.158-0.188] 0.469 [0.461-0.482]             -0.256             -0.186
                            WITHOUT goals        170 0.401 [0.382-0.416] 0.759 [0.747-0.776] 0.356 [0.336-0.371] 0.608 [0.598-0.619]             -0.118             -0.052
                           WITHOUT grades         91 0.509 [0.495-0.523] 0.802 [0.795-0.813] 0.466 [0.450-0.482] 0.679 [0.673-0.689]             -0.011             -0.009
                        WITHOUT interests        145 0.509 [0.492-0.528] 0.799 [0.784-0.808] 0.463 [0.447-0.483] 0.677 [0.665-0.690]             -0.010             -0.012
                           WITHOUT skills        131 0.522 [0.510-0.536] 0.812 [0.801-0.829] 0.483 [0.469-0.495] 0.691 [0.682-0.707]              0.003              0.002
WITHOUT US test scores (Pakistan-askable)        135 0.522 [0.507-0.540] 0.815 [0.798-0.828] 0.483 [0.464-0.500] 0.693 [0.679-0.707]              0.003              0.005
```

## Accuracy vs number of questions (nested)

```
top_N_questions                top1                top3             macroF1               NDCG3
              5 0.497 [0.486-0.513] 0.791 [0.780-0.801] 0.443 [0.430-0.457] 0.668 [0.659-0.681]
             10 0.507 [0.486-0.518] 0.800 [0.789-0.812] 0.468 [0.444-0.485] 0.677 [0.664-0.689]
             15 0.510 [0.499-0.528] 0.804 [0.795-0.811] 0.470 [0.458-0.487] 0.681 [0.672-0.693]
             20 0.511 [0.495-0.526] 0.804 [0.792-0.817] 0.471 [0.453-0.486] 0.682 [0.669-0.694]
             30 0.515 [0.500-0.531] 0.805 [0.794-0.817] 0.474 [0.454-0.490] 0.684 [0.672-0.697]
             50 0.517 [0.502-0.535] 0.810 [0.796-0.821] 0.475 [0.455-0.492] 0.688 [0.674-0.701]
      ALL (179) 0.519 [0.504-0.535] 0.810 [0.798-0.825] 0.478 [0.462-0.493] 0.689 [0.677-0.703]
```

## SHAP share by group (final model)

```
    group   share_%
    goals 27.000000
   grades 33.599998
interests 24.400000
   skills 14.900000
```

## Top 30 questions by SHAP (final model)

```
        question     group  share_%
     X2STU30OCC2     goals    13.16
X2STU30OCC_STEM1     goals     4.54
       S2FAVSUBJ interests     4.00
     X1STU30OCC2     goals     3.56
         X2SCIID interests     2.76
         X2MTHID interests     1.92
        S2EDUEXP     goals     1.90
      X3TCREDSCI    grades     1.63
        X2SCIUTI interests     1.58
        X2SCIINT interests     1.45
     X3TCREDSTEM    grades     1.43
       X3THIMATH    grades     1.39
     S1LEASTSUBJ interests     1.36
      X3TCREDART    grades     1.20
       S1FAVSUBJ interests     1.16
  X3TCREDCOMPSCI    grades     1.08
        X2MTHUTI interests     1.07
        X2MTHEFF    skills     1.02
    S2OCC30THINK     goals     0.97
       S1WEBINFO interests     0.97
  S2OCC30CERTAIN     goals     0.93
      X3TCREDBUS    grades     0.85
        X1MTHINT interests     0.83
    X3TCREDSOCST    grades     0.81
        S2SPORTS interests     0.79
   X3TCREDHELSCI    grades     0.77
      X3TGPALANG    grades     0.75
    S1OCC30THINK     goals     0.74
        X1SCIINT interests     0.73
     S1EDUEXPECT     goals     0.71
```

