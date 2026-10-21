# 🎬 SOIL Narrated Motion Slides & Video Builder (`soil-motion-html`)
# 🎬 SOIL 英文旁白動畫投影片與解說影片製作技能（中英雙語教學指南）

> 🌐 **[🇹🇼 中文版使用說明與教學指南（請往下捲動）](#-第一部分中文版使用說明與教學指南-traditional-chinese)** ｜ **[🇺🇸 Click Here for English Usage Guide & Tutorial](#-part-2-english-usage-guide--tutorial)**
>
> 📄 **獨立完整教學講義 / Standalone Complete Tutorials**:
> - 📘 [中文完整教學講義 (`docs/TUTORIAL_ZH.md`)](./docs/TUTORIAL_ZH.md)
> - 📗 [English Complete Tutorial (`docs/TUTORIAL_EN.md`)](./docs/TUTORIAL_EN.md)

---

## 🇹🇼 第一部分：中文版使用說明與教學指南 (Traditional Chinese)

### 一、 這個 Skill 是什麼？解決什麼問題？

**`soil-motion-html`** 是專為 **SOIL HTML 互動教學投影片**（例如鑲嵌在「教學駕駛艙 Teaching Cockpit」裡的 Walkthrough、Review 等簡報）設計的**「英文旁白動畫頁 ＋ MP4 解說影片」雙棲製作技能**（改編自 `mathruffian-dot/soil-motion-deck`）。

核心理念是 **「一次製作，兩份成品（Build Once, Two Outputs）」**：

| 成品 | 產出格式與內容 | 適用情境 |
| :--- | :--- | :--- |
| **成品 A：互動旁白動畫頁**<br>（HTML，直接嵌在原投影片內） | 將投影片的關鍵頁升級為可按 **`▶ Play`** 播放的互動動畫頁：<br>• 內建英文語音旁白（`edge-tts`）與 `🔊 Voice on / 🔇 Voice off` 切換<br>• 畫面動作（打字、游標點擊、氣泡對話、重點高亮、展開卡片）精準對齊旁白的**逐字時間軸（WordBoundary）**<br>• 支援 `⟲ Replay`、分段跳轉按鈕（Chapters / Chips）與即時進度條 | 課堂投影教學、學生課後自學（Teaching Cockpit、Claude Artifact、Firebase Hosting） |
| **成品 B：獨立解說影片**<br>（`.mp4` ＋ `.srt` 字幕檔） | 由 `scripts/render_video.py` 直接從成品 A 錄製並合成：<br>• 自動開啟本機 Edge / Chrome 播放成品 A 並擷取高畫質畫面<br>• 合成同一段英文旁白音軌與自動切分的 `.srt` 字幕（預設為可開關軟字幕軌，亦可用 `--burn` 燒錄進畫面，或用 `--join` 合併多頁為單一影片） | 課前預習、缺課補課、上傳至 YouTube / 教學平台 |

> 💡 **為什麼「動畫只做一次」？**
> **成品 A 是唯一的原稿（Single Source of Truth）**；成品 B 直接從組裝好的成品 A 讀取 Base64 音檔、字幕時間軸與實際渲染畫面。因此兩份成品的秒數、用字、畫面與動畫節奏 100% 一致，絕不發生圖文或影音不同步的問題。
>
> 💡 **與原版 `soil-motion-deck` 的差別**：
> 原版是先做靜音的 HyperFrames 影片再剪片段放進 `.pptx` 供老師現場口頭講解；本技能則是針對放在 Teaching Cockpit 裡的 HTML 投影片，且**預設自帶完整英文語音旁白**，讓學生不靠老師現場講解也能自己聽懂、看懂。
>
> ⚠️ **AI-assisted Translation 課程 Cockpit 原生分頁特別注意**：
> **AI-assisted Translation 課程的 Cockpit（如 Project 1、Project 2 等原生分頁）不是 SOIL 投影片，請勿使用本技能的 `build_motion.py`**；請改用該課程資料夾裡的專案技能 **`translation-cockpit-motion`**（它沿用本技能的 `motion_engine.js` 引擎與 `make_narration.py`，並針對 Cockpit 原生分頁處理插入位置、script 順序與切換分頁時的暫停／重新量高）。

---

### 二、 技能架構與內建工具一覽

本技能安裝於 `~/.claude/skills/soil-motion-html`（Claude Code / Cowork）與 `~/.gemini/config/skills/soil-motion-html`（AntiGravity）：

```text
soil-motion-html/
├── SKILL.md                      # AI Agent 核心工作流指令與規範
├── README.md                     # 中英雙語快速上手指南（本文件）
├── docs/
│   ├── TUTORIAL_ZH.md            # 完整中文教學講義（含 Spec 結構詳解與避坑指南）
│   └── TUTORIAL_EN.md            # Complete English Tutorial & Reference
├── scripts/
│   ├── make_narration.py         # 分段旁白 JSON → narration.mp3 ＋ 逐字時間軸 narration.json (edge-tts)
│   ├── build_motion.py           # 從 spec 資料夾組裝出含動畫頁、語音與字幕時間的完整 HTML 投影片
│   ├── render_video.py           # 成品 B：從組裝好的 HTML 投影片錄製 1280x720 MP4 ＋ SRT 字幕
│   └── check_motion.js           # 瀏覽器自動驗收腳本（檢查時間軸版面高度、溢出捲動與裁切）
├── templates/
│   ├── motion_engine.js          # 共用播放與時間軸引擎（makeMotion、語音時鐘同步、自動預留最高高度）
│   └── motion.css                # 共用播放控制列、淡入 (.mx-fade)、摺疊展開 (.mx-fold)、印章 (.mx-stamp) 樣式
├── references/
│   └── lessons.md                # 30 條實戰踩坑紀錄與工程最佳實踐（動手前必讀）
└── install/
    ├── install.ps1               # Windows PowerShell 一鍵安裝腳本
    └── install.sh                # macOS / Linux Bash 一鍵安裝腳本
```

---

### 三、 環境需求與安裝方式

#### 1. 安裝必備 Python 套件
```bash
# 必備（產生成品 A 的英文旁白與逐字時間軸）
pip install edge-tts

# 選配（需產生成品 B 的 MP4 影片與 SRT 字幕時安裝）
pip install playwright imageio-ffmpeg
```
*(註：`render_video.py` 直接呼叫電腦已安裝的 Microsoft Edge 或 Google Chrome，**不需要**執行 `playwright install` 下載額外瀏覽器！)*

#### 2. 安裝此 Skill 到 Claude Code / Cowork 與 AntiGravity

##### 方法 A：請 AI Agent 自動幫你安裝（最推薦）
複製以下這段話貼給你的 Claude 或 AntiGravity：
```text
請幫我 clone https://github.com/MeiChen-ai/soil-motion-html-skill.git 並安裝 soil-motion-html 技能：
1. Claude Code / Cowork：複製到 ~/.claude/skills/soil-motion-html/
2. AntiGravity：複製到 ~/.gemini/config/skills/soil-motion-html/
請確認 SKILL.md、scripts/、templates/、references/ 與 docs/ 都完整包含。
```

##### 方法 B：使用終端機一鍵安裝腳本
**Windows (PowerShell)：**
```powershell
git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
powershell -ExecutionPolicy Bypass -File .\soil-motion-html-skill\install\install.ps1
```

**macOS / Linux：**
```bash
git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
bash ./soil-motion-html-skill/install/install.sh
```

---

### 四、 標準工作流程（8 大步驟）

1. **Step 1 — 讀投影片、挑頁（先給使用者確認）**：
   * AI 會先讀取整份 HTML 投影片，找出**「隨時間改變本身就是教學重點」**的頁面（例如：介面操作流程、因果／前後對照、迷思翻轉、分數累加或條件對應）。
   * 靜態頁（封面、比較表、清單、檢查表、Your Turn 練習頁）則保留讓學生慢慢閱讀。
   * AI 會以表格回報每頁「很適合／可以做／不需要」及「動畫怎麼演」，由你決定要做哪幾頁（建議每份簡報挑 2～4 頁關鍵頁）。
2. **Step 2 — 撰寫英文旁白並產生逐字時間軸（`make_narration.py`）**：
   * 預設採用 **B1 程度短句英文、有聲旁白**（主講聲音 `N` 為 `en-US-JennyNeural`，語速 `-6%`；畫面內 App 朗讀聲音 `A` 為 `en-GB-RyanNeural`）。
   * 每頁約 30～70 秒，分為 4～7 個段落寫入 `<spec>/sN/segments.json`，執行：
     ```bash
     python ~/.claude/skills/soil-motion-html/scripts/make_narration.py "<spec>/s6/segments.json" "<spec>/s6"
     ```
   * 自動產出 `narration.mp3` 與記錄每個英文字精準秒數的 `narration.json`。
3. **Step 3 — 設計動畫頁版面（`slides.html` ＋ `slides.css`）**：
   * 保留原投影片標題；左欄放步驟說明文字（旁白講到該步時加 `.on` 亮起），右欄放固定高度的示範視窗（`.win`），下方放置 `<!--CTRL 名稱-->` 標記。
   * **注意 `.mx-stage` 包裹範圍與小標籤排版**：`makeMotion` 的 `$` 只找 `.mx-stage` 內部，因此若左欄步驟也要亮起，**`.mx-stage` 必須包住整個左右兩欄**；字塊下方的小標籤（如 `HEAD`、`STRONG VERB 強動詞`）**不要用絕對定位**（以免標籤比字寬時換行疊字），請改放字下方的一般排版（`white-space: nowrap`、預留一行高度）。
   * 若有 AI 補充的示範內容，畫面上會明確標示 `Example …` 並在交付時列出請你確認。
4. **Step 4 — 設定時間軸動作（`configs.js`）**：
   * 根據 `narration.json` 的逐字秒數設定 `makeMotion(name, { end, acts, tracks })`，讓畫面在念到關鍵字的那一瞬間觸發高亮、展開（`.mx-fold.show`）、淡入（`.mx-fade.show`）、蓋章（`.mx-stamp.no/.ok`）或打字動畫（`typeInto`）。
5. **Step 5 — 組裝試做檔與自動化版面檢驗（`build_motion.py` ＋ `check_motion.js`）**：
   * 先組裝成 `<投影片>_motion_trial.html` 試做檔（絕不直接動到正式檔與 Cockpit）：
     ```bash
     python ~/.claude/skills/soil-motion-html/scripts/build_motion.py "<spec>" "<deck>_motion_trial.html"
     ```
   * 在瀏覽器執行 `check_motion.js` 的 `mxReport()` 與 `mxStates()`，確保 `1366×768` 全程零捲動、標題不跳動、固定高度視窗無裁切（`clip ok`），並測試手機／窄螢幕尺寸。
6. **Step 6 — 使用者試聽確認後正式部署**：
   * 你在自己的瀏覽器試聽確認無誤後，AI 才會覆蓋正式投影片、更新 Teaching Cockpit 的 `?v=` 版本號、重新打包 Claude Artifact（`DECK_B64`）並部署至 Firebase Hosting。
7. **Step 7 — 輸出 MP4 解說影片與 SRT 字幕（`render_video.py`）**：
   ```bash
   python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<組好的投影片>.html" "<輸出資料夾>" [--motion g6] [--burn] [--join all.mp4]
   ```
8. **Step 8 — 日後修改已部署的動畫頁**：
   * 永遠修改 `slides/motion/<deck>/`（spec 資料夾）內的原始設定，重跑 `make_narration.py` → 對齊秒數 → `build_motion.py` 重新組裝，乾淨不疊加重複程式碼。

---

### 五、 常用許願 Prompt 範本（直接複製貼給 AI）

#### 📋 範本 1：請 AI 分析一份投影片並推薦適合做動畫的頁面
```text
請使用 soil-motion-html 技能，幫我讀這份投影片 `[投影片路徑.html]`，逐頁分析哪些頁適合改成「英文旁白動畫頁」，用表格列出「很適合／可以做／不需要」以及每頁預計怎麼演，先讓我確認要挑哪幾頁。
```

#### 📋 範本 2：把指定頁面做成英文旁白動畫頁（先出試做檔）
```text
請使用 soil-motion-html 技能，把 `[投影片路徑.html]` 的第 [6, 8, 9] 頁做成英文旁白動畫頁：
1. 在 `slides/motion/[簡報名稱]/` 建立 spec 資料夾並備份 `original.html`。
2. 撰寫 B1 程度的英文分段旁白，用 `make_narration.py` 產生 MP3 與逐字時間軸。
3. 設計左欄步驟＋右欄動畫視窗版面，對齊逐字秒數寫好 `configs.js`。
4. 用 `build_motion.py` 組出 `_motion_trial.html` 試做檔並跑完 `check_motion.js` 檢查，把試做檔連結、每頁秒數與旁白全文表格交給我試聽。
```

#### 📋 範本 3：試聽滿意後，正式部署到 Teaching Cockpit 與 Firebase
```text
我聽過 `_motion_trial.html` 確認沒問題了！請幫我照 soil-motion-html 的部署流程：
1. 先在課程 Git commit 一次當存檔點。
2. 用試做檔覆蓋正式投影片，更新 Teaching Cockpit 的 `?v=` 版本號與打包檔（`DECK_B64`）。
3. 部署到 Firebase Hosting 並做線上 SHA-256 比對，最後 git commit 並更新 `handoff.md`。
```

#### 📋 範本 4：把做好的動畫頁匯出成 MP4 解說影片＋SRT 字幕
```text
請使用 soil-motion-html 的 `render_video.py`，把 `[組好的投影片.html]` 裡的所有動畫頁錄製成 1280x720 的 MP4 影片與 SRT 字幕，存到 `[輸出資料夾]`，並同時用 `--join` 合併成一支完整影片（若需要燒錄字幕請加上 `--burn`）。
```

---
---

## 🇺🇸 Part 2: English Usage Guide & Tutorial

### 1. What Is `soil-motion-html`?

**`soil-motion-html`** is an end-to-end skill for Claude Code / Cowork and AntiGravity that upgrades key slides inside existing **SOIL interactive HTML presentations** (such as Walkthrough and Review decks hosted inside a Teaching Cockpit) into **English-narrated step-by-step animated slides** and **standalone MP4 + SRT explainer videos** (adapted from `mathruffian-dot/soil-motion-deck`).

It follows a strict **"Build Once, Two Outputs"** architecture:

| Output | Format & Features | Target Use Case |
| :--- | :--- | :--- |
| **Output A: Narrated Motion Slide**<br>(Interactive HTML inside the deck) | Turns key slides into interactive players with **`▶ Play`**, **`⟲ Replay`**, **`🔊 Voice on / 🔇 Voice off`**, clickable chapter chips (`.mx-chip`), and a live progress bar.<br>• Visual actions (typing, cursor clicks, chat bubbles, callout highlights, folding cards, stamps) are anchored to **exact word-level timestamps (`WordBoundary`)** from `edge-tts`. | Live classroom projection & self-paced student review (Teaching Cockpit, Claude Artifact, Firebase Hosting) |
| **Output B: Explainer Video**<br>(`.mp4` + `.srt` subtitles) | Rendered directly from Output A via `scripts/render_video.py`:<br>• Launches local Edge/Chrome via Playwright + CDP (`Page.startScreencast`) to capture the live animation.<br>• Muxes the exact same MP3 voiceover and auto-chunked `.srt` captions via `ffmpeg` (soft subtitle track by default, `--burn` for burned-in captions, `--join` to concatenate clips). | Pre-class preview, make-up lessons, LMS / YouTube upload |

> 💡 **Why Build Once?**
> **Output A is the single source of truth.** Output B extracts the inlined Base64 MP3 audio and `.mx-captions` word timings directly from the built HTML deck and records the actual slide playback. Timing, wording, and visuals never drift apart.
>
> ⚠️ **Important Note for AI-Assisted Translation Cockpit Native Tabs**:
> **Native tabs inside the AI-assisted Translation Teaching Cockpit (such as Project 1, Project 2, etc.) are not SOIL slide decks—do NOT run `build_motion.py` on them.** Instead, use the project-specific skill **`translation-cockpit-motion`** inside that course folder (which reuses this skill's `motion_engine.js` and `make_narration.py`, while handling native Cockpit injection points, script ordering, and tab-switch pause/re-measurement).

---

### 2. Repository & Skill Directory Structure

Installed at `~/.claude/skills/soil-motion-html` (Claude Code / Cowork) and `~/.gemini/config/skills/soil-motion-html` (AntiGravity):

```text
soil-motion-html/
├── SKILL.md                      # Core agent instructions and 8-step workflow
├── README.md                     # Bilingual quick-start guide (this file)
├── docs/
│   ├── TUTORIAL_ZH.md            # Complete Traditional Chinese tutorial
│   └── TUTORIAL_EN.md            # Complete English tutorial & technical reference
├── scripts/
│   ├── make_narration.py         # Converts segments.json → narration.mp3 + word-level narration.json (edge-tts)
│   ├── build_motion.py           # Compiles a spec/ directory into a motion-enabled SOIL HTML deck
│   ├── render_video.py           # Output B: records 1280x720 H.264 MP4 + SRT subtitles from a built HTML deck
│   └── check_motion.js           # In-browser verification suite (mxReport, mxStates, mxFit, mxClip)
├── templates/
│   ├── motion_engine.js          # Shared playback engine (makeMotion, audio-clock sync, auto min-height reservation)
│   └── motion.css                # Shared control bar, .mx-fold, .mx-fade, .mx-stamp, and .mx-caret styles
├── references/
│   └── lessons.md                # 30 battle-tested engineering lessons & edge-case fixes
└── install/
    ├── install.ps1               # Windows PowerShell one-click installer
    └── install.sh                # macOS / Linux Bash one-click installer
```

---

### 3. Prerequisites & Installation

#### 1. Python Dependencies
```bash
# Required for Output A (neural TTS audio + word-boundary timestamps)
pip install edge-tts

# Optional for Output B (MP4 + SRT video rendering)
pip install playwright imageio-ffmpeg
```
*(Note: `render_video.py` uses your locally installed Microsoft Edge `msedge` or Google Chrome via `channel="msedge"`, so you do **not** need to run `playwright install` to download browser binaries!)*

#### 2. Install the Skill (Claude Code / Cowork & AntiGravity)

##### Option 1: Ask Your AI Agent to Install Automatically (Recommended)
Paste the following prompt into Claude or AntiGravity:
```text
Please clone https://github.com/MeiChen-ai/soil-motion-html-skill.git and install the `soil-motion-html` skill:
1. For Claude Code / Cowork: copy to `~/.claude/skills/soil-motion-html/`
2. For AntiGravity: copy to `~/.gemini/config/skills/soil-motion-html/`
Make sure `SKILL.md`, `scripts/`, `templates/`, `references/`, and `docs/` are all included.
```

##### Option 2: One-Click CLI Installer Script
**Windows (PowerShell):**
```powershell
git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
powershell -ExecutionPolicy Bypass -File .\soil-motion-html-skill\install\install.ps1
```

**macOS / Linux:**
```bash
git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
bash ./soil-motion-html-skill/install/install.sh
```

---

### 4. The 8-Step Workflow

1. **Step 1 — Inspect Deck & Select Candidate Slides (Confirm with User First)**:
   * Read the deck and identify slides where **change over time is the core teaching point**:
     * UI walkthroughs (typing a prompt → sending → receiving a response, `/` command menus, permission dialogs)
     * Cause-and-effect or before/after comparisons (buggy rule → wrong output → fix → right output)
     * Myth-busting flips (common misconception → ❌ stamp → ✅ principle)
     * Cumulative scoring or 1-to-1 rubric mapping
   * Keep static reference slides (cover, comparison tables, checklists, Your Turn tasks) static so students can read at their own pace.
   * Present a table categorizing slides into **Great Fit / Possible / Keep Static** with a 1-sentence animation summary for user approval (typically 2–4 slides per deck).
2. **Step 2 — Generate Segmented English Narration (`make_narration.py`)**:
   * Default to **spoken B1-level English narration** (narrator voice `N`: `en-US-JennyNeural` at `-6%`; secondary app voice `A`: `en-GB-RyanNeural`).
   * Aim for 30–70 seconds per slide across 4–7 segments in `<spec>/sN/segments.json`:
     ```bash
     python ~/.claude/skills/soil-motion-html/scripts/make_narration.py "<spec>/s6/segments.json" "<spec>/s6"
     ```
   * Produces `narration.mp3` and `narration.json` containing exact word-boundary timestamps (`[[word, sec], ...]`).
3. **Step 3 — Build Motion Slide Markup & Styles (`slides.html` + `slides.css`)**:
   * Keep the slide's original `<h2>` title; place step callouts in the left column (highlighted via `.on` as narrated) and a fixed-height demo window (`.win`) in the right column, followed by `<!--CTRL name-->`.
   * **`.mx-stage` Scope & Sub-Label Flow**: Because `makeMotion`'s `$` selector queries inside `.mx-stage` only, **`.mx-stage` must wrap both the left and right columns** whenever left-column step items need `.on` highlighting. Never use `position: absolute` for small sub-labels beneath word tokens (e.g., `HEAD`, `STRONG VERB`), as labels wider than the word will wrap and overlap the text; place them in normal flow beneath the word (`white-space: nowrap`, reserving one line of height).
   * Design visuals so the slide is **self-explanatory even with the sound muted**. Mark any AI-supplied demo examples with `Example …` and list them for user confirmation.
4. **Step 4 — Anchor Actions to Word Timestamps (`configs.js`)**:
   * Configure `makeMotion(name, { end, acts, tracks })` using exact word timestamps from `narration.json`.
   * Because `seek(t)` resets `stage.innerHTML = INIT` and replays all actions up to `t` with transitions suppressed (`.mx-instant`), actions must be pure class/text mutations (`cls`, `text`, `html`).
5. **Step 5 — Assemble Trial Deck & Verify Layout (`build_motion.py` + `check_motion.js`)**:
   * Always build a `<deck>_motion_trial.html` copy first without touching the production deck:
     ```bash
     python ~/.claude/skills/soil-motion-html/scripts/build_motion.py "<spec>" "<deck>_motion_trial.html"
     ```
   * Serve over HTTP and run `mxReport()` and `mxStates()` from `scripts/check_motion.js` across `1366×768` (must have `0/...` overflow, constant reserved stage height, and `clip ok`) and mobile viewports (`390×844`, `844×390`, `932×430`).
   * Ask the user to listen to the trial file in their own browser before deployment.
6. **Step 6 — Deploy to Production (After User Approval)**:
   * Create a Git checkpoint commit, copy the trial deck over the production deck, bump the `?v=` query string in the Teaching Cockpit, re-bundle `DECK_B64` for Claude Artifact, deploy to Firebase Hosting, verify SHA-256 online, and log in `handoff.md`.
7. **Step 7 — Render Output B Explainer Videos (`render_video.py`)**:
   ```bash
   python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<built_deck>.html" "<out_dir>" [--motion g6] [--burn] [--join all.mp4]
   ```
8. **Step 8 — Updating Deployed Motion Slides**:
   * Always edit files inside the `spec/` folder (`slides/motion/<deck>/`), re-run `make_narration.py` (and re-anchor `acts` timestamps if narration changed), and re-run `build_motion.py` from `original.html`.

---

### 5. Quick-Start Prompt Templates (English)

#### 📋 Template 1: Analyze a Deck & Recommend Slides to Animate
```text
Please use the `soil-motion-html` skill to inspect `[path/to/deck.html]` and evaluate each slide for animation. Give me a table categorizing slides into "Great Fit / Possible / Keep Static" with a one-sentence description of how each candidate animation would play out, so I can choose which slides to animate.
```

#### 📋 Template 2: Build Narrated Motion Slides (Trial Build)
```text
Please use the `soil-motion-html` skill to turn slides [6, 8, 9] of `[path/to/deck.html]` into English-narrated motion slides:
1. Create the spec folder at `slides/motion/[deck-name]/` and save a clean copy of `original.html`.
2. Write B1-level segmented English narration and run `make_narration.py` to generate MP3 audio and word timings.
3. Build the two-column motion layouts (`slides.html` + `slides.css`) and word-synced timeline (`configs.js`).
4. Compile `<deck>_motion_trial.html` with `build_motion.py`, run `check_motion.js` across desktop and mobile viewports, and share the trial file link, durations, and full narration table for my review.
```

#### 📋 Template 3: Deploy Approved Motion Deck to Cockpit & Firebase
```text
I have listened to `_motion_trial.html` and approved it. Please follow Step 6 of `soil-motion-html`:
1. Commit a checkpoint in Git.
2. Replace the production deck with the trial build, bump `?v=` in the Teaching Cockpit, and update the bundled Artifact (`DECK_B64`).
3. Deploy to Firebase Hosting, verify the live SHA-256 hash, commit to Git, and update `handoff.md`.
```

#### 📋 Template 4: Render MP4 + SRT Explainer Videos (Output B)
```text
Please use `render_video.py` from `soil-motion-html` to render all motion slides in `[path/to/built_deck.html]` into 1280x720 MP4 videos + SRT subtitles in `[output_folder]`, and join them into a single `all_motions.mp4` file (add `--burn` if burned-in subtitles are needed).
```
