---
name: soil-motion-html
description: >
  把既有的 SOIL HTML 互動投影片（如 soil-html-deck 產出的 .html 簡報，或 Teaching Cockpit 裡的 Walkthrough、Review）的關鍵頁改成「英文旁白動畫頁（Narrated Motion Slides）」：按 ▶ Play 後畫面跟著旁白逐字時間一步步動、可暫停、跳段、開關聲音；同一份動畫還能直接匯出成有配音和字幕的 MP4 解說影片（免裝 HyperFrames）。
  使用者說「把第幾頁做成動畫」、「這份投影片哪些頁可以做成動畫」、「投影片加旁白動畫」、「做成解說影片」、「soil-motion-html」、「動畫頁」，或英文請求如 "turn slides into narrated motion slides", "animate key slides in my HTML deck", "add voiceover animation to slides", "export motion slides to MP4 video" 時，請務必使用此技能。改編自 mathruffian-dot/soil-motion-deck。
---

# SOIL 旁白動畫頁（HTML 網頁版）：一次製作，兩份成品

> 🌐 **Language Rule（雙語互動原則）**：
> - 若使用者以**中文**提問，請以**繁體中文**與使用者討論選頁與回報進度；若使用者以**英文（English）**提問，請全程以**英文**回報與互動。
> - 投影片內的語音旁白預設使用清楚易懂的 **CEFR B1 英文短句**（若使用者明確指定其他語言再依指示調整）。

| 成品 | 內容 | 給誰用 |
|---|---|---|
| **A 動畫頁**（HTML，放在原本的投影片裡） | 關鍵頁變成按 ▶ Play 播放的動畫：英文旁白、🔊 Voice on/off、分段跳轉、進度條。畫面跟著旁白的逐字時間動作 | 上課投影、學生課後自己看（單一 HTML 檔、Cockpit、Artifact、Firebase） |
| **B 影片**（MP4＋SRT） | 同一頁動畫錄成影片，配同一段旁白，附字幕 | 預習、補課、上傳 |

**動畫只做一次。** A 是唯一的原稿；B 用 `render_video.py` 直接從 A 錄出來，所以秒數、用字、畫面完全一致。

和原版 `soil-motion-deck` 的差別：原版先做 HyperFrames 影片再剪片段放進 `.pptx`，而且片段是靜音的、老師現場講。`soil-motion-html` 則是針對 HTML 投影片（例如用 `soil-html-deck` 做出來的互動簡報），**免裝 HyperFrames，且預設自帶完整英文旁白**。要 `.pptx` 內嵌靜音片段或 HyperFrames 獨立解說片時，請改用同 repo 下的 `soil-motion-deck` 技能。

**AI-assisted Translation 課程的 Cockpit（Project 1、Project 2 等原生分頁）不要用本技能的 `build_motion.py`**，改用該課程資料夾裡的專案技能 `translation-cockpit-motion`（它沿用本技能的引擎與 `make_narration.py`）。

## 0. 工具與位置

本技能資料夾（以下稱 `<sk>`）依 Agent 環境位於：
- **Google Antigravity**：`~/.gemini/config/skills/soil-motion-html`
- **OpenCode**：`~/.config/opencode/skills/soil-motion-html` 或 `~/.agents/skills/soil-motion-html`
- **Claude Code / Cowork**：`~/.claude/skills/soil-motion-html`
- **Codex**：`~/.codex/skills/soil-motion-html`

開工前請先確認 `<sk>` 實際存在的路徑。

| 檔案 | 用途 |
|---|---|
| `scripts/make_narration.py` | 分段旁白 JSON → `narration.mp3`＋逐字時間 `narration.json`（edge-tts） |
| `scripts/build_motion.py` | 從 spec 資料夾組出動畫版投影片（片段、樣式、引擎、時間設定、base64 語音、字幕時間） |
| `scripts/render_video.py` | 成品 B：從組好的投影片錄出 MP4＋SRT |
| `scripts/check_motion.js` | 在預覽窗格的 javascript 工具裡逐時間點檢查狀態和版面 |
| `templates/motion_engine.js` | 共用播放引擎（`makeMotion`）；**不要在 spec 裡複製一份** |
| `templates/motion.css` | 共用播放列、淡入、展開樣式 |
| `references/lessons.md` | 實作時踩過的坑，動手前先讀 |

