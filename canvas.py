#!/usr/bin/env python3
"""sam-canvas engine — the deterministic half of the human/agent canvas loop.

A human sketches in any Excalidraw app; an AI coding agent (with full project context)
reads the sketch, DESIGNS a diagram answer as Excalidraw elements, and this script does
the fragile mechanical parts reliably: inspect the sketch, merge the answer onto the same
canvas without touching the human's own elements, and render a standalone preview.

Subcommands:
  summary            Print an inventory of the current canvas (element types, texts, bbox).
  merge <resp.json>  Merge the agent's answer elements to the RIGHT of the human's sketch,
                     tagged in blue, replacing any previous agent answer. Never edits human elements.
  preview            Render the canvas to <file>-preview.(svg|png) and open it.
  init               Create a blank canvas file if none exists.

Default canvas file: canvas.excalidraw (override with --file or $SAM_CANVAS_FILE).
The agent authors answer elements at natural coordinates near (0,0); merge handles offset,
recolor, tagging, and de-duplication. Agent elements are marked with id-prefix "ada-".
"""
import argparse
import base64
import html
import json
import math
import mimetypes
import os
import shutil
import subprocess
import sys

ADA_BLUE = "#1971c2"
ADA_PREFIX = "ada-"
GAP = 120  # px gap between the human's sketch and the agent's answer

# Excalidraw fontFamily -> CSS family (1=hand-drawn, 2=normal, 3=code)
FONT_MAP = {1: "Comic Sans MS, Segoe Print, cursive", 2: "Helvetica, Arial, sans-serif",
            3: "Cascadia Code, Consolas, monospace"}
DEFAULT_FILE = os.environ.get("SAM_CANVAS_FILE", "canvas.excalidraw")


def load(path):
    if not os.path.exists(path):
        sys.exit(f"No canvas at {path}. Run `canvas.py init` and draw something first.")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if data.get("type") != "excalidraw":
        sys.exit(f"{path} is not a valid .excalidraw file.")
    data.setdefault("elements", [])
    return data


def save(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_ada(el):
    return str(el.get("id", "")).startswith(ADA_PREFIX)


def bbox(elements):
    xs, ys, xe, ye = [], [], [], []
    for el in elements:
        x, y = el.get("x", 0), el.get("y", 0)
        w, h = el.get("width", 0), el.get("height", 0)
        pts = el.get("points") or []
        if pts:  # lines/arrows/freedraw: bounds from points relative to x,y
            px = [x + p[0] for p in pts]
            py = [y + p[1] for p in pts]
            xs.append(min(px)); ys.append(min(py)); xe.append(max(px)); ye.append(max(py))
        else:
            xs.append(x); ys.append(y); xe.append(x + w); ye.append(y + h)
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xe), max(ye))


# ---------------------------------------------------------------- summary
def cmd_summary(args):
    data = load(args.file)
    els = data["elements"]
    sam = [e for e in els if not is_ada(e)]
    ada = [e for e in els if is_ada(e)]
    print(f"Canvas: {args.file}")
    print(f"Your elements: {len(sam)} | Agent's previous answer: {len(ada)}")
    if sam:
        x0, y0, x1, y1 = bbox(sam)
        print(f"Your bbox: x[{x0:.0f}..{x1:.0f}] y[{y0:.0f}..{y1:.0f}] (w={x1-x0:.0f} h={y1-y0:.0f})")
    kinds = {}
    texts = []
    for e in sam:
        kinds[e.get("type", "?")] = kinds.get(e.get("type", "?"), 0) + 1
        t = e.get("text")
        if t:
            texts.append(t.replace("\n", " ").strip())
    print("Types:", ", ".join(f"{k}×{v}" for k, v in sorted(kinds.items())) or "(none)")
    if texts:
        print("Text on canvas:")
        for t in texts:
            print(f"  • {t}")
    else:
        print("Text on canvas: (none — likely freehand; add a text label or export a PNG for clarity)")


# ---------------------------------------------------------------- merge
def _encode_image(path):
    with open(path, "rb") as f:
        raw = f.read()
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return mime, "data:%s;base64,%s" % (mime, base64.b64encode(raw).decode("ascii"))


