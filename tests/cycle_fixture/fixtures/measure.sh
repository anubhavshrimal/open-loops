#!/bin/sh
# Run command of the fixture Exploration Spec: fib.py must still print the right
# value, then the metric is its count of non-empty lines (lower is better).
out=$(python3 fib.py 20)
if [ "$out" != "6765" ]; then
  echo "lines: FAIL (fib.py 20 printed '$out', want 6765)"
  exit 1
fi
echo "lines: $(grep -c . fib.py)"
