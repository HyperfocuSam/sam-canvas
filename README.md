# sam-canvas

**A live drawing canvas for people who live in an AI coding agent's terminal.**

You sketch on an Excalidraw canvas in your browser; your agent — Claude Code, or any tool that can
run a shell command — reads your sketch *with full context of your project* and draws a diagram
answer back onto the same canvas, live.

English · [简体中文](README.zh-Hans.md) · [繁體中文](README.zh-Hant.md) · MIT License

![sam-canvas example: a rough sketch on the left, the agent's diagram answer on the right](examples/auth-flow.png)

*Left: a rough sketch. Right: the agent read it and drew an answer onto the same canvas, in blue.*

## Why I made this

I have ADHD and I think visually, but I live in the Claude Code terminal all day — and nothing let me
sketch an idea and have *my* agent answer it on a canvas. So I built this for myself and I'm sharing
it as a skill in case you're the same kind of person.

It is deliberately small. The whiteboard part isn't new — Excalidraw already does AI text-to-diagram.
The one thing here that nothing else does for a terminal user: **the AI that answers is your own
agent, the one that already knows your codebase and your conversation** — not a context-blind model
that only sees the drawing.

This is a personal tool shared openly, not a product. No roadmap, no signups. Fork it, bend it, keep it.

## Use it with Claude Code (the main way)

```bash
git clone https://github.com/HyperfocuSam/sam-canvas.git
export SAM_CANVAS_HOME="$PWD/sam-canvas"
# copy the drop-in into your Claude Code config:
cp -r sam-canvas/claude/skills/sam-canvas   ~/.claude/skills/
cp    sam-canvas/claude/commands/sam-canvas.md ~/.claude/commands/
```

Then, in Claude Code:

1. Type **`/sam-canvas`** → a dedicated canvas window opens (docked to the right of your screen).
2. **Draw something.** Boxes and labels read best; you can also write your request *on the canvas*.
3. Nudge the agent — even one word ("look", "go", "?") — and it reads your sketch, understands it
   against your repo, and draws the answer on the same canvas within ~1s. A **Collapse** button folds
   it away when you're done.

## Use it with any agent

No Claude Code required — the integration is three shell steps (read, author JSON, merge). See
[`docs/for-agents.md`](docs/for-agents.md) for the full contract and the Excalidraw element format.

```bash
./start.sh                                # open the canvas
python3 canvas.py summary                 # your agent reads the current sketch
# ...agent authors an answer as Excalidraw elements → response.json...
python3 canvas.py merge response.json     # appears on the live canvas within ~1s
```

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
- **Your canvas file persists** across sessions — it is an external brain you can leave and come back to.
- **Loopback only.** The server binds `127.0.0.1`; nothing is exposed to the network.

## Honest limits

- **You have to nudge it.** The agent doesn't watch the canvas — you poke it each turn. That is the
  price of keeping *your* context: the answer comes from your live agent session, so it can't run
  fully on its own without becoming context-blind. A one-word nudge is the intended cost.
- **Structured beats freehand.** It reads shapes and text exactly; pure scribbles it has to render
  and squint at. Draw boxes and labels for the best results.
- **Excalidraw loads from a CDN**, so the first load needs internet.

## Requirements

- **Python 3.8+** (standard library only — nothing to `pip install`)
- A modern **browser** (Chrome/Chromium gets a dedicated docked window; others open a normal tab)
- An **AI coding agent** that can run shell commands (e.g. Claude Code)
- Optional: `rsvg-convert` (from `librsvg`) for PNG previews; SVG previews work without it

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `SAM_CANVAS_PORT` | `3899` | Port the server listens on |
| `SAM_CANVAS_FILE` | `./canvas.excalidraw` | Path to the shared canvas file |

Stop the server: `kill $(lsof -tiTCP:3899 -sTCP:LISTEN)`. Blank the canvas: `python3 canvas.py init`.

## Credits & license

Built on [Excalidraw](https://github.com/excalidraw/excalidraw) (MIT). Released under the
[MIT License](LICENSE). Made by [Sam Wong](https://github.com/HyperfocuSam).