def merge_elements(file, resp_els):
    """Merge agent-authored elements (may include images) to the right of the human's sketch.
    An image element is authored as {"type":"image","_file":"path.png","x":,"y":,"width":,"height":};
    the file is base64-encoded into the canvas `files` map. Returns the normalized elements."""
    data = load(file)
    sam = [e for e in data["elements"] if not is_ada(e)]

    # backup for undo
    if os.path.exists(file):
        shutil.copyfile(file, file.replace(".excalidraw", ".prev.excalidraw"))

    # offset target: to the right of the human's sketch, top-aligned
    if sam:
        _, sy0, sx1, _ = bbox(sam)
        target_x, target_y = sx1 + GAP, sy0
    else:
        target_x, target_y = 40, 40
    rx0, ry0, _, _ = bbox(resp_els)
    dx, dy = target_x - rx0, target_y - ry0

    group_id = f"{ADA_PREFIX}response"
    new_files, normalized = {}, []
    for i, el in enumerate(resp_els):
        el = dict(el)
        el["id"] = f"{ADA_PREFIX}{i}-{el.get('id', el.get('type', 'el'))}"
        el["x"] = el.get("x", 0) + dx
        el["y"] = el.get("y", 0) + dy
        # sensible defaults so it always opens
        el.setdefault("angle", 0)
        el.setdefault("strokeColor", ADA_BLUE)
        el.setdefault("backgroundColor", "transparent")
        el.setdefault("fillStyle", "solid")
        el.setdefault("strokeWidth", 2)
        el.setdefault("roughness", 1)
        el.setdefault("opacity", 100)
        el.setdefault("groupIds", [group_id])
        el.setdefault("seed", 1 + i)
        el.setdefault("version", 1)
        el.setdefault("versionNonce", 1 + i)
        el.setdefault("isDeleted", False)
        el.setdefault("boundElements", None)
        el.setdefault("updated", 1)
        el.setdefault("link", None)
        el.setdefault("locked", False)
        if el.get("type") in ("line", "arrow"):
            el.setdefault("points", [[0, 0], [el.get("width", 100), 0]])
            el.setdefault("lastCommittedPoint", None)
            el.setdefault("startBinding", None)
            el.setdefault("endBinding", None)
            el.setdefault("startArrowhead", None)
            el.setdefault("endArrowhead", "arrow" if el["type"] == "arrow" else None)
        if el.get("type") == "text":
            el.setdefault("fontSize", 20)
            el.setdefault("fontFamily", 1)
            el.setdefault("textAlign", "left")
            el.setdefault("verticalAlign", "top")
            el.setdefault("baseline", el.get("fontSize", 20))
            el.setdefault("containerId", None)
            el.setdefault("originalText", el.get("text", ""))
            el.setdefault("lineHeight", 1.25)
        if el.get("type") == "image":
            src = el.pop("_file", None) or el.pop("_path", None)
            if src:
                if not os.path.exists(src):
                    sys.exit(f"Image not found: {src}")
                fid = f"{ADA_PREFIX}img-{i}"
                mime, data_url = _encode_image(src)
                new_files[fid] = {"mimeType": mime, "id": fid, "dataURL": data_url,
                                  "created": 1, "lastRetrieved": 1}
                el["fileId"] = fid
            el.setdefault("status", "saved")
            el.setdefault("scale", [1, 1])
            el.setdefault("width", 320)
            el.setdefault("height", 320)
        normalized.append(el)

    # files map: keep those the human's own images reference, add the agent's new ones
    human_fileids = {e.get("fileId") for e in sam if e.get("type") == "image" and e.get("fileId")}
    disk_files = data.get("files") or {}
    data["files"] = {fid: disk_files[fid] for fid in human_fileids if fid in disk_files}
    data["files"].update(new_files)

    data["elements"] = sam + normalized  # human's untouched + fresh agent answer (old agent dropped)
    data.setdefault("appState", {}).setdefault("viewBackgroundColor", "#ffffff")
    save(file, data)
    return normalized


