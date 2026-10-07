#!/bin/sh
# Build and test command of the fixture project: every .txt file must be non-empty
# and end with a newline.
status=0
for f in $(git ls-files '*.txt'); do
  if [ ! -s "$f" ] || [ "$(tail -c 1 "$f" | od -An -c | tr -d ' ')" != '\n' ]; then
    echo "FAIL: $f is empty or has no final newline"
    status=1
  fi
done
[ "$status" -eq 0 ] && echo "ok"
exit "$status"
