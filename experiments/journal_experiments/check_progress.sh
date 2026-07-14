#!/bin/bash
# Quick script to check experiment progress

echo "=================================="
echo "EXPERIMENT PROGRESS CHECK"
echo "=================================="
echo ""

# Check if master process is running
if pgrep -f "run_all_experiments.py" > /dev/null; then
    echo "✓ Experiments are running"
    echo ""
else
    echo "✗ Experiments not running"
    echo ""
    exit 1
fi

# Count completed experiments
completed=$(find . -name "*_results.json" -path "*/results/*" 2>/dev/null | wc -l)
total=9

echo "Completed: $completed / $total experiments"
echo ""

# Show which experiments are done
echo "Completed Experiments:"
for dir in 0*/; do
    exp_name=$(basename "$dir")
    if [ -f "$dir/results/"*"_results.json" ]; then
        echo "  ✓ $exp_name"
    else
        echo "  ⏳ $exp_name"
    fi
done

echo ""
echo "Latest results:"
ls -lht */results/*.json 2>/dev/null | head -5

echo ""
echo "To view live output:"
echo "  tail -f results/experiment_run_*.json"
echo ""
echo "To stop experiments:"
echo "  pkill -f run_all_experiments.py"