def cmd_merge(args):
    with open(args.response, encoding="utf-8") as f:
        resp = json.load(f)
    resp_els = resp.get("elements", []) if isinstance(resp, dict) else resp if isinstance(resp, list) else []
    if not resp_els:
        sys.exit("Response file has no elements (expected a JSON list, or an object with an 'elements' array).")
    n = merge_elements(args.file, resp_els)
    print(f"Merged {len(n)} agent elements to the right of your sketch → {args.file}")
    print("The live canvas shows it within ~1s (or run `canvas.py preview`).")


def cmd_image(args):
    """Convenience: drop a single image (that your agent generated) onto the canvas, with an optional caption."""
    if not os.path.exists(args.path):
        sys.exit(f"Image not found: {args.path}")
    resp_els = [{"type": "image", "_file": args.path, "x": 0, "y": 0,
                 "width": args.width, "height": args.height}]
    if args.caption:
        resp_els.append({"type": "text", "x": 0, "y": args.height + 14, "width": args.width,
                         "height": 24, "text": args.caption, "fontSize": 16, "fontFamily": 2,
                         "strokeColor": "#495057"})
    merge_elements(args.file, resp_els)
    print(f"Placed image {args.path} on the canvas → {args.file}")
    print("The live canvas shows it within ~1s.")


# ---------------------------------------------------------------- preview (self-contained SVG renderer)
def esc(s):
    return html.escape(str(s), quote=True)


def _poly_points(el):
    x, y = el.get("x", 0), el.get("y", 0)
    return [(x + p[0], y + p[1]) for p in (el.get("points") or [])]


def render_svg(data):
    els = [e for e in data["elements"] if not e.get("isDeleted")]
    if not els:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"></svg>'
    x0, y0, x1, y1 = bbox(els)
    pad = 40
    W, H = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
    bg = data.get("appState", {}).get("viewBackgroundColor", "#ffffff")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" '
           f'viewBox="{x0-pad:.0f} {y0-pad:.0f} {W:.0f} {H:.0f}" font-family="{FONT_MAP[2]}">',
           f'<rect x="{x0-pad:.0f}" y="{y0-pad:.0f}" width="{W:.0f}" height="{H:.0f}" fill="{esc(bg)}"/>']
    for el in els:
        t = el.get("type")
        stroke = el.get("strokeColor", "#1e1e1e")
        fillc = el.get("backgroundColor", "transparent")
        fill = "none" if fillc in (None, "transparent", "") else esc(fillc)
        sw = el.get("strokeWidth", 2)
        op = el.get("opacity", 100) / 100.0
        x, y = el.get("x", 0), el.get("y", 0)
        w, h = el.get("width", 0), el.get("height", 0)
        ang = el.get("angle", 0)
        g_open = g_close = ""
        if ang:
            cx, cy = x + w / 2, y + h / 2
            g_open = f'<g transform="rotate({math.degrees(ang):.2f} {cx:.1f} {cy:.1f})">'
            g_close = "</g>"
        common = f'stroke="{esc(stroke)}" stroke-width="{sw}" fill="{fill}" opacity="{op:.2f}"'
        if t == "rectangle":
            rx = 12 if el.get("roundness") else 0
            out.append(f'{g_open}<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" {common}/>{g_close}')
        elif t == "ellipse":
            out.append(f'{g_open}<ellipse cx="{x+w/2:.1f}" cy="{y+h/2:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}" {common}/>{g_close}')
        elif t == "diamond":
            pts = f"{x+w/2:.1f},{y:.1f} {x+w:.1f},{y+h/2:.1f} {x+w/2:.1f},{y+h:.1f} {x:.1f},{y+h/2:.1f}"
            out.append(f'{g_open}<polygon points="{pts}" {common}/>{g_close}')
        elif t in ("line", "arrow", "freedraw"):
            pts = _poly_points(el)
            if len(pts) >= 2:
                ptstr = " ".join(f"{px:.1f},{py:.1f}" for px, py in pts)
                out.append(f'<polyline points="{ptstr}" stroke="{esc(stroke)}" stroke-width="{sw}" fill="none" opacity="{op:.2f}" stroke-linecap="round" stroke-linejoin="round"/>')
                if t == "arrow" and el.get("endArrowhead", "arrow") is not None:
                    (ax, ay), (bx, by) = pts[-2], pts[-1]
                    a = math.atan2(by - ay, bx - ax)
                    L = 12
                    p1 = (bx - L * math.cos(a - 0.4), by - L * math.sin(a - 0.4))
                    p2 = (bx - L * math.cos(a + 0.4), by - L * math.sin(a + 0.4))
                    out.append(f'<polyline points="{p1[0]:.1f},{p1[1]:.1f} {bx:.1f},{by:.1f} {p2[0]:.1f},{p2[1]:.1f}" stroke="{esc(stroke)}" stroke-width="{sw}" fill="none"/>')
        elif t == "text":
            fs = el.get("fontSize", 20)
            fam = FONT_MAP.get(el.get("fontFamily", 2), FONT_MAP[2])
            anchor = {"center": "middle", "right": "end"}.get(el.get("textAlign", "left"), "start")
            tx = x + (w / 2 if anchor == "middle" else w if anchor == "end" else 0)
            lines = str(el.get("text", "")).split("\n")
            out.append(f'<text x="{tx:.1f}" y="{y+fs:.1f}" font-size="{fs}" font-family="{fam}" fill="{esc(stroke)}" text-anchor="{anchor}" opacity="{op:.2f}">')
            for i, ln in enumerate(lines):
                dy = 0 if i == 0 else fs * 1.25
                out.append(f'<tspan x="{tx:.1f}" dy="{dy:.1f}">{esc(ln)}</tspan>')
            out.append("</text>")
        elif t == "image":
            fid = el.get("fileId")
            durl = ((data.get("files") or {}).get(fid) or {}).get("dataURL") if fid else None
            if durl:
                out.append(f'{g_open}<image href="{durl}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" opacity="{op:.2f}" preserveAspectRatio="xMidYMid meet"/>{g_close}')
            else:
                out.append(f'{g_open}<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="#f1f3f5" stroke="#adb5bd"/><text x="{x+8:.1f}" y="{y+20:.1f}" font-size="12" fill="#868e96">[image]</text>{g_close}')
    out.append("</svg>")
    return "\n".join(out)


