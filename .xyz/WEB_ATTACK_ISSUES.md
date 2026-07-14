# Web Attack Model - Issue Analysis

## CRITICAL ISSUES IDENTIFIED

### Issue 1: Class Imbalance (PRIMARY CAUSE)
- Dataset: 174,015 attacks (94%) vs 11,337 benign (6%)  
- Ratio: 15:1 (severe imbalance)
- Model predicts ALL as attack to maximize accuracy
- Confusion Matrix: 0 benign correctly classified!

### Issue 2: Misleading Metrics
- 93.88% accuracy appears good
- But benign precision = 0%, benign recall = 0%
- Balanced accuracy = 50% (random guessing!)

### Issue 3: No Class Balancing
- No class weights applied
- No SMOTE oversampling
- No undersampling

### Issue 4: Missing Validation
- No cross-validation
- No per-class metric monitoring
- Early stopping on overall accuracy (misleading)

## PROPOSED FIXES

1. Apply class weights in training
2. Use SMOTE for benign samples
3. Monitor balanced accuracy
4. Add 5-fold cross-validation
5. Report per-class metrics

## TARGET METRICS (Re-training)

- Overall Accuracy: 80-95%
- Benign Precision: >70% (currently 0%)
- Benign Recall: >70% (currently 0%)
- Attack Precision: >85%
- Attack Recall: >85%
- Balanced Accuracy: >80% (currently 50%)

## FILES USED

Training combines all CSV files from:
- Datasets/SQLI-nosqli-XSS/sqli injection dataset/ (3 files)
- Datasets/SQLI-nosqli-XSS/sqli-new/ (3 files)
- Datasets/SQLI-nosqli-XSS/nosqli/ (3 files)

Split: 70% train, 10% val, 20% test (stratified)
