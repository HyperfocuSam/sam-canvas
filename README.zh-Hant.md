# sam-canvas

**一塊你和 AI 編程助理共享的即時畫布。**

你在瀏覽器裡的無限 Excalidraw 畫布上隨手畫草圖；你的 AI 助理——Claude Code，或任何能執行命令列的工具
——會**結合你專案的完整上下文**讀懂你畫的東西，並把圖示回答直接畫回同一塊畫布上，即時更新。不用再把
截圖貼到聊天框裡。

[English](README.md) · [简体中文](README.zh-Hans.md) · 繁體中文 · MIT 授權

![sam-canvas 範例：左邊是隨手草圖，右邊是助理畫的圖示回答](examples/auth-flow.png)

*左邊是一張隨手草圖；右邊是助理讀懂之後，用藍色畫在同一塊畫布上的回答。*

## 為什麼做它

用聊天框跟 AI 交流，你得先把腦子裡的空間想法翻譯成文字。獨立的 AI 白板雖然能畫，但它的模型只看得到畫布
本身——對你的程式碼庫、你們剛才聊的內容一無所知。

sam-canvas 既保留了「畫」這件事，又把它接到**你自己的**助理上——那個本來就了解你在做什麼的助理。你在畫布上
思考，它在畫布上回應，而且它真的知道你在忙什麼。

## 執行環境

- **Python 3.8+**（只用標準函式庫，無需 `pip install`）
- 一個現代**瀏覽器**（Excalidraw 從 CDN 載入，首次使用需要連網）
- 一個能執行命令列的 **AI 編程助理**（例如 Claude Code）。選用，但這正是它的意義所在。
- 選用：`rsvg-convert`（來自 `librsvg`）用來產生 PNG 預覽；沒有它也能產生 SVG 預覽。

## 快速開始

```bash
git clone https://github.com/HyperfocuSam/sam-canvas.git
cd sam-canvas
./start.sh            # 啟動本機伺服器（連接埠 3899）並開啟畫布
```

畫點東西，然後讓你的助理來回答（見下文）。你畫的內容會隨手自動儲存，助理隨時都能讀取——不需要「匯出檔案」
這一步。

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

- **天生不會互相覆蓋。** 你和助理各自擁有檔案的一半：瀏覽器只寫你的元素，助理只寫 `ada-*` 元素。你的成果
  永遠不會被覆蓋。
- **可摺疊。** 頂列有個按鈕，能把整塊畫布收成角落裡的小標籤，再按一下展開。
- **只監聽本機。** 伺服器綁定在 `127.0.0.1`，不對外開放。

## 搭配 Claude Code 使用

[`claude/`](claude) 目錄裡備好了現成的 skill 和 `/sam-canvas` 指令。把這個目錄設為 Claude Code 的落腳位置
（`export SAM_CANVAS_HOME=/path/to/sam-canvas`），再把 `claude/skills/sam-canvas` 和
`claude/commands/sam-canvas.md` 複製到你的 `.claude/` 資料夾。然後：

1. 輸入 `/sam-canvas` → 畫布開啟。
2. 畫草圖，然後說「看一下」或 `/sam-canvas 幫我整理成架構圖`。
3. Claude 讀懂你的草圖，結合你的程式碼庫理解它，把回答畫在畫布上。

## 搭配任何助理使用

整個對接就是三條命令列——讀取、產生 JSON、合併。完整約定和 Excalidraw 元素格式見
[`docs/for-agents.md`](docs/for-agents.md)。

```bash
python3 canvas.py summary                 # 讀取目前草圖（類型、文字、外框範圍）
# ……你的助理把回答設計成 Excalidraw 元素 → response.json……
python3 canvas.py merge response.json     # 約 1 秒內出現在即時畫布上
python3 canvas.py preview                 # 選用：產生 canvas-preview.png 覆核一下
```

## 設定

| 環境變數 | 預設值 | 作用 |
|---|---|---|
| `SAM_CANVAS_PORT` | `3899` | 伺服器監聽的連接埠 |
| `SAM_CANVAS_FILE` | `./canvas.excalidraw` | 共享畫布檔案的路徑 |

停止伺服器：`kill $(lsof -tiTCP:3899 -sTCP:LISTEN)`。清空畫布：`python3 canvas.py init`。

## 致謝與授權

基於 [Excalidraw](https://github.com/excalidraw/excalidraw)（MIT）建置。sam-canvas 以
[MIT 授權](LICENSE)釋出。
