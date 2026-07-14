"""
Feature Engineering Module for Web Attack Detection
Extracts meaningful features from SQL/NoSQL injection text
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List

class WebAttackFeatureExtractor:
    """Extract features from SQL/NoSQL injection strings"""
    
    def __init__(self):
        # SQL keywords to detect

        self.sql_keywords = [
            'select', 'union', 'insert', 'update', 'delete', 'drop',
            'exec', 'execute', 'waitfor', 'declare', 'alter', 'create',
            'grant', 'revoke', 'truncate', 'merge', 'into', 'from',
            'where', 'having', 'group', 'order', 'limit', 'offset'
        ]
        
        # NoSQL keywords

        self.nosql_keywords = [
            '$where', '$ne', '$gt', '$lt', '$regex', '$nin', '$in',
            'find', 'aggregate', 'mapreduce', '$expr', '$jsonSchema'
        ]
        
        # Dangerous functions

        self.dangerous_functions = [
            'xp_cmdshell', 'sp_executesql', 'eval', 'exec', 'system',
            'load_file', 'into outfile', 'dumpfile', 'benchmark'
        ]
        
    def extract_features(self, text: str) -> Dict[str, float]:
        """Extract all features from a single text sample"""
        text_str = str(text).lower()
        features = {}
        
        # 1. SQL Keyword Features (13 features)

        for keyword in self.sql_keywords[:13]:  # Top 13 most important
            features[f'has_{keyword}'] = float(keyword in text_str)
        
        # 2. NoSQL Keyword Features (5 features)

        for keyword in self.nosql_keywords[:5]:
            features[f'has_nosql_{keyword.replace("$", "")}'] = float(keyword in text_str)
        
        # 3. Dangerous Function Features (3 features)

        for func in self.dangerous_functions[:3]:
            features[f'has_{func.replace("_", "")}'] = float(func in text_str)
        
        # 4. Special Character Features (8 features)

        features['single_quote_count'] = text_str.count("'") / max(len(text_str), 1)
        features['double_quote_count'] = text_str.count('"') / max(len(text_str), 1)
        features['semicolon_count'] = text_str.count(';') / max(len(text_str), 1)
        features['comment_count'] = (text_str.count('--') + text_str.count('/*')) / max(len(text_str), 1)
        features['equals_count'] = text_str.count('=') / max(len(text_str), 1)
        features['parenthesis_count'] = (text_str.count('(') + text_str.count(')')) / max(len(text_str), 1)
        features['bracket_count'] = (text_str.count('[') + text_str.count(']')) / max(len(text_str), 1)
        features['underscore_count'] = text_str.count('_') / max(len(text_str), 1)
        
        # 5. Logical Operator Features (3 features)

        features['or_count'] = text_str.count(' or ') + text_str.count('||')
        features['and_count'] = text_str.count(' and ') + text_str.count('&&')
        features['not_count'] = text_str.count(' not ') + text_str.count('!')
        
        # 6. Length Features (3 features)

        features['text_length'] = len(text_str)
        features['word_count'] = len(text_str.split())
        features['avg_word_length'] = features['text_length'] / max(features['word_count'], 1)
        
        # 7. Pattern Detection Features (8 features)

        features['has_1_equals_1'] = float(bool(re.search(r'1\s*=\s*1', text_str)))
        features['has_true_condition'] = float(bool(re.search(r"'1'\s*=\s*'1'|\"1\"\s*=\s*\"1\"", text_str)))
        features['has_sleep_delay'] = float('sleep' in text_str or 'waitfor' in text_str or 'benchmark' in text_str)
        features['has_concat'] = float('concat' in text_str or '||' in text_str)
        features['has_comment_injection'] = float('--' in text_str or '/*' in text_str or '*/' in text_str)
        features['has_hex_encoding'] = float(bool(re.search(r'0x[0-9a-f]+', text_str)))
        features['has_unicode_escape'] = float('\\u' in text_str or '\\x' in text_str)
        features['has_url_encoding'] = float('%' in text_str and bool(re.search(r'%[0-9a-f]{2}', text_str)))
        
        # 8. SQL Injection Specific Patterns (5 features)

        features['has_union_select'] = float('union' in text_str and 'select' in text_str)
        features['has_order_by'] = float('order' in text_str and 'by' in text_str)
        features['has_information_schema'] = float('information_schema' in text_str)
        features['has_into_outfile'] = float('into' in text_str and 'outfile' in text_str)
        features['has_load_file'] = float('load_file' in text_str)
        
        # 9. Character Diversity Features (2 features)

        unique_chars = len(set(text_str))
        features['char_diversity'] = unique_chars / max(len(text_str), 1)
        features['has_special_chars'] = float(bool(re.search(r'[^a-zA-Z0-9\s]', text_str)))
        
        # 10. Numeric Features (2 features)

        numbers = re.findall(r'\d+', text_str)
        features['number_count'] = len(numbers)
        features['has_large_numbers'] = float(any(int(n) > 1000 for n in numbers if n.isdigit()))
        
        return features
    
    def extract_features_batch(self, texts: pd.Series) -> pd.DataFrame:
        """Extract features from a batch of texts"""
        print(f"\n Extracting features from {len(texts):,} samples...")
        
        features_list = []
        for idx, text in enumerate(texts):
            if idx % 10000 == 0 and idx > 0:
                print(f"   Processed {idx:,} / {len(texts):,} samples...")
            features_list.append(self.extract_features(text))
        
        features_df = pd.DataFrame(features_list)
        print(f" Extracted {len(features_df.columns)} features!")
        print(f"   Feature names: {list(features_df.columns)[:10]}... (showing first 10)")
        
        return features_df

# Test the extractor

if __name__ == "__main__":
    extractor = WebAttackFeatureExtractor()
    
    # Test samples

    test_samples = [
        "SELECT * FROM users WHERE id = 1",  # Benign
        "' OR '1'='1' --",  # SQLi
        "admin' --",  # SQLi
        "{\"$where\": \"function() { return true; }\"}",  # NoSQLi
        "SELECT name FROM products",  # Benign
    ]
    
    print("Testing Feature Extractor:")
    
    for sample in test_samples:
        features = extractor.extract_features(sample)
        non_zero = {k: v for k, v in features.items() if v > 0}
        print(f"\nText: {sample[:50]}...")
        print(f"Non-zero features ({len(non_zero)}): {list(non_zero.keys())[:10]}")
