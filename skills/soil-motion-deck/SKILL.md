---
name: soil-motion-deck
description: 動畫教學簡報：把 SOIL Teaching Deck（教學簡報六引擎）和 motion-explainer（解說動畫）接在一起，一次做出兩樣東西。A 是一份 .pptx 教學簡報，關鍵頁嵌入會動的解說動畫；B 是同一份內容的配音字幕解說影片（MP4）。使用者說「做有動畫的教學簡報」、「簡報的關鍵頁加動畫」、「SOIL 簡報加解說動畫」、「把這個單元做成簡報和動畫影片」、「投影片裡放動畫講解」，或手上已有 SOIL 簡報想把某幾頁換成動畫時，就要使用此技能。
---

# SOIL 動畫教學簡報：一次製作，兩份成品

| 成品 | 內容 | 給誰用 |
|---|---|---|
| **A 簡報**（.pptx） | SOIL 六引擎做出的教學簡報。2–4 個 ★ 關鍵頁嵌入動畫片段，片段**靜音、沒有字幕**，老師邊播邊講 | 上課投影 |
| **B 影片**（MP4） | 同一份內容的完整解說片：配音、字幕、三色主題 | 預習、補課、上傳 |

兩份成品共用同一套動畫：先做 B，再從 B 的「靜音孿生版」把 ★ 頁的那幾格剪出來，嵌進 A。所以動畫只要做一次，兩邊秒數完全一致。

這個技能只負責「接起來」。做法以兩個上游技能為準：

