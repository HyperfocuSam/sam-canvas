---
description: Open the live shared drawing canvas (real Excalidraw in the browser); you draw, Claude Code answers with diagrams on the same canvas
argument-hint: [optional — what to do with the sketch, e.g. "turn this into a clean architecture diagram"]
---

The user typed `/sam-canvas`. Open the live shared canvas and be ready to answer on it with diagrams.

Optional steering (may be empty): $ARGUMENTS

Full method: `claude/skills/sam-canvas/SKILL.md`. In short:

1. `bash "${SAM_CANVAS_HOME:-.}/start.sh"` — start the local bridge and open the canvas
   (real Excalidraw + a Collapse button). Tell the user it is live and they can draw.
2. If they have drawn, or ask you to respond:
   `python3 "${SAM_CANVAS_HOME:-.}/canvas.py" summary` to read the sketch (if freehand,
   `... preview --no-open` and read `canvas-preview.png`). Interpret it against the real work
   (repo / conversation), not generically.
3. Author the answer as Excalidraw elements (`docs/for-agents.md`) → `response.json` →
   `python3 "${SAM_CANVAS_HOME:-.}/canvas.py" merge response.json`. It appears live within ~1s.

The user's elements are never touched; your answer replaces any previous agent answer.