需求：Python 3、`pip install edge-tts`。成品 B 另需 Playwright（Python）＋本機已安裝的 Edge 或 Chrome（不用另外下載瀏覽器），以及 ffmpeg（PATH 上沒有的話 `pip install imageio-ffmpeg`）。

**spec 資料夾**放在課程資料夾裡、投影片旁邊，例如 `Week 7/slides/motion/gemini-skills-walkthrough/`：

```
original.html      加動畫之前的投影片；每次都從它組，重組不會疊兩份引擎
manifest.json      {"deck": "...html", "motions": [{"name","slide","end","audio","chips"}]}
slides.html        每頁一段，以 <!--SLIDE n--> 開頭；取代該頁 </h2> 之後的內容；內含 <!--CTRL name-->
slides.css         這份投影片動畫頁專用的樣式
configs.js         每頁一個 makeMotion(name, {end, acts, tracks})
s6/ s8/ ...        各頁的 segments.json、narration.mp3、narration.json
```

範例（都是這個格式）：`Week 7/slides/motion/gemini-skills-walkthrough/`（第 6、8、9、10 頁，已部署）、`Week 7/slides/motion/week-6-review/`（第 5～9 頁，已部署）、`Week 8/slides/motion/antigravity-vocab-walkthrough/`（第 5 頁，試做）。新的投影片照 Gemini 那份的寫法做。

## 1. 讀投影片、挑頁（先給使用者確認）

讀整份投影片的文字（`python -I`、`sys.stdout.reconfigure(encoding="utf-8")`，主控台是 cp950），逐頁判斷。

**適合做動畫**：「隨時間改變」本身就是重點的頁。
- 介面操作流程（打字 → 送出 → 回覆、打 / 選選單、點授權按鈕）
- 因果、前後對照（錯誤的規則 → 錯誤的結果 → 修正 → 正確的結果）
- 迷思翻轉（錯的說法 → 打叉 → 正確說法）
- 數量累加或對應（分數一格格加、需求和評分列一對一連起來）

**不需要**：封面、比較表、清單、檢查表、題目清單、範例卡、Your Turn。這些頁學生要能停下來慢慢讀。

用表格回報：「很適合／可以做／不需要」，每頁一句「動畫怎麼演」。頁數由使用者決定（建議值是每份 2～4 頁，但使用者可以選更多）。

## 2. 旁白（英文、有聲）

- **預設英文、有聲**，Review 投影片也一樣。不要假設老師會現場講。
- 預設聲音 `en-US-JennyNeural`、`-6%`；畫面裡「App 念出句子」之類用第二個聲音 `A`（預設 `en-GB-RyanNeural`）。
- 每頁約 30～70 秒，分 4～7 段；每段對應畫面上的一個步驟，用短句、B1 程度的英文。
- 理論要寫出人名（Lyster & Ranta、Swain、Schmidt……），跟課程其他教材一致。
- 段名就是之後的跳段按鈕：在 `manifest.json` 的 `chips` 寫 2～3 個「段落開頭」。

```bash
python <sk>/scripts/make_narration.py "<spec>/s6/segments.json" "<spec>/s6"
```

`segments.json` 是 `[["名稱", "N", "旁白文字"], ...]`。腳本會印出每個字的時間，下一步用它。

## 3. 動畫頁的版面（slides.html＋slides.css）

- 保留原頁的標題；左欄放原本的說明文字（加 `id`，旁白講到時用 `.on` 亮起來），右欄放動畫視窗（`.win`）。
- 畫面要**不靠聲音也看得懂**：數字、標籤、結論都寫在畫面上。
- 示範用的視窗（Gemini 對話、評分結果……）設**固定高度**，內容改變時版面不動。
- 一定要放 `<!--CTRL 名稱-->`，`build_motion.py` 會換成 ▶ Play／⟲ Replay／🔊 Voice、跳段按鈕、進度條和語音。
- 有真實資料就用真實的（例如老師在 Gemini 實測的回覆）。**自己補的示範內容**在畫面上標「Example …」，交付時逐條列出請使用者確認。
- 照課程 `CLAUDE.md` 的 SOIL 版面規則（安全置中、窄螢幕、Focus 模式）。

## 4. 時間設定（configs.js）

