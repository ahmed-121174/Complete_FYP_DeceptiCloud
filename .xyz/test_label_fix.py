#!/usr/bin/env python3
"""
Quick test to debug the Label column issue
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'ml_pipeline'))

from preprocessing import DataPreprocessor

# Test with sample data

print("Creating test dataframe...")
test_df = pd.DataFrame({
    'query': ['SELECT * FROM users', 'DELETE FROM cart', 'UPDATE table'],
    'Label': [1, 1, 1]  # All same value (constant)
})

print(f"\nInitial DataFrame:")
print(test_df)
print(f"Columns: {list(test_df.columns)}")

# Create preprocessor

preprocessor = DataPreprocessor()

# Test remove_constant_columns with label protection

label_col = 'Label'
print(f"\nCalling remove_constant_columns with label_col='{label_col}'")
result = preprocessor.remove_constant_columns(test_df, label_col)

print(f"\nAfter remove_constant_columns:")
print(f"Columns: {list(result.columns)}")
print(f"Label column present: {'Label' in result.columns}")

if 'Label' in result.columns:
    print("\n SUCCESS: Label column was protected!")
else:
    print("\n FAIL: Label column was removed!")