def cmd_preview(args):
    data = load(args.file)
    svg = render_svg(data)
    base = args.file.replace(".excalidraw", "-preview")
    svg_path, png_path = base + ".svg", base + ".png"
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    made_png = False
    if shutil.which("rsvg-convert"):
        try:
            subprocess.run(["rsvg-convert", "-o", png_path, svg_path], check=True)
            made_png = True
        except Exception:
            pass
    target = png_path if made_png else svg_path
    print(f"Preview: {target}")
    if not args.no_open:
        try:
            subprocess.run(["open", target], check=False)
        except Exception:
            pass


# ---------------------------------------------------------------- init
BLANK = {"type": "excalidraw", "version": 2, "source": "sam-canvas",
         "elements": [], "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
         "files": {}}


def cmd_init(args):
    if os.path.exists(args.file):
        print(f"Canvas already exists: {args.file}")
        return
    save(args.file, BLANK)
    print(f"Created blank canvas: {args.file}. Open it in Excalidraw, draw, and save.")


def main():
    ap = argparse.ArgumentParser(description="sam-canvas engine")
    ap.add_argument("--file", default=DEFAULT_FILE)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("summary")
    m = sub.add_parser("merge"); m.add_argument("response")
    p = sub.add_parser("preview"); p.add_argument("--no-open", action="store_true")
    im = sub.add_parser("image"); im.add_argument("path"); im.add_argument("--caption", default=None)
    im.add_argument("--width", type=int, default=360); im.add_argument("--height", type=int, default=360)
    sub.add_parser("init")
    args = ap.parse_args()
    {"summary": cmd_summary, "merge": cmd_merge, "preview": cmd_preview,
     "image": cmd_image, "init": cmd_init}[args.cmd](args)


if __name__ == "__main__":
    main()