```js
makeMotion('g8', { end: 29.9, acts: ({ $, cls, text, html }) => [
  [3.72, () => { cls('#g8L2', 'on'); text('#g8Txt', '/'); }],   // 念到 "slash" 的時間
  [5.32, () => cls('#g8Menu', 'show')],
], tracks: ({ $ }) => [[12.58, 19.0, p => typeInto($('#g8Txt'), TEXT, p)]] });
```

- `acts`：`[秒數, 動作]`。秒數**一律從 `narration.json` 的逐字時間來**，對到旁白念到那個字的瞬間。動作只能改 class 或文字，而且要能從頭重算（`seek` 會重設畫面再重跑到該時間）。
- `tracks`：連續動畫（打字）。`typeInto(el, text, p)`、`pressEl(el)` 在引擎裡。
- `end`：旁白總長＋約 0.5～1 秒。
- 常用 class：`.mx-fold`＋`show`（展開）、`.mx-fade`＋`show`、`.gx-b`＋`in`（聊天泡泡）、`.mx-stamp` 加 `no`/`ok`（❌/✅ 標籤）、`.gone`（完全隱藏）。
- 游標：絕對定位的 SVG，`translate()` 到目標元素（範例見第 8 頁）。

## 5. 組裝、測試

```bash
python <sk>/scripts/build_motion.py "<spec>" "<投影片>_motion_trial.html"
```

**先做試做副本**，原檔和 Cockpit 都不動。測試（細節見 `references/lessons.md`）：

1. 用 `preview_start` 啟動 `slides` 伺服器（port 8765），用 http 開試做檔。預覽窗格開不了超過約 500 KB 的本機檔。
2. 貼上 `scripts/check_motion.js`，跑 `mxReport()`：1366×768 每個時間點都要 `0/…`（不捲動），stage 高度只有一個值，`clip ok`。
3. 再量 390×844、844×390、932×430：可以捲動，但頂端（第二個數字）不能小於標題列高度，不能有 `HSCROLL`。每次 `resize_window` 之後先 `window.dispatchEvent(new Event('resize'))`。
4. `mxStates(name, t, [...])` 抽查關鍵時間點的畫面狀態。
5. **聲音一定要請使用者在自己的瀏覽器聽**。預覽窗格隱藏時不畫畫面，無法實際播放；不要說「已確認可以播放」。

交付時給：檔案連結、每頁長度、旁白全文（表格）、需要使用者確認的自補內容。

## 6. 正式輸出／部署（使用者聽過、同意後）

- **一般單一 HTML 簡報（學生課堂作品／獨立簡報）**：
  1. 確認試做檔 `<投影片>_motion_trial.html` 試聽與版面無誤後，將試做檔複製為正式檔（或保留原檔備份於 `spec/original.html`）。
- **課程 Teaching Cockpit 專案（老師部署流程）**：
  1. 在課程 Git commit 一次當存檔點。
  2. 試做檔 → 覆蓋正式投影片；Cockpit 裡該投影片的 `?v=` 換新版本號。
  3. 照 `teaching-cockpit-builder` skill 更新：重新打包（`DECK_B64` 那一行）、Artifact（先 read 確認沒有別人改過）、Firebase（`Firebase/public/weekN/`）、線上逐位元組比對、commit、在 `handoff.md` 記一筆。
  4. 打包檔變大（旁白每分鐘約 480 KB），交付時要告知大小。

## 7. 成品 B：影片

```bash
python <sk>/scripts/render_video.py "<組好的投影片>.html" "<輸出資料夾>" [--motion g6] [--burn] [--join all.mp4]
```

- 每頁一支 MP4（1280×720，H.264＋AAC）和一份 SRT。字幕預設是可開關的字幕軌；`--burn` 直接燒進畫面。
- 錄的是真實播放（每頁花的時間等於片長），播放列在錄影時會隱藏。
- 錄完抽幾張畫面看（ffmpeg `-ss 秒數 -frames:v 1`），確認動作時間和字幕對得上。

## 8. 修改已部署的動畫頁

改 spec 資料夾裡的檔案 → 旁白有改就重跑 `make_narration.py` 並**重新對時間**（`acts` 的秒數都會變）→ `build_motion.py` 重新組 → 測試 → 部署。不要直接改正式投影片裡的動畫碼；正式檔是組出來的成品。
