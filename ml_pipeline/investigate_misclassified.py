"""
Data Quality Investigation - Analyze Misclassified Samples
Extract and analyze the ~4000 attacks that are consistently misclassified as benign
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
import tensorflow as tf
from collections import Counter
import re

sys.path.append(str(Path(__file__).parent))
from feature_engineering import WebAttackFeatureExtractor

def load_data():
    """Load and prepare test data"""
    print("LOADING TEST DATA")
    
    base_path = Path(__file__).parent.parent / "Datasets" / "SQLI-nosqli-XSS"
    all_csv_files = list(base_path.rglob("*.csv"))
    
    all_df = []
    for csv_file in all_csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            df = df.drop_duplicates().dropna(how='all').dropna(axis=1, how='all')
            all_df.append(df)
        except:
            continue
    
    combined_df = pd.concat(all_df, ignore_index=True).drop_duplicates()
    
    # Get columns

    label_col = [col for col in combined_df.columns if 'label' in col.lower()][0]
    text_col = [col for col in ['Sentence', 'Query'] if col in combined_df.columns][0]
    
    # Normalize labels

    unique_labels = combined_df[label_col].unique()
    label_set = set([str(v).strip() for v in unique_labels if pd.notna(v)])
    
    if label_set <= {'0', '1'}:
        y = combined_df[label_col].fillna('1').astype(str).str.strip().astype(int)
    else:
        y = (combined_df[label_col] != unique_labels[0]).astype(int)
    
    text_data = combined_df[text_col].fillna('').astype(str)
    
    print(f" Loaded {len(text_data):,} samples")
    print(f"   Benign: {(y==0).sum():,} ({(y==0).sum()/len(y)*100:.1f}%)")
    print(f"   Attack: {(y==1).sum():,} ({(y==1).sum()/len(y)*100:.1f}%)")
    
    return text_data, y

def extract_features(texts, extractor):
    """Extract features from texts"""
    print("\n Extracting features...")
    features_list = []
    for idx, text in enumerate(texts):
        if idx % 10000 == 0 and idx > 0:
            print(f"   Processed {idx:,} / {len(texts):,}...")
        features_list.append(extractor.extract_features(text))
    
    features_df = pd.DataFrame(features_list)
    print(f" Extracted {len(features_df.columns)} features")
    return features_df

def analyze_misclassified(texts, true_labels, predictions, threshold=0.5):
    """Analyze misclassified samples"""
    print("ANALYZING MISCLASSIFIED SAMPLES")
    
    # Get predictions

    pred_labels = (predictions >= threshold).astype(int)
    
    # False positives: Attacks (label=1) predicted as benign (pred=0)

    false_positives = (true_labels == 1) & (pred_labels == 0)
    fp_indices = np.where(false_positives)[0]
    
    # False negatives: Benign (label=0) predicted as attack (pred=1)

    false_negatives = (true_labels == 0) & (pred_labels == 1)
    fn_indices = np.where(false_negatives)[0]
    
    print(f"\n Misclassification Summary:")
    print(f"   False Positives (attacks → benign): {len(fp_indices):,}")
    print(f"   False Negatives (benign → attack): {len(fn_indices):,}")
    print(f"   Total Misclassified: {len(fp_indices) + len(fn_indices):,}")
    
    # Analyze false positives (the problematic ones)

    print(f"\n" + "="*100)
    print(f"FALSE POSITIVES ANALYSIS ({len(fp_indices):,} samples)")
    
    fp_texts = texts.iloc[fp_indices].values
    fp_confidences = predictions[fp_indices]
    
    # Sort by confidence (how confident model was they were benign)

    sorted_indices = np.argsort(fp_confidences)  # Low confidence = very confident it's benign
    
    print(f"\n Sample Analysis (showing 50 examples):")
    print("-" * 100)
    
    sample_data = []
    for i in range(min(50, len(sorted_indices))):
        idx = sorted_indices[i]
        text = fp_texts[idx]
        conf = fp_confidences[idx]
        
        sample_data.append({
            'index': fp_indices[idx],
            'text': text,
            'confidence': conf,
            'length': len(text)
        })
        
        print(f"\n{i+1}. Confidence: {conf:.4f} (Model thought this was BENIGN)")
        print(f"   Text: {text[:200]}{'...' if len(text) > 200 else ''}")
    
    # Create DataFrame for further analysis

    fp_df = pd.DataFrame({
        'index': fp_indices,
        'text': fp_texts,
        'confidence': fp_confidences
    })
    
    return fp_df, fn_indices, sample_data

def detect_patterns(texts):
    """Detect common patterns in misclassified samples"""
    print("PATTERN DETECTION")
    
    patterns = {
        'Single quotes': 0,
        'Double quotes': 0,
        'Comments (-- or #)': 0,
        'OR keyword': 0,
        'AND keyword': 0,
        'UNION': 0,
        'SELECT': 0,
        'Semicolon': 0,
        'Equals sign': 0,
        '1=1 pattern': 0,
        'No special chars': 0,
        'Very short (<10 chars)': 0,
        'Very long (>200 chars)': 0,
        'Contains numbers only': 0,
        'Empty or whitespace': 0,
    }
    
    for text in texts:
        text_upper = text.upper()
        
        if "'" in text:
            patterns['Single quotes'] += 1
        if '"' in text:
            patterns['Double quotes'] += 1
        if '--' in text or '#' in text:
            patterns['Comments (-- or #)'] += 1
        if re.search(r'\bOR\b', text_upper):
            patterns['OR keyword'] += 1
        if re.search(r'\bAND\b', text_upper):
            patterns['AND keyword'] += 1
        if 'UNION' in text_upper:
            patterns['UNION'] += 1
        if 'SELECT' in text_upper:
            patterns['SELECT'] += 1
        if ';' in text:
            patterns['Semicolon'] += 1
        if '=' in text:
            patterns['Equals sign'] += 1
        if '1=1' in text or "1='1" in text:
            patterns['1=1 pattern'] += 1
        
        # Special cases

        if not re.search(r'[^\w\s]', text):
            patterns['No special chars'] += 1
        if len(text) < 10:
            patterns['Very short (<10 chars)'] += 1
        if len(text) > 200:
            patterns['Very long (>200 chars)'] += 1
        if text.strip().replace(' ', '').isdigit():
            patterns['Contains numbers only'] += 1
        if len(text.strip()) == 0:
            patterns['Empty or whitespace'] += 1
    
    print(f"\n Pattern Distribution ({len(texts):,} samples):")
    for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
        pct = count / len(texts) * 100
        print(f"   {pattern:30s}: {count:5,} ({pct:5.1f}%)")
    
    return patterns

def identify_suspicious_samples(fp_df):
    """Identify potentially mislabeled samples"""
    print("IDENTIFYING POTENTIALLY MISLABELED SAMPLES")
    
    suspicious = []
    
    # Very low confidence (model VERY sure they're benign)

    very_low_conf = fp_df[fp_df['confidence'] < 0.1]
    print(f"\n Very low confidence (<0.1): {len(very_low_conf):,} samples")
    print("   These might be truly benign but mislabeled as attacks in dataset")
    
    if len(very_low_conf) > 0:
        print("\n   Top 20 examples:")
        for i, row in very_low_conf.head(20).iterrows():
            print(f"   {row['confidence']:.4f} | {row['text'][:150]}")
            suspicious.append({
                'reason': 'Very low confidence (<0.1)',
                'confidence': row['confidence'],
                'text': row['text']
            })
    
    # No malicious patterns

    print(f"\n Checking for samples with NO malicious indicators...")
    no_malicious = []
    
    malicious_keywords = [
        'select', 'union', 'insert', 'update', 'delete', 'drop',
        'exec', 'execute', '--', '#', ';', '1=1', 'or 1', 'and 1',
        '$where', '$ne', 'script', 'alert', 'onerror', 'onload'
    ]
    
    for idx, row in fp_df.iterrows():
        text_lower = row['text'].lower()
        has_malicious = any(keyword in text_lower for keyword in malicious_keywords)
        
        if not has_malicious:
            no_malicious.append(row)
    
    print(f"   Found {len(no_malicious):,} samples with NO malicious keywords")
    
    if len(no_malicious) > 0:
        print("\n   Examples:")
        for i, sample in enumerate(no_malicious[:20]):
            print(f"   {sample['confidence']:.4f} | {sample['text'][:150]}")
    
    return suspicious, very_low_conf, no_malicious

def save_for_manual_review(fp_df, output_file='data_quality/misclassified_samples.csv'):
    """Save misclassified samples for manual review"""
    print("SAVING FOR MANUAL REVIEW")
    
    Path('data_quality').mkdir(exist_ok=True)
    
    # Sort by confidence (lowest first = most likely mislabeled)

    fp_df_sorted = fp_df.sort_values('confidence')
    
    # Save full list

    fp_df_sorted.to_csv(output_file, index=False)
    print(f"\n Saved {len(fp_df):,} samples to: {output_file}")
    
    # Save top 500 most suspicious

    top_500 = fp_df_sorted.head(500)
    top_500.to_csv('data_quality/top_500_suspicious.csv', index=False)
    print(f" Saved top 500 most suspicious to: data_quality/top_500_suspicious.csv")
    
    # Save samples with confidence < 0.2

    very_suspicious = fp_df_sorted[fp_df_sorted['confidence'] < 0.2]
    very_suspicious.to_csv('data_quality/very_suspicious_low_confidence.csv', index=False)
    print(f" Saved {len(very_suspicious):,} very suspicious (conf < 0.2) to: data_quality/very_suspicious_low_confidence.csv")

def main():
    print("DATA QUALITY INVESTIGATION - MISCLASSIFIED SAMPLES ANALYSIS")
    
    # Load model

    print("\n Loading model...")
    model = tf.keras.models.load_model('models/web_attack_detector_v2.keras')
    extractor = WebAttackFeatureExtractor()
    print(" Model loaded")
    
    # Load data

    texts, labels = load_data()
    
    # Use test split (same as training)

    from sklearn.model_selection import train_test_split
    _, texts_test, _, labels_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )
    
    print(f"\n Using test set: {len(texts_test):,} samples")
    
    # Extract features

    features = extract_features(texts_test.reset_index(drop=True), extractor)
    
    # Predict

    print("\n Generating predictions...")
    predictions = model.predict(features.values, verbose=0).flatten()
    print(" Predictions complete")
    
    # Analyze misclassified

    fp_df, fn_indices, sample_data = analyze_misclassified(
        texts_test.reset_index(drop=True), 
        labels_test.values, 
        predictions
    )
    
    # Detect patterns in false positives

    print("ANALYZING FALSE POSITIVE PATTERNS")
    detect_patterns(fp_df['text'].values)
    
    # Identify suspicious samples

    suspicious, very_low_conf, no_malicious = identify_suspicious_samples(fp_df)
    
    # Save for manual review

    save_for_manual_review(fp_df)
    
    # Summary

    print("INVESTIGATION SUMMARY")
    print(f"\n Key Findings:")
    print(f"   Total False Positives: {len(fp_df):,}")
    print(f"   Very Low Confidence (<0.1): {len(very_low_conf):,}")
    print(f"   No Malicious Patterns: {len(no_malicious):,}")
    print(f"\n Recommendation:")
    
    if len(very_low_conf) > 100:
        print(f"     {len(very_low_conf):,} samples have very low confidence (<0.1)")
        print(f"   These are likely MISLABELED in the dataset (should be benign)")
        print(f"   Removing them could improve benign precision significantly!")
    
    print(f"\n Files created:")
    print(f"   - data_quality/misclassified_samples.csv ({len(fp_df):,} samples)")
    print(f"   - data_quality/top_500_suspicious.csv (500 most suspicious)")
    print(f"   - data_quality/very_suspicious_low_confidence.csv ({len(very_low_conf):,} samples)")
    
    print(f"\n Next Steps:")
    print(f"   1. Review data_quality/very_suspicious_low_confidence.csv")
    print(f"   2. Manually verify if these are truly attacks or mislabeled")
    print(f"   3. If mislabeled, remove or relabel them")
    print(f"   4. Retrain model on cleaned dataset")
    
    print(" INVESTIGATION COMPLETE")

if __name__ == "__main__":
    main()
