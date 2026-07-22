# Integrating an AI agent with sam-canvas

sam-canvas is agent-agnostic. Anything that can run a shell command and write a JSON file can
answer on the canvas — Claude Code, Cursor, Aider, a plain script, etc. This is the contract.

## The loop

```
Human draws in the browser ──autosave──▶ canvas.excalidraw
                                              │ (structured JSON: exact shapes + text)
                        Agent reads it (canvas.py summary  or  GET /canvas)
                                              │  + whatever context the agent has (repo, chat, docs)
                        Agent designs a diagram answer as Excalidraw elements → response.json
                                              │
                        canvas.py merge response.json   (writes ada-* elements)
                                              │
        the browser polls every ~1s and shows the answer live — no reload
```

## The contract (3 steps)

1. **Read the sketch.**
   ```bash
   python3 canvas.py summary        # element types, every text label, bounding box
   ```
   Or `GET http://localhost:3899/canvas` for the raw JSON. If the sketch is freehand with no
   text, render it and look at the image:
   ```bash
   python3 canvas.py preview --no-open   # writes canvas-preview.png
   ```

2. **Author the answer** as a JSON array of Excalidraw elements at natural coordinates near
   `(0,0)`, saved to `response.json` (a bare `[...]` array, or `{"elements":[...]}`). You only
   provide the shapes you care about — `merge` fills in every other required field.

3. **Merge it.**
   ```bash
   python3 canvas.py merge response.json
   ```
   `merge` offsets your answer to the right of the human's sketch, tags every element with an
   `ada-` id prefix, and **replaces any previous agent answer**. It never touches the human's
   elements. The live page shows it within ~1s.

## Ownership split (why it is race-safe)

The human and the agent own different halves of the same file:

- The **browser** only ever writes non-`ada-` elements (the human's).
- The **agent** (`canvas.py merge`) only ever writes `ada-*` elements.
- The file on disk is always the union of both.

So both sides can write concurrently without clobbering each other — like two people writing in
different-coloured pens on one sheet.

## Element format (the subset you author)

Every element needs `type`, `x`, `y`, `width`, `height`. `merge` supplies sensible defaults for
everything else, so a minimal element is enough.

```jsonc
// rectangle (card / box)
{ "type": "rectangle", "x": 0, "y": 0, "width": 240, "height": 60,
  "backgroundColor": "#e7f5ff", "strokeColor": "#1971c2", "roundness": { "type": 3 } }

// text (label). Use \n for line breaks. fontFamily: 1=hand-drawn, 2=normal, 3=code
{ "type": "text", "x": 16, "y": 18, "width": 220, "height": 24,
  "text": "1 · do the thing", "fontSize": 16, "fontFamily": 2, "strokeColor": "#1971c2" }

// arrow (points are [dx,dy] offsets from x,y; endArrowhead defaults to "arrow")
{ "type": "arrow", "x": 120, "y": 60, "width": 0, "height": 30, "points": [[0,0],[0,30]] }

// also: "ellipse", "diamond", "line" (same shape as arrow, no arrowhead)
```

Suggested palette (Excalidraw's own): blue `#1971c2` on `#e7f5ff`, green `#2f9e44` on `#d3f9d8`,
red `#e03131` on `#ffe3e3`, violet `#6741d9` on `#f3f0ff`, yellow `#f08c00` on `#fff9db`,
ink `#1e1e1e`. Leave `backgroundColor` off (defaults to transparent) for outline-only shapes.

## Tips

- Keep the answer to the point — a few boxes and arrows beat a wall of text.
- `python3 canvas.py preview` then look at `canvas-preview.png` to self-check before telling the
  human it is done.
- The whole value of this over a context-free whiteboard is that YOUR agent has context. Read the
  repo / conversation / docs and make the answer specific, not generic.
- To wipe the canvas: `python3 canvas.py init` (after stopping the server or removing the file).

A ready-made drop-in for Claude Code lives in [`../claude/`](../claude) — a skill plus a
`/sam-canvas` command.
