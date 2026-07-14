#!/bin/bash
# Pre-sample DDoS datasets to manageable size

# Samples 5% from each massive CSV file using command-line tools


set -e  # Exit on error


echo "PRE-SAMPLING DDOS DATASETS (5% sample from each file)"


# Source and destination directories

SOURCE_DIR="Datasets/DDoS"
DEST_DIR="Datasets/DDoS_sampled"

# Create destination directory

mkdir -p "$DEST_DIR"
echo " Created directory: $DEST_DIR"


# Get list of CSV files

CSV_FILES=("$SOURCE_DIR"/*.csv)

if [ ${#CSV_FILES[@]} -eq 0 ]; then
    echo " No CSV files found in $SOURCE_DIR"
    exit 1
fi

echo "Found ${#CSV_FILES[@]} CSV files to process"


# Process each file

for file in "${CSV_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        continue
    fi
    
    filename=$(basename "$file")
    output_file="$DEST_DIR/$filename"
    

    echo "Processing: $filename"
    
    # Get total line count (including header)

    echo -n "  Counting lines... "
    total_lines=$(wc -l < "$file")
    echo "$total_lines lines"
    
    # Calculate 5% (excluding header line)

    data_lines=$((total_lines - 1))
    sample_lines=$((data_lines * 5 / 100))
    
    if [ $sample_lines -lt 1000 ]; then
        sample_lines=1000  # Minimum 1000 rows
    fi
    
    echo "  Sampling: $sample_lines rows (5% of $data_lines data rows)"
    echo -n "  Processing... "
    
    # Extract header

    head -n 1 "$file" > "$output_file"
    
    # Sample 5% of data rows (skip header, shuffle, take sample)

    # Using tail to skip header, shuf to randomize, head to take sample

    tail -n +2 "$file" | shuf -n "$sample_lines" --random-source=<(yes 42) >> "$output_file" 2>/dev/null || \
        tail -n +2 "$file" | shuf -n "$sample_lines" >> "$output_file"
    
    # Get output file size

    output_size=$(du -h "$output_file" | cut -f1)
    output_lines=$(wc -l < "$output_file")
    
    echo "DONE"
    echo "   Created: $output_file"
    echo "     Size: $output_size, Lines: $output_lines"

done


echo " PRE-SAMPLING COMPLETE!"


echo "Summary:"
echo "  Source: $SOURCE_DIR (multi-GB files)"
echo "  Output: $DEST_DIR (5% sampled files)"

echo "Next step: Train DDoS model using sampled data"
echo "  Command: cd ml_pipeline && python train_ddos.py"
