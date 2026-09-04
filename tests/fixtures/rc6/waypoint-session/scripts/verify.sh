#!/bin/sh
set -eu
if [ "${1:-}" = "fast" ]; then
  exit 0
fi
exit 2
