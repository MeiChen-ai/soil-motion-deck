# 📘 SOIL 英文旁白動畫投影片與解說影片製作技能 (`soil-motion-html`) 完整中文教學講義

> 本講義完整介紹如何使用 **`soil-motion-html`** 技能，將既有 SOIL HTML 互動投影片（例如放在「教學駕駛艙 Teaching Cockpit」裡的 Walkthrough、Review 等簡報）中的關鍵頁面，升級為**「英文語音旁白動畫頁（成品 A）」**，並從同一份原稿自動錄製出**「附字幕的 MP4 解說影片（成品 B）」**。

---

## 目錄
1. [核心設計理念：一次製作，兩份成品](#一核心設計理念一次製作兩份成品)
2. [環境安裝與前置準備](#二環境安裝與前置準備)
3. [Spec 資料夾結構與檔案職責詳解](#三spec-資料夾結構與檔案職責詳解)
4. [Step 1：挑頁原則——哪些頁該做動畫？哪些不該動？](#四step-1挑頁原則哪些頁該做動畫哪些不該動)
5. [Step 2：撰寫英文分段旁白與產生逐字時間軸 (`make_narration.py`)](#五step-2撰寫英文分段旁白與產生逐字時間軸-make_narrationpy)
6. [Step 3 & 4：動畫版面設計 (`slides.html` / `slides.css`) 與時間軸設定 (`configs.js`)](#六step-3--4動畫版面設計-slideshtml--slidescss-與時間軸設定-configsjs)
7. [Step 5：組裝試做檔 (`build_motion.py`) 與瀏覽器自動檢驗 (`check_motion.js`)](#七step-5組裝試做檔-build_motionpy-與瀏覽器自動檢驗-check_motionjs)
8. [Step 6：正式部署至 Teaching Cockpit、Claude Artifact 與 Firebase](#八step-6正式部署至-teaching-cockpitclaude-artifact-與-firebase)
9. [Step 7：錄製成品 B——MP4 解說影片與 SRT 字幕 (`render_video.py`)](#九step-7錄製成品-bmp4-解說影片與-srt-字幕-render_videopy)
10. [Step 8：日後修改與維護已部署的動畫頁](#十step-8日後修改與維護已部署的動畫頁)
11. [常見問題與 30 條實戰避坑指南（Troubleshooting）](#十一常見問題與-30-條實戰避坑指南troubleshooting)

---

## 一、核心設計理念：一次製作，兩份成品

| 成品 | 格式與內容 | 適用情境 |
| :--- | :--- | :--- |
| **成品 A：互動動畫頁**<br>（HTML，嵌於原投影片） | 關鍵頁變成可按 **`▶ Play`** 播放的互動動畫：內建英文語音旁白、`🔊 Voice on / 🔇 Voice off`、分段跳轉按鈕（Chapters / Chips）、進度條。畫面動作完全跟著旁白的逐字時間軸（WordBoundary）推進。 | 課堂投影、學生課後自學（Teaching Cockpit、Claude Artifact、Firebase Hosting） |
| **成品 B：解說影片**<br>（`.mp4` ＋ `.srt` 字幕） | 同一頁動畫直接錄製成 1280×720 H.264 影片，合成同一段英文旁白音軌與自動切分的 `.srt` 字幕（預設為可開關的軟字幕軌，加 `--burn` 可直接燒進畫面）。 | 課前預習、缺課補課、上傳至 YouTube 或教學平台 |

* **單一真實來源（Single Source of Truth）**：動畫只做一次！成品 A 是唯一的原稿；成品 B 用 `render_video.py` 直接從組裝好的成品 A 擷取 Base64 MP3 音檔、字幕時間軸與真實瀏覽器播放畫面，確保兩份成品的秒數、用字、畫面 100% 一致。
* **與原版 `soil-motion-deck` 的差異**：原版先做靜音的 HyperFrames 影片再剪片段放進 `.pptx` 由老師現場講解；本技能專為放在 Teaching Cockpit 裡的 HTML 投影片打造，且考量到**學生自學與課堂不一定現場口頭講解**，因此預設自帶完整英文語音旁白。
* ⚠️ **AI-assisted Translation 課程 Cockpit 原生分頁特別注意**：**AI-assisted Translation 課程的 Cockpit（如 Project 1、Project 2 等原生分頁）不是 SOIL 投影片，不要用本技能的 `build_motion.py`**，請改用該課程資料夾裡的專案技能 **`translation-cockpit-motion`**（它沿用本技能的 `motion_engine.js` 引擎與 `make_narration.py`，但會插在指定位置、把引擎放在 Cockpit 自己的 script 之後，並在切換分頁時暫停與重新量測高度）。

---

## 二、環境安裝與前置準備

### 1. Python 套件安裝
```bash
# 必備：產生 edge-tts 英文旁白與 WordBoundary 逐字時間軸
pip install edge-tts

# 成品 B（錄製 MP4 影片）必備：
pip install playwright imageio-ffmpeg
```
* **免下載額外瀏覽器**：`render_video.py` 直接呼叫本機已安裝的 Microsoft Edge（`--browser msedge`）或 Google Chrome（`--browser chrome`），**不需要**執行 `playwright install`。
* **FFmpeg 自動偵測**：若系統 `PATH` 已有 `ffmpeg` 會直接使用；若無則自動使用 `imageio-ffmpeg` 內建的執行檔。

### 2. 安裝技能至 Claude Code / Cowork 與 AntiGravity
* **Windows (PowerShell)**：
  ```powershell
  git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
  powershell -ExecutionPolicy Bypass -File .\soil-motion-html-skill\install\install.ps1
  ```
* **macOS / Linux**：
  ```bash
  git clone https://github.com/MeiChen-ai/soil-motion-html-skill.git
  bash ./soil-motion-html-skill/install/install.sh
  ```

---

## 三、Spec 資料夾結構與檔案職責詳解

製作每份投影片的動畫頁時，會在課程資料夾的投影片旁建立一個 **spec 資料夾**（例如 `Week 7/slides/motion/gemini-skills-walkthrough/`）：

```text
slides/motion/gemini-skills-walkthrough/
├── original.html      # 加動畫之前的乾淨原始投影片（每次組裝都從它開始，重組絕不疊加兩份引擎）
├── manifest.json      # 定義哪些頁要做動畫、總秒數、音檔資料夾與跳段按鈕 (chips)
├── slides.html        # 每頁一段 HTML（以 <!--SLIDE n--> 開頭），取代該頁 </h2> 之後的內容，內含 <!--CTRL name-->
├── slides.css         # 這份投影片動畫頁專用的自訂樣式
├── configs.js         # 每頁一個 makeMotion(name, { end, acts, tracks }) 時間軸動作設定
├── s6/                # 第 6 頁的旁白資料夾
│   ├── segments.json  # 分段旁白稿 [["段名", "N", "英文旁白文字"], ...]
│   ├── narration.mp3  # make_narration.py 產生的合併 MP3 音檔
│   └── narration.json # make_narration.py 產生的逐字時間軸 (WordBoundary)
└── s8/                # 第 8 頁的旁白資料夾 ...
```

### `manifest.json` 範例
```json
{
  "deck": "gemini-skills-walkthrough.html",
  "motions": [
    {
      "name": "g6",
      "slide": 6,
      "end": 47.6,
      "audio": "s6",
      "chips": [
        ["1 Write the prompt", 0],
        ["2 Send", 21.4],
        ["3 Check result", 37.46]
      ]
    }
  ]
}
```

---

## 四、Step 1：挑頁原則——哪些頁該做動畫？哪些不該動？

動手寫程式前，先讀取整份投影片的文字（Windows 主控台預設 cp950，請用 `python -I` 搭配 `sys.stdout.reconfigure(encoding="utf-8")`），逐頁判斷：

### ✅ 適合做動畫的頁面（「隨時間改變」本身就是教學重點）
1. **介面操作流程**：例如在對話框打字 → 按送出 → 出現 AI 回覆、輸入 `/` 跳出技能選單、點擊 OAuth 授權按鈕。
2. **因果與前後對照**：例如錯誤的 Prompt 規則 → 產生錯誤結果 → 修改規則 → 產生正確結果。
3. **迷思翻轉（Myth vs. Reality）**：常見的錯誤說法 → 蓋上 ❌ 印章 → 展開正確的教學原則 ✅。
4. **數量累加或條件一對一對應**：例如評分項目一格一格加分、作業需求與評分標準逐條連線對應。

### ❌ 不需要做動畫的頁面（保留靜態讓學生自己看）
* 封面頁、比較表、詞彙清單、自我檢查表（Checklist）、題目清單、範例參考卡、Your Turn 課堂實作頁。這些頁面學生需要停下來照自己的速度慢慢讀。

> 📌 **回報格式**：以表格列出每頁屬於「很適合／可以做／不需要」，並附上一句「動畫怎麼演」，先讓使用者決定要做哪幾頁（建議每份簡報 2～4 頁，但使用者可自由指定更多頁）。

---

## 五、Step 2：撰寫英文分段旁白與產生逐字時間軸 (`make_narration.py`)

### 1. 旁白撰寫規範
* **預設英文、有聲**：即使是課堂 Review 投影片也一律配英文語音旁白，不要假設老師會現場逐頁講解。
* **雙聲道角色支援**：
  * `"N"`（Narrator 預設旁白）：`en-US-JennyNeural`，語速 `-6%`。
  * `"A"`（App 示範發音，例如畫面中單字練習 App 朗讀例句）：預設 `en-GB-RyanNeural`。
* **長度與難度**：每頁總長約 **30～70 秒**，分為 **4～7 個段落**；每段對應畫面上的一個步驟，使用短句、**B1 程度**的清晰英文。
* **理論學者署名**：提到二語習得或教學理論時要明確寫出學者姓氏（如 `Lyster & Ranta`, `Swain`, `Schmidt`），與課程其他教材一致。

### 2. `segments.json` 格式與執行指令
在 `<spec>/s6/segments.json` 寫入：
```json
[
  ["1 Write the prompt", "N", "First, let's look at how we write the system instructions."],
  ["2 App demo", "A", "Could you please reschedule our meeting to Thursday?"],
  ["3 Check feedback", "N", "Notice how the feedback highlights both the polite modal and the reason."]
]
```
執行 `make_narration.py`：
```bash
python ~/.claude/skills/soil-motion-html/scripts/make_narration.py "<spec>/s6/segments.json" "<spec>/s6"
```
腳本會在終端機印出每個英文字的精準秒數（例如 `feasible@14.28`），並在 `<spec>/s6/` 下產出 `narration.mp3` 與 `narration.json`。

---

## 六、Step 3 & 4：動畫版面設計 (`slides.html` / `slides.css`) 與時間軸設定 (`configs.js`)

### 1. 版面設計原則（`slides.html` ＋ `slides.css`）
* **保留原頁 `<h2>` 標題**：`slides.html` 中以 `<!--SLIDE n-->` 開頭的片段會取代該頁 `</h2>` 之後的所有內容。
* **左欄步驟＋右欄固定視窗（`.mx-stage` 須包住左右兩欄）**：
  * 左欄放原本的步驟或重點說明（加上 `id`，當旁白講到該段時加上 `.on` 亮起）。
  * 右欄放示範視窗（`.win`），**設定固定高度**，確保對話泡泡或評分結果出現時外框不會忽大忽小。
  * ⚠️ **`.mx-stage` 包裹範圍**：因為 `makeMotion` 的 `$` 只會在 `.mx-stage` 裡面尋找元素，若左欄步驟清單也要跟著旁白亮起來，**`.mx-stage` 必須包住整個左右兩欄**。
* **字塊下方小標籤（如 `HEAD`、`STRONG VERB 強動詞`）切勿用絕對定位**：
  * 絕對定位的小標籤在比字塊本身還寬時會換行、疊到字上。請改成放在字下方的一般排版（設 `white-space: nowrap` 並預留一行高度），檢查時一併比對標籤與字的位置。
* **不靠聲音也看得懂**：關鍵數字、標籤、結論都必須直接呈現在畫面上。
* **播放器佔位標記**：在動畫區塊底部放入 `<!--CTRL g6-->`，`build_motion.py` 會自動將其替換為 `▶ Play`、`⟲ Replay`、`🔊 Voice on`、跳段按鈕（Chips）、進度條、時間顯示、Base64 `<audio>` 與 `.mx-captions` 字幕時間 JSON。
* **標明自補內容**：若有 AI 為了教學示範自己補充的內容（例如模擬的 Gemini 回覆或範例分數），畫面上要標註 `Example …`，並在交付時逐條列出請使用者確認。

### 2. 時間軸與動作設定（`configs.js`）
```javascript
makeMotion('g8', {
  end: 29.9,
  acts: ({ $, cls, text, html }) => [
    [3.72, () => { cls('#g8L2', 'on'); text('#g8Txt', '/'); }], // 旁白念到 "slash" 的瞬間
    [5.32, () => cls('#g8Menu', 'show')],
  ],
  tracks: ({ $ }) => [
    [12.58, 19.0, p => typeInto($('#g8Txt'), PROMPT_TEXT, p)]
  ]
});
```
* **`acts`（時間點動作）**：格式為 `[秒數, 動作函式]`。秒數**一律從 `narration.json` 的逐字時間查表填入**。
  * ⚠️ **重要規則**：因為使用者點擊跳段或拖曳時，`seek(t)` 會先把畫面重設為初始 HTML（`stage.innerHTML = INIT`），再瞬間重跑 `0` 到 `t` 的所有動作，所以動作函式**只能透過 `cls`、`text`、`html` 修改狀態，絕不能依賴「上一個時間點的殘留狀態」**。
* **`tracks`（連續區間動畫）**：格式為 `[起點秒數, 終點秒數, p => ...]`，其中 `p` 為 `0` 到 `1` 的進度比例。引擎內建 `typeInto(el, text, p)` 打字輔助函式與 `pressEl(el)` 按鈕按壓效果。
* **`end`（總秒數）**：設為 `narration.json` 的 `total` 總長再加上約 `0.5～1.0` 秒的尾韻停頓。
* **內建共用 CSS Class（定義於 `templates/motion.css`）**：
  * `.mx-fold` ＋ `.show`：平滑展開區塊（`max-height` 與 `opacity` 過渡）。
  * `.mx-fade` ＋ `.show`：淡入並微幅上移呈現。
  * `.mx-stamp` ＋ `.no` / `.ok`：膠囊型印章標籤（紅底 ❌ 或綠／強調色底 ✅）。
  * `.mx-caret`：閃爍的打字游標。

---

## 七、Step 5：組裝試做檔 (`build_motion.py`) 與瀏覽器自動檢驗 (`check_motion.js`)

### 1. 組裝試做副本（不動原檔）
```bash
python ~/.claude/skills/soil-motion-html/scripts/build_motion.py "<spec>" "<投影片>_motion_trial.html"
```
* 先輸出成 `_motion_trial.html`，正式投影片與 Teaching Cockpit 保持原狀。

### 2. 瀏覽器自動化驗收流程（`check_motion.js`）
1. **透過 HTTP 伺服器開啟**：因為加入 Base64 語音後的 HTML 通常超過 500 KB，桌面版預覽窗格無法直接開本機大檔，請啟動課程的 HTTP 伺服器（例如 port 8765）載入試做檔。
2. **注入 `scripts/check_motion.js` 並執行 `mxReport()`**：
   * 在桌面標準尺寸 **`1366×768`** 下，每個時間點的 `fit(over/top)` 第一個數字都必須是 **`0`**（代表全程零垂直捲動）、`stage` 高度只有單一數值（代表 `reserve()` 自動預留最高高度成功，播放時標題絕不上下跳動），且 `clip` 為 **`ok`**（固定高度視窗內沒有任何文字在某個秒數超出底邊被切掉）。
3. **檢查手機與窄螢幕尺寸（`390×844`、`844×390`、`932×430`）**：
   * 窄螢幕允許垂直捲動，但 `top`（第二個數字）不能小於標題列高度，且絕不能出現 `HSCROLL`（水平捲軸）。
   * ⚠️ 每次改變視窗大小後，先執行 `window.dispatchEvent(new Event('resize'))` 再跑 `mxReport()`。
4. **抽查關鍵秒數畫面狀態（`mxStates`）**：
   ```javascript
   mxStates('g6', 21.4, ['#g6S2', '#g6Bubble1', '#g6Stamp'])
   ```
5. **交由使用者在自己的瀏覽器試聽聲音**：確認語音節奏、發音與自補示範內容都符合預期。

---

## 八、Step 6：正式部署至 Teaching Cockpit、Claude Artifact 與 Firebase

當使用者試聽過 `_motion_trial.html` 並同意部署後：
1. 在課程 Git 倉庫先 `git commit` 一次作為安全存檔點。
2. 將試做檔複製覆蓋正式投影片檔案；把 Teaching Cockpit HTML 裡對應該投影片的 `?v=` 參數換成新版本號（防止瀏覽器快取舊版）。
3. 依據課程的 `teaching-cockpit-builder` 技能重新打包單檔 Claude Artifact（更新 `window.DECK_B64`，並留意語音每分鐘約增加 480 KB Base64 體積，總檔需小於 16 MB 上限）。
4. 部署至 Firebase Hosting（`Firebase/public/weekN/`），並用 `fetch(url, {cache: 'no-store'})` 計算線上檔案的 SHA-256 與本機逐位元組比對確認一致。
5. 完成 `git commit` 並在專案 `handoff.md` 記錄本次更新。

---

## 九、Step 7：錄製成品 B——MP4 解說影片與 SRT 字幕 (`render_video.py`)

```bash
# 錄製整份投影片裡的所有動畫頁，並合併成一支 all.mp4
python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<組好的投影片>.html" "<輸出資料夾>" --join all.mp4

# 只錄製指定動畫頁 (例如 g6 與 g8)，並將字幕直接燒進畫面 (--burn)
python ~/.claude/skills/soil-motion-html/scripts/render_video.py "<組好的投影片>.html" "<輸出資料夾>" --motion g6 --motion g8 --burn
```

* **運作原理**：Playwright 開啟本機 Edge/Chrome 載入組裝好的 HTML 投影片，跳至該頁並隱藏底欄與播放控制列（`#footer-shell, #hint, .mx-ctrl`），透過 CDP `Page.startScreencast` 擷取真實播放畫面，再由 `ffmpeg` 將畫面、原始 MP3 音軌與 `.srt` 字幕合成為 1280×720（30 fps, H.264 `crf 18` + AAC `128k`）的高畫質 MP4。
* **抽幀驗收**：錄製完成後可用 `ffmpeg -ss <秒數> -i <影片.mp4> -frames:v 1 check.jpg` 抽查幾張關鍵畫面，確認動作與字幕完全對齊。

---

## 十、Step 8：日後修改與維護已部署的動畫頁

* **永遠不要直接手動編輯正式投影片 HTML 裡的動畫程式碼**（因為正式投影片是編譯產物）。
* 正確修改步驟：
  1. 修改 `slides/motion/<deck>/`（spec 資料夾）裡的 `segments.json`、`slides.html`、`slides.css` 或 `configs.js`。
  2. 如果改了 `segments.json` 的旁白文字，請重跑 `make_narration.py`，並**根據新印出的逐字時間重新對齊 `configs.js` 裡 `acts` 的秒數**。
  3. 執行 `build_motion.py`（它會自動從乾淨的 `original.html` 重新組裝，不會疊加舊引擎）→ 跑 `check_motion.js` 驗收 → 部署。

---

## 十一、常見問題與 30 條實戰避坑指南（Troubleshooting）

完整實戰筆記收錄於技能目錄下的 [`references/lessons.md`](../references/lessons.md)，以下摘錄最重要的核心關鍵：

1. **為什麼按 Play 畫面有動但偶爾沒聲音？**
   * 瀏覽器剛載入 Base64 `<audio>` 時，`audio.duration` 可能還是 `NaN`。若寫成 `if (t < (audio.duration || 0))` 就會被跳過不播！`motion_engine.js` 已採用正確寫法 `if (!(t >= audio.duration))` 解決此問題。
2. **為什麼播放過程中整頁投影片（含標題）會上下跳動？**
   * 因為 SOIL 投影片採用垂直安全置中，當 `.mx-fold` 展開時高度改變會把標題往上推。`motion_engine.js` 的 `reserve()` 會在載入與視窗寬度改變時，自動以每 1.5 秒取樣整條時間軸，找出最高高度設為 `.mx-stage` 的 `min-height`，徹底消除跳動。
3. **為什麼在某幾秒固定高度視窗裡的內容被切掉，但 4 秒一次抽查沒發現？**
   * 當兩個提示框與按鈕同時在某 2 秒內展開時，稀疏取樣會漏掉峰值。因此 `mxReport()` 預設每 2 秒（可設為 `mxReport(1)` 每 1 秒）密集檢查 `mxClip()`，若高度超標，可在新元素展開前先將舊提示收起（例如用 `.gone` 或移除 `.show`）。
4. **Windows 下 `ffmpeg` 燒錄字幕（`--burn`）報路徑錯誤怎麼辦？**
   * `ffmpeg` 的 `subtitles` 濾鏡無法解析含 Windows 磁碟機冒號（`C:\...`）的路徑，因此 `render_video.py` 會在暫存資料夾內以 `cwd=tmp` 搭配相對路徑 `subs.srt` 執行，完美避開 Windows 路徑限制。
5. **Cockpit 原生分頁（如 AI-assisted Translation 的 Project 1 / Project 2）可以用 `build_motion.py` 嗎？**
   * 不行（Lesson #28）。Teaching Cockpit 的原生分頁不是 SOIL 投影片，請改用該課程專屬的 `translation-cockpit-motion` 技能（插在指定位置、引擎放在 Cockpit 自己的 script 之後、切換分頁時暫停並重新量測高度）。
6. **為什麼左欄步驟清單加了 `cls('#step1', 'on')` 卻沒反應，或字塊下的小標籤疊到字上？**
   * `makeMotion` 的 `$` 只找 `.mx-stage` 裡面，所以左欄步驟清單也要亮起時，**`.mx-stage` 必須包住整個左右兩欄**（Lesson #29）。
   * 字塊下方的小標籤（如 `HEAD`、`STRONG VERB 強動詞`）切勿用絕對定位，應放在字下方的一般排版（`white-space: nowrap`、預留一行高度），避免標籤比字寬時換行疊字（Lesson #30）。
