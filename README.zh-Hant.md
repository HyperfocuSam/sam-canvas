# sam-canvas

**一塊給「整天泡在 AI 編程助理終端機裡」的人用的即時畫布。**

你在瀏覽器的 Excalidraw 畫布上隨手畫草圖；你的助理——Claude Code，或任何能執行命令列的工具——會
**結合你專案的完整上下文**讀懂你畫的東西，並把圖示回答直接畫回同一塊畫布上，即時更新。

[English](README.md) · [简体中文](README.zh-Hans.md) · 繁體中文 · MIT 授權

![sam-canvas 範例：左邊是隨手草圖，右邊是助理畫的圖示回答](examples/auth-flow.png)

*左邊是一張隨手草圖；右邊是助理讀懂之後，用藍色畫在同一塊畫布上的回答。*

## 我為什麼做它

我有 ADHD，習慣用畫的方式思考，但整天待在 Claude Code 終端機裡——市面上沒有一個工具，能讓我隨手畫個想法，
再讓「我自己的」助理在畫布上回答我。所以我給自己做了這個，也把它當成一個 skill 分享出來，說不定你也是這類人。

它刻意做得很小。白板這部分並不新鮮——Excalidraw 本來就有 AI 文字生成圖表。這裡唯一別處沒有的：**回答你的是你
自己的助理——那個了解你程式碼庫和對話的助理**，而不是只看得到畫布、對你專案一無所知的模型。

這是一個公開分享的個人小工具，不是產品。沒有路線圖，不用註冊。隨便 fork、隨便改。

## 搭配 Claude Code 使用（主要用法）

```bash
git clone https://github.com/HyperfocuSam/sam-canvas.git
export SAM_CANVAS_HOME="$PWD/sam-canvas"
# 把現成的 skill 放進你的 Claude Code 設定：
cp -r sam-canvas/claude/skills/sam-canvas   ~/.claude/skills/
cp    sam-canvas/claude/commands/sam-canvas.md ~/.claude/commands/
```

然後在 Claude Code 裡：

1. 輸入 **`/sam-canvas`** → 一個專屬畫布視窗開啟（停靠在螢幕右半邊）。
2. **畫點東西**（方框加文字最好讀；也可以把你的要求直接寫在畫布上）。
3. 輕推助理一下——一個字也行（「看」「?」）——它就讀懂草圖、結合你的程式碼庫、把答案畫上去，約 1 秒。用完按
   **摺疊**收起來。

## 搭配任何助理使用

不一定要 Claude Code——整個對接就是三條命令列（讀取、產生 JSON、合併）。完整約定和 Excalidraw 元素格式見
[`docs/for-agents.md`](docs/for-agents.md)。

```bash
./start.sh                                # 開啟畫布
python3 canvas.py summary                 # 你的助理讀取目前草圖
# ……助理把回答設計成 Excalidraw 元素 → response.json……
python3 canvas.py merge response.json     # 約 1 秒內出現在即時畫布上
```

## 運作原理

```
你在瀏覽器裡畫 ──自動儲存──▶ canvas.excalidraw
                                 │  （結構化 JSON：精確的圖形與文字）
              助理讀取它 + 你的專案上下文
                                 │
              助理設計出圖示回答 → response.json
                                 │
              canvas.py merge  ──▶  ada-* 元素寫入同一個檔案
                                 │
        頁面每約 1 秒輪詢一次，即時顯示回答——無需重新整理
```

- **天生不會互相覆蓋。** 你和助理各自擁有檔案的一半：瀏覽器只寫你的元素，助理只寫 `ada-*` 元素，你的成果
  永遠不會被覆蓋。
- **畫布檔案會跨工作階段保留**，它就是一個你可以隨時離開、隨時回來的「外接大腦」。
- **只監聽本機。** 伺服器綁定在 `127.0.0.1`，不對外開放。

## 老實說的限制

- **你得推它一下。** 助理不會自己盯著畫布——每一輪都要你輕推一下。這是保住「你的上下文」的代價：答案來自你
  正在用的這個助理工作階段，所以它沒法完全自動跑，否則就變回「看不到你專案」的模型了。一個字的輕推，就是設計上的成本。
- **結構化比手繪好讀。** 圖形和文字它讀得很準；純手繪塗鴉就得靠算圖出來「瞇著眼看」。想要好效果，多用方框加文字。
- **Excalidraw 從 CDN 載入**，所以首次開啟需要連網。

## 執行環境

- **Python 3.8+**（只用標準函式庫，無需 `pip install`）
- 一個現代**瀏覽器**（Chrome / Chromium 會得到一個專屬停靠視窗，其它瀏覽器則開一般分頁）
- 一個能執行命令列的 **AI 編程助理**（例如 Claude Code）
- 選用：`rsvg-convert`（來自 `librsvg`）用來產生 PNG 預覽；沒有它也能產生 SVG 預覽

## 設定

| 環境變數 | 預設值 | 作用 |
|---|---|---|
| `SAM_CANVAS_PORT` | `3899` | 伺服器監聽的連接埠 |
| `SAM_CANVAS_FILE` | `./canvas.excalidraw` | 共享畫布檔案的路徑 |

停止伺服器：`kill $(lsof -tiTCP:3899 -sTCP:LISTEN)`。清空畫布：`python3 canvas.py init`。

## 致謝與授權

基於 [Excalidraw](https://github.com/excalidraw/excalidraw)（MIT）建置。以 [MIT 授權](LICENSE)釋出。
作者 [Sam Wong](https://github.com/HyperfocuSam)。
