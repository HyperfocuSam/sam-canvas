#!/usr/bin/env bash
# Start the sam-canvas bridge and open the canvas in your browser.
# Idempotent: reuses the running server if the port is already up.
set -uo pipefail

PORT="${SAM_CANVAS_PORT:-3899}"
DIR="$(cd "$(dirname "$0")" && pwd)"
export SAM_CANVAS_FILE="${SAM_CANVAS_FILE:-$DIR/canvas.excalidraw}"
export SAM_CANVAS_PORT="$PORT"

if ! curl -s -o /dev/null "http://localhost:$PORT/canvas" 2>/dev/null; then
  nohup python3 "$DIR/server.py" > "$DIR/.serve.log" 2>&1 &
  sleep 2
fi

if curl -s -o /dev/null "http://localhost:$PORT/canvas" 2>/dev/null; then
  URL="http://localhost:$PORT"
  echo "sam-canvas live → $URL"
  echo "canvas file: $SAM_CANVAS_FILE"
  # open in the default browser (macOS: open, Linux: xdg-open)
  (open "$URL" 2>/dev/null || xdg-open "$URL" 2>/dev/null) || echo "Open $URL in your browser."
else
  echo "ERROR: server did not start; see $DIR/.serve.log"
  exit 1
fi
