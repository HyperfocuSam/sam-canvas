---
name: sam-canvas
description: A live shared Excalidraw canvas wired to Claude Code. Opens a real drawing canvas in the browser; the human sketches and Claude reads it (with full project/context) and draws diagram answers onto the same canvas, live. Use when the user types /sam-canvas, or says "open the canvas / whiteboard", "let's draw", "look at my sketch", "answer on the canvas", "turn this into a diagram". Requires a sam-canvas checkout (set SAM_CANVAS_HOME to it, or run from that directory).
---

# sam-canvas — a live canvas you and Claude Code share

`/sam-canvas` opens a browser canvas (real Excalidraw) served by a small local bridge. The human
draws; the scene autosaves to `canvas.excalidraw`. Claude reads it, designs a diagram answer, and
merges it in; the page shows it within ~1s (no reload). Ownership is split so it is race-safe: the
page writes only the human's elements, Claude writes only `ada-*` elements.

Set `SAM_CANVAS_HOME` to the sam-canvas checkout, or run these from that directory.

## When invoked

1. **Open the canvas** (idempotent):
   ```bash
   bash "${SAM_CANVAS_HOME:-.}/start.sh"
   ```
   It prints the URL and opens the browser. Tell the user it is live, they can draw, and the
   **Collapse** button folds the canvas away.

2. **If they have drawn, or ask for a response:**
   ```bash
   python3 "${SAM_CANVAS_HOME:-.}/canvas.py" summary
   ```
   If the summary says "likely freehand" (no text), render and look:
   `python3 "${SAM_CANVAS_HOME:-.}/canvas.py" preview --no-open` then read `canvas-preview.png`.
   - **Interpret it with context** — read the relevant repo files / conversation. A context-free
     answer misses the point of using YOUR agent. Fold in `$ARGUMENTS`.
   - Author the answer as Excalidraw elements (see `docs/for-agents.md` for the format) → write
     `response.json` → merge:
     ```bash
     python3 "${SAM_CANVAS_HOME:-.}/canvas.py" merge response.json
     ```
   - It appears on the live canvas automatically. Tell the user in one line what you drew.

3. If they have not drawn yet: tell them to sketch on the open canvas and ping you ("look" / "respond").

The human's elements are never edited; each merge replaces the previous agent answer. Element
format and the full contract: `docs/for-agents.md`.