- **`soil-teaching-deck`**（[mathruffian-dot/soil-teaching-deck](https://github.com/mathruffian-dot/soil-teaching-deck)）：六顆引擎、頁面角色、visual 版型、三明治結構、F-0 字型安裝。
- **`motion-explainer`**（[mathruffian-dot/claude-motion-explainer](https://github.com/mathruffian-dot/claude-motion-explainer)），以及它帶的 `motion-design`、`review-loop` 和 HyperFrames 官方 skills：腳本、旁白、分格製作、字幕、三色主題、審查、輸出。

沒裝的話，先請使用者裝好這兩個（各自的 README 有一行安裝指令），不要憑記憶硬做。

## 0. 環境

- 上游兩個技能的需求：Node.js 22+、ffmpeg、Python 3、HyperFrames，以及一個 TTS（edge-tts 或 Breeze）。
- 簡報：`npm i pptxgenjs@3.12.0`，源石黑體 H／B／M（照 SOIL 的 F-0 安裝）。
- 縮圖：Windows 有 PowerPoint 最好（`scripts/thumbs.py` 會直接用 PowerPoint 輸出，字型和影片封面跟上課時一模一樣）；沒有的話用 LibreOffice + poppler。

## 1. 開場訪談（一次問完）

1. 科目、單元、對象、上課時間（SOIL 的補問）。
2. 要哪幾份成品：**A+B（預設）**、只要 A、只要 B。只要 A 也照樣先做 B：旁白決定每一格的節奏，動畫才會自然。只是不交 B，旁白不必讓使用者試聽。
3. 配色。預設是「影片三色 + SOIL 三明治」：
   - 影片（以及簡報裡的動畫視窗）用 motion-explainer 的三色，預設黑底 `#121212`、白字 `#F2F0EA`、橘色重點 `#FF7A1A`。
   - 簡報的封面、行動頁、結語是深色頁，用影片的三色；內容頁是淺色頁，動畫放在深色的「播放視窗」裡。
   - 另一個選項：整份簡報都用深色。
4. 旁白聲音：照 motion-explainer 的規則。

## 2. SOIL 引擎一～三，標出 ★ 動畫頁

照 `soil-teaching-deck` 跑引擎一（概念定位）、引擎二（脈絡定位）、引擎三（頁面架構），每顆引擎跑完都給使用者確認。在引擎三的頁面角色表，替要做動畫的頁加上 `animate` 欄位：

```
第 6 頁：為什麼一定成立？面積拼圖
- 頁面角色：流程頁
- 唯一主重點：大正方形與三角形都沒變，所以空出來的面積相等
- animate: { frame: 04-proof, seconds: 20, poster: last }
```

**哪些頁值得做動畫**（全份 2–4 頁，每段 15–25 秒）：「隨時間改變」本身就是重點的頁。

| 適合 | 例子 |
|---|---|
| 推導、證明、過程 | 拼圖證明、反應進行、光的路徑 |
| 數量累加或比較 | 數方格 9 + 16 = 25、長條成長 |
| 迷思翻轉 | 錯誤說法 → 打叉 → 翻成正確說法 |
| 空間關係 | 旋轉、平移、展開圖、斜放的正方形 |

**不適合**：定義、表格、練習題、總結，這些頁用 SOIL 的 visual 版型就好。

## 3. 從簡報流程寫影片腳本

影片的分格順著簡報的流程走，一張對照表寫進 `BRIEF.md`：

| 簡報頁 | 影片格 | 用途 |
|---|---|---|
| 2 問題引入 | 01-hook | 只在影片裡用 |
| ★3 | 02-… | 剪成 p03 |
| 4–5 概念 | 03-… | 只在影片裡用 |
| ★6 | 04-… | 剪成 p06 |
| … | … | … |
| 13 總結 | 0N-takeaway | 只在影片裡用 |

★ 格交給 worker 時，`_dispatch_context.md` 要多寫這四條（它們會被單獨拿出來，在沒有聲音、沒有字幕的情況下播放）：

1. **只看畫面也看得懂**：關鍵的數字、標籤、結論都要寫在畫面上，不能只靠旁白。
2. **從空白開始，最後停在結論**：最後一個狀態要完整、靜止至少 1 秒，因為它就是投影片上的封面。
3. **重要內容不要放在字幕區**（y > 896 px）：影片的字幕會蓋住它，簡報裡雖然沒有字幕，但同一格要兩邊都能用。
4. 前後格的銜接（同一個梯子、同一個三角形）照常做；剪片時會自動去掉交叉淡入淡出的部分。

接下來完全照 `motion-explainer` 的流程：腳本 → 旁白 → 鏡頭 → 平行做每一格 → 組裝、字幕、配色 → draft 審查 → 輸出 B。

## 4. 靜音孿生版 → 剪出 ★ 片段

```bash
python <本技能>/scripts/make_silent.py --project <影片專案>          # 建立 <影片專案>-silent：拿掉所有 audio 軌和字幕
cd <影片專案>-silent && hyperframes render --quality high --output renders/silent.mp4
python <本技能>/scripts/cut_clips.py --project <影片專案> --video <影片專案>-silent/renders/silent.mp4 \
    --map p03=02-squares p06=04-proof p09=06-myths --out <影片專案>/deck/media
```

- `cut_clips.py` 讀 `index.html` 的轉場，從淡入結束剪到淡出開始，所以不會混到前後格。它會印出每段長度，把長度寫進講者備註。
- 封面圖預設是最後一格（`--poster last`，停在結論）。如果是迷思頁、不想提前洩漏答案，就用 `--poster first`，或給秒數（例如 `--poster 2.5`）。
- **影片有任何修改**（任何一格、配色、長度）：重跑 `make_silent.py`、輸出、`cut_clips.py`。孿生版是一份快照，不會自動跟著改。

## 5. 做簡報（SOIL 引擎四～六）

1. 引擎四（認知編修）、引擎五（風格）照 SOIL 的規則做。引擎五的配色採用第 1 步選好的方案。
2. 把 `templates/deck_helpers.js` 複製到 `<影片專案>/deck/`。`build_deck.js` 照 `templates/example_pythagoras.js` 的寫法：

```js
const { makeDeck } = require("./deck_helpers");
const D = makeDeck(pptx, { theme: { bg: "121212", fg: "F2F0EA", accent: "FF7A1A" }, mediaDir: path.join(__dirname, "media") });
const s = D.lightSlide("流程・動畫");
D.title(s, "為什麼一定成立？面積拼圖");
D.video(s, "p06", 0.6, 2.0, 8.0);   // 左側 8 吋寬的播放視窗（16:9），下方有「點一下播放」提示
// 右側 x = 9.0、寬 3.9 吋：放動畫的步驟摘要或重點，讓沒播放時這一頁也看得懂
```

3. ★ 頁的版面：左邊放動畫（8.0 × 4.5 吋），右邊放 2–3 行步驟或結論。講者備註寫：片長、在哪幾個地方停下來問學生、預期的答案。
4. 其他頁照 SOIL 的頁面角色和 visual 版型做。練習題的答案寫在講者備註，不放在投影片上。
5. `node build_deck.js`。片段還沒剪好時，`video()` 會先放一個佔位框，可以先排版。

## 6. 審查

```bash
python <本技能>/scripts/thumbs.py <deck>.pptx --out thumbs     # 每頁一張 PNG + 總覽圖 deck-*.png
```

逐張看總覽圖，對照下面的清單：

- [ ] ★ 頁的封面是動畫的那一格，不是黑框或佔位文字
- [ ] 動畫視窗沒有被其他文字或圖形蓋到；下方的播放提示看得到
- [ ] 每頁只有一個主重點；三明治結構（深色封面、行動、結語，淺色內容頁）
- [ ] 簡報和影片用的是同一套強調色，數字和用語兩邊一致
- [ ] 講者備註有片長、停下來提問的地方、答案
- [ ] 練習題的答案自己算過一次
- [ ] B 影片的審查照 `review-loop` 做完（每個子句截一格，逐張看）

## 7. 交付

交出 .pptx 和 MP4 的路徑，並說明：

- ★ 頁是哪幾頁、各幾秒、封面用了哪一格。
- 播放那台電腦要先裝好源石黑體（.pptx 不內嵌字型；沒裝會退回微軟正黑體）。
- 影片已經嵌進 .pptx，PowerPoint 和 Keynote 都能直接播放；Google 簡報不能播放嵌入的影片，要把 `media/*.mp4` 上傳到雲端硬碟，再插入影片。
- 旁白發音請使用者用耳朵聽一遍（ASR 聽不出聲調）。唸錯的字用 motion-explainer 的 `fix_voice.py` 修；修完要重剪片段、重建簡報。

`references/lessons.md` 是第一次實作（〈畢氏定理〉，13 頁、3 段動畫、110 秒影片）時踩過的坑。
