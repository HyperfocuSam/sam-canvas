# sam-canvas

**一块给「整天泡在 AI 编程助手终端里」的人用的实时画布。**

你在浏览器的 Excalidraw 画布上随手画草图；你的助手——Claude Code，或任何能执行命令行的工具——会
**结合你项目的完整上下文**读懂你画的东西，并把图示回答直接画回同一块画布上，实时更新。

[English](README.md) · 简体中文 · [繁體中文](README.zh-Hant.md) · MIT 许可证

![sam-canvas 示例：左边是随手草图，右边是助手画的图示回答](examples/auth-flow.png)

*左边是一张随手草图；右边是助手读懂之后，用蓝色画在同一块画布上的回答。*

## 我为什么做它

我有 ADHD，习惯用画的方式思考，但整天待在 Claude Code 终端里——市面上没有一个工具，能让我随手画个想法，
再让「我自己的」助手在画布上回答我。所以我给自己做了这个，也把它当成一个 skill 分享出来，说不定你也是这类人。

它刻意做得很小。白板这部分并不新鲜——Excalidraw 本来就有 AI 文生图表。这里唯一别处没有的：**回答你的是你
自己的助手——那个了解你代码库和对话的助手**，而不是只看得到画布、对你项目一无所知的模型。

这是一个公开分享的个人小工具，不是产品。没有路线图，不用注册。随便 fork、随便改。

## 配合 Claude Code 使用（主要用法）

```bash
git clone https://github.com/HyperfocuSam/sam-canvas.git
export SAM_CANVAS_HOME="$PWD/sam-canvas"
# 把现成的 skill 放进你的 Claude Code 配置：
cp -r sam-canvas/claude/skills/sam-canvas   ~/.claude/skills/
cp    sam-canvas/claude/commands/sam-canvas.md ~/.claude/commands/
```

然后在 Claude Code 里：

1. 输入 **`/sam-canvas`** → 一个专属画布窗口打开（贴在屏幕右半边）。
2. **画点东西**（方框加文字最好读；也可以把你的要求直接写在画布上）。
3. 轻推助手一下——一个字也行（「看」「?」）——它就读懂草图、结合你的仓库、把答案画上去，约 1 秒。用完点
   **折叠**收起来。

## 配合任何助手使用

不一定要 Claude Code——整个对接就是三条命令行（读取、生成 JSON、合并）。完整约定和 Excalidraw 元素格式见
[`docs/for-agents.md`](docs/for-agents.md)。

```bash
./start.sh                                # 打开画布
python3 canvas.py summary                 # 你的助手读取当前草图
# ……助手把回答设计成 Excalidraw 元素 → response.json……
python3 canvas.py merge response.json     # 约 1 秒内出现在实时画布上
```

## 工作原理

```
你在浏览器里画 ──自动保存──▶ canvas.excalidraw
                                 │  （结构化 JSON：精确的图形与文字）
              助手读取它 + 你的项目上下文
                                 │
              助手设计出图示回答 → response.json
                                 │
              canvas.py merge  ──▶  ada-* 元素写入同一个文件
                                 │
        页面每约 1 秒轮询一次，实时显示回答——无需刷新
```

- **天生不会互相覆盖。** 你和助手各自拥有文件的一半：浏览器只写你的元素，助手只写 `ada-*` 元素，你的成果
  永远不会被覆盖。
- **画布文件会跨会话保留**，它就是一个你可以随时离开、随时回来的「外置大脑」。
- **只监听本机。** 服务绑定在 `127.0.0.1`，不对外暴露。

## 老实说的局限

- **你得推它一下。** 助手不会自己盯着画布——每一轮都要你轻推一下。这是保住「你的上下文」的代价：答案来自你
  正在用的这个助手会话，所以它没法完全自动跑，否则就变回「看不到你项目」的模型了。一个字的轻推，就是设计上的成本。
- **结构化比手绘好读。** 图形和文字它读得很准；纯手绘涂鸦就得靠渲染出来「眯着眼看」。想要好效果，多用方框加文字。
- **Excalidraw 从 CDN 加载**，所以首次打开需要联网。

## 运行环境

- **Python 3.8+**（只用标准库，无需 `pip install`）
- 一个现代**浏览器**（Chrome / Chromium 会得到一个专属停靠窗口，其它浏览器则开普通标签页）
- 一个能执行命令行的 **AI 编程助手**（比如 Claude Code）
- 可选：`rsvg-convert`（来自 `librsvg`）用于生成 PNG 预览；没有它也能生成 SVG 预览

## 配置

| 环境变量 | 默认值 | 作用 |
|---|---|---|
| `SAM_CANVAS_PORT` | `3899` | 服务监听的端口 |
| `SAM_CANVAS_FILE` | `./canvas.excalidraw` | 共享画布文件的路径 |

停止服务：`kill $(lsof -tiTCP:3899 -sTCP:LISTEN)`。清空画布：`python3 canvas.py init`。

## 致谢与许可

基于 [Excalidraw](https://github.com/excalidraw/excalidraw)（MIT）构建。以 [MIT 许可证](LICENSE)发布。
作者 [Sam Wong](https://github.com/HyperfocuSam)。
