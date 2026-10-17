# Edu Path - algorithm comparison (2026-10-17)

Dataset: HSLS:09 questionnaire set, n=10585 students, 259 features, 7 fields. Protocol: repeated stratified 5-fold CV x 5; duplicates removed before CV; imputation/scaling fitted inside each training fold; fixed hyperparameters (listed in scripts/03b_compare_models.py), no tuning on test folds. Values = mean [2.5-97.5 percentile over folds]. P@3 max = 0.333 because each student has one true field. R@3 = top-3 accuracy.

## Results

```
                              model                top1                top3             macroF1                 P@3                 R@3              NDCG@3 seconds
     Baseline (largest / 3 biggest)               0.252               0.573               0.057               0.191               0.573               0.435        
                            XGBoost 0.520 [0.505-0.536] 0.810 [0.797-0.824] 0.479 [0.460-0.494] 0.270 [0.266-0.275] 0.810 [0.797-0.824] 0.689 [0.678-0.702]     150
                      HistGradBoost 0.513 [0.494-0.532] 0.803 [0.790-0.818] 0.473 [0.451-0.489] 0.268 [0.263-0.273] 0.803 [0.790-0.818] 0.682 [0.671-0.696]     175
                Logistic Regression 0.502 [0.489-0.513] 0.800 [0.787-0.812] 0.460 [0.445-0.475] 0.267 [0.262-0.271] 0.800 [0.787-0.812] 0.675 [0.666-0.685]     120
XGBoost - SHUFFLED labels (control) 0.222 [0.219-0.226] 0.548 [0.534-0.556] 0.110 [0.107-0.116] 0.183 [0.178-0.185] 0.548 [0.534-0.556] 0.408 [0.399-0.413]        
```

## Recall per field (first repeat, out-of-fold)

```
                    field    n  XGBoost  HistGradBoost  Logistic Regression
                 Business 1590    0.464          0.440                0.440
                  CS & IT  395    0.271          0.278                0.261
Education/Humanities/Arts 1811    0.606          0.610                0.595
       Engineering & Tech 1460    0.555          0.547                0.546
         Medical & Health 2666    0.668          0.674                0.644
         Natural Sciences 1298    0.319          0.304                0.311
     Social Sci/Law/Psych 1365    0.396          0.385                0.380
```

