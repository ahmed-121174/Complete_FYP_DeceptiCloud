"""
Dataset Analysis Script
Analyzes all DDoS and Web Attack datasets to understand structure, quality, and preprocessing needs
"""

import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
import json

class DatasetAnalyzer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.ddos_path = self.base_path / "DDoS"
        self.web_attack_path = self.base_path / "SQLI-nosqli-XSS"
        
    def analyze_csv(self, filepath):
        """Analyze a single CSV file"""
        print(f"\n{'='*80}")
        print(f"Analyzing: {filepath.name}")
        print(f"{'='*80}")
        
        try:
            # Read the CSV

            df = pd.read_csv(filepath)
            
            analysis = {
                'filename': filepath.name,
                'shape': df.shape,
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'duplicate_rows': df.duplicated().sum(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2,
            }
            
            # Print summary

            print(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
            print(f"Memory Usage: {analysis['memory_usage_mb']:.2f} MB")
            print(f"\nColumns: {', '.join(df.columns.tolist())}")
            
            # Null values

            null_cols = {k: v for k, v in analysis['null_counts'].items() if v > 0}
            if null_cols:
                print(f"\nNull Values:")
                for col, count in null_cols.items():
                    print(f"  - {col}: {count:,} ({count/len(df)*100:.2f}%)")
            else:
                print("\nNo null values found ")
            
            # Duplicates

            if analysis['duplicate_rows'] > 0:
                print(f"\nDuplicate Rows: {analysis['duplicate_rows']:,} ({analysis['duplicate_rows']/len(df)*100:.2f}%)")
            else:
                print("\nNo duplicate rows ")
            
            # Sample data

            print(f"\nFirst 3 rows:")
            print(df.head(3).to_string())
            
            # Data types

            print(f"\nData Types:")
            for col, dtype in df.dtypes.items():
                print(f"  - {col}: {dtype}")
            
            # Basic statistics for numeric columns

            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                print(f"\nNumeric Column Statistics:")
                print(df[numeric_cols].describe().to_string())
            
            # Check for label column

            label_candidates = ['label', 'Label', 'target', 'class', 'attack', 'malicious']
            label_col = None
            for candidate in label_candidates:
                if candidate in df.columns:
                    label_col = candidate
                    break
            
            if label_col:
                print(f"\nLabel Column: '{label_col}'")
                print(f"Unique Values: {df[label_col].unique()}")
                print(f"Value Counts:")
                print(df[label_col].value_counts().to_string())
            else:
                print("\nNo standard label column found - need to investigate")
            
            return analysis
            
        except Exception as e:
            print(f"ERROR analyzing {filepath.name}: {str(e)}")
            return None
    
    def analyze_ddos_datasets(self):
        """Analyze all DDoS datasets"""
        print("DDOS DATASETS ANALYSIS")
        
        ddos_files = sorted(self.ddos_path.glob("*.csv"))
        print(f"\nFound {len(ddos_files)} DDoS dataset files")
        
        all_analyses = []
        for filepath in ddos_files:
            analysis = self.analyze_csv(filepath)
            if analysis:
                all_analyses.append(analysis)
        
        return all_analyses
    
    def analyze_web_attack_datasets(self):
        """Analyze all Web Attack datasets"""
        print("WEB ATTACK DATASETS ANALYSIS")
        
        web_files = sorted(self.web_attack_path.rglob("*.csv"))
        print(f"\nFound {len(web_files)} Web Attack dataset files")
        
        all_analyses = []
        for filepath in web_files:
            analysis = self.analyze_csv(filepath)
            if analysis:
                all_analyses.append(analysis)
        
        return all_analyses
    
    def generate_report(self, ddos_analyses, web_analyses):
        """Generate comprehensive analysis report"""
        print("SUMMARY REPORT")
        
        print(f"\n DDoS Datasets: {len(ddos_analyses)} files")
        total_ddos_rows = sum(a['shape'][0] for a in ddos_analyses)
        print(f"   Total rows: {total_ddos_rows:,}")
        
        print(f"\n Web Attack Datasets: {len(web_analyses)} files")
        total_web_rows = sum(a['shape'][0] for a in web_analyses)
        print(f"   Total rows: {total_web_rows:,}")
        
        # Save report to JSON

        report = {
            'ddos_datasets': ddos_analyses,
            'web_attack_datasets': web_analyses,
            'summary': {
                'total_ddos_files': len(ddos_analyses),
                'total_ddos_rows': total_ddos_rows,
                'total_web_files': len(web_analyses),
                'total_web_rows': total_web_rows
            }
        }
        
        report_path = self.base_path.parent / 'dataset_analysis_report.json'
        with open(report_path, 'w') as f:
            # Convert non-serializable types

            def convert_types(obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif pd.api.types.is_dtype_equal(obj, 'object'):
                    return str(obj)
                return str(obj)
            
            json.dump(report, f, indent=2, default=convert_types)
        
        print(f"\n Report saved to: {report_path}")
        
        return report

def main():
    base_path = "/home/irtaza-butt/Desktop/Ahmed Fype-II/Datasets"
    
    analyzer = DatasetAnalyzer(base_path)
    
    # Analyze DDoS datasets

    ddos_analyses = analyzer.analyze_ddos_datasets()
    
    # Analyze Web Attack datasets

    web_analyses = analyzer.analyze_web_attack_datasets()
    
    # Generate report

    analyzer.generate_report(ddos_analyses, web_analyses)
    
    print("\n Dataset analysis complete!")

if __name__ == "__main__":
    main()
