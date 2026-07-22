# sam-canvas

**A live shared drawing canvas for you and your AI coding agent.**

You sketch on an infinite Excalidraw canvas in your browser. Your agent — Claude Code, or any tool
that can run a shell command — reads your sketch *with full context of your project* and draws a
diagram answer back onto the same canvas, live. No copy-pasting screenshots into a chat box.

English · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · MIT License

![sam-canvas example: a rough sketch on the left, the agent's diagram answer on the right](examples/auth-flow.png)

*Left: a rough sketch. Right: the agent read it and drew an answer onto the same canvas, in blue.*

## Why

Chat-based AI makes you translate a spatial idea into words. Standalone AI whiteboards can draw, but
their model only sees the canvas — it knows nothing about your codebase or your conversation.

sam-canvas keeps the drawing **and** wires it to *your* agent, the one that already has context. You
think on the canvas; it answers on the canvas, and it actually knows what you are working on.

## Requirements

- **Python 3.8+** (standard library only — nothing to `pip install`)
- A modern **browser** (Excalidraw loads from a CDN, so you need internet the first time)
- An **AI coding agent** that can run shell commands (e.g. Claude Code). Optional but that is the point.
- Optional: `rsvg-convert` (from `librsvg`) for PNG previews; SVG previews work without it.

## Quick start

```bash
git clone https://github.com/HyperfocuSam/sam-canvas.git
cd sam-canvas
./start.sh            # starts the local server (port 3899) and opens the canvas
```

Draw something. Then ask your agent to answer it (see below). Your drawing autosaves as you go, so
the agent can read it at any time — there is no "export the file" step.

## How it works

```
You draw in the browser ──autosave──▶ canvas.excalidraw
                                           │  (structured JSON: exact shapes + text)
                     Your agent reads it + your project context
                                           │
                     Agent designs a diagram answer → response.json
                                           │
                     canvas.py merge  ──▶  ada-* elements added to the same file
                                           │
        the page polls every ~1s and shows the answer live — no reload
```

- **Race-safe by design.** You and the agent own different halves of the file: the browser only
  writes your elements, the agent only writes `ada-*` elements. Your work is never overwritten.
- **Collapse.** A button in the top bar folds the whole canvas into a small corner pill and back.
- **Loopback only.** The server binds `127.0.0.1` — nothing is exposed to the network.

## Use it with Claude Code

A ready-made skill and `/sam-canvas` command live in [`claude/`](claude). Point Claude Code at this
checkout (`export SAM_CANVAS_HOME=/path/to/sam-canvas`) and copy `claude/skills/sam-canvas` and
`claude/commands/sam-canvas.md` into your `.claude/` folder. Then:

1. Type `/sam-canvas` → the canvas opens.
2. Draw, then say "look" or `/sam-canvas turn this into an architecture diagram`.
3. Claude reads your sketch, understands it against your repo, and draws the answer on the canvas.

## Use it with any agent

The integration is three shell steps — read, author JSON, merge. See
[`docs/for-agents.md`](docs/for-agents.md) for the full contract and the Excalidraw element format.

```bash
python3 canvas.py summary                 # read the current sketch (types, text, bounding box)
# ...your agent designs an answer as Excalidraw elements → response.json...
python3 canvas.py merge response.json     # appears on the live canvas within ~1s
python3 canvas.py preview                 # optional: render canvas-preview.png to double-check
```

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `SAM_CANVAS_PORT` | `3899` | Port the server listens on |
| `SAM_CANVAS_FILE` | `./canvas.excalidraw` | Path to the shared canvas file |

Stop the server: `kill $(lsof -tiTCP:3899 -sTCP:LISTEN)`. Blank the canvas: `python3 canvas.py init`.

## Credits & license

Built on [Excalidraw](https://github.com/excalidraw/excalidraw) (MIT). sam-canvas is released under
the [MIT License](LICENSE).
