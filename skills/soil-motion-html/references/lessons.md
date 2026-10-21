# 實作紀錄（2026-10-18～19）

做過的投影片（都已轉成 spec 格式，放在各週 `slides/motion/`）：Week 8〈Antigravity Vocab Walkthrough〉第 5 頁（試做）、Week 7〈Week 6 Review〉第 5～9 頁、〈Gemini Skills Walkthrough〉第 6、8、9、10 頁（兩份都已部署）。

## 使用者的需求

1. **要有聲、要英文。** 原本以為 Review 投影片老師會現場講、建議做無聲版，使用者說她不會對照學生作品講解。之後一律做英文旁白。
2. **頁數由使用者決定。** 建議 2～4 頁，但她選了 Week 6 Review 的 5 頁。
3. **先試做、聽過才部署。** 試做檔 `_motion_trial.html` 放在原檔旁邊；原檔、Cockpit、Firebase 都等她說「部署」才動。
4. 自己補的示範內容（例如 Gemini 第 8 頁 skill 的第一則回覆、第 10 頁的問題情境、Week 6 Review 第 6 頁修正後的 8/10）在畫面上標「Example」，交付時逐條列出請她確認。

## 引擎

5. **旁白的 `currentTime` 就是時鐘**（靜音時也一樣）；旁白結束後才改用畫面時鐘跑到 `end`。這樣畫面不會跟聲音越差越多。
6. **按 Play 時語音長度可能還是 `NaN`**（瀏覽器還沒讀完 metadata）。舊寫法 `if(t < (audio.duration || 0)) audio.play()` 因此不播放，畫面照跑但沒聲音——使用者第一次聽時就是這樣。正確寫法是 `if(!(t >= audio.duration))`。
7. `seek(t)`：重設畫面（`innerHTML = INIT`）→ 從頭重跑所有到 t 為止的動作，期間加 `.mx-instant` 關掉轉場。所以動作只能改 class、文字，不能依賴「上一個狀態」。
8. **播放中版面會跳。** 內容出現時，安全置中會讓整頁（含標題）往上移 30～40 px。解法：載入時把每頁時間軸每 1.5 秒取樣一次，找最高的高度設成 `min-height` 預留。
9. 寬度改變（旋轉、縮放）要重新量：`resize` 事件之外再用 `ResizeObserver` 看寬度（只看寬度，因為 `min-height` 本身會改高度）；播放中就等停下來再量。
10. 換頁時暫停播放（`mxOnSlide`）；點動畫區不能觸發「點左右翻頁」；Play 按鈕固定寬度（"▶ Play again" 比較長，窄螢幕會換行）。
11. 多頁共用一個引擎、各頁一個 `makeMotion`。用 id 前綴區分（`g6…`、`s5…`），不要讓兩頁用同一個 id。

## 版面

12. 1366×768 的預算：kicker＋一行標題約 100 px、播放列約 54 px，動畫區約 380～420 px；兩行標題時再少約 45 px。
13. 固定高度的視窗要量「有沒有內容被切掉」（`mxClip`），不只量整頁有沒有捲動。**取樣要密（每 1～2 秒）**：Week 8 第 5 頁用每 4 秒取樣，漏掉了 36 秒時「兩個提示＋Listen」同時出現、高出 38 px 的那一刻。解法是答對時先收起提示（畫面上的「Hints used: 2」保留了資訊）。
14. 不同週的色票不同（Week 8 是 `--coral-light`，Week 7 是 `--green-light`），共用樣式要有 fallback。

## 測試環境（Claude 桌面版預覽窗格）

15. **本機檔超過約 500 KB 打不開**（加了旁白的投影片都超過）。用課程的 `slides` 伺服器（`.claude/launch.json`，port 8765）從 http 開。
16. 預覽窗格會快取本機檔；改了檔案還看到舊版時，換一個檔名或改從 http 開。
17. **窗格沒有顯示時不畫畫面**：`requestAnimationFrame` 不跑，resize 事件和 `ResizeObserver` 也不觸發。所以：用 `seek(t)` 檢查狀態；`resize_window` 之後手動 `dispatchEvent(new Event('resize'))`；實際播放和聲音請使用者在自己的瀏覽器確認。
18. `const MOTIONS` 不是 `window` 的屬性：從 Cockpit 外層用 `contentWindow.MOTIONS` 讀不到，要在投影片自己的頁面裡跑檢查。

## 旁白

19. edge-tts 預設輸出 24 kHz、48 kbit/s 的 CBR MP3，所以長度＝位元組數 ÷ 6000。分段產生後直接接在一起就能播放。
20. 逐字時間（WordBoundary）就是動作時間的來源：「念到 *feasible* 那一刻按鈕變紅」。改了旁白，所有秒數都要重對。
21. 大小：每分鐘約 360 KB，base64 後約 480 KB。Week 7 Cockpit 打包後 4.9 MB（Artifact 上限 16 MB）。

## 影片（成品 B）

22. Playwright 內建的錄影需要另外下載它自己的 ffmpeg。改用 CDP `Page.startScreencast` 收 JPEG 畫面（畫面有變才送），每張停到下一張為止，再用自己的 ffmpeg 編碼——不用多下載，畫質也比較好。
23. Playwright 用本機的 Edge（`channel="msedge"`）就能跑，不用 `playwright install`。
24. ffmpeg 的 `subtitles` 濾鏡吃不下 Windows 的磁碟機路徑（`C:`），所以在暫存資料夾裡用相對檔名。
25. 字幕從逐字時間切：每條最多約 12 個字，遇到句尾（. ! ? :）且已有 4 個字以上就斷。

## 部署

26. Week 7 Cockpit 的打包方式：原始 Cockpit 本身會讀 `window.DECK_B64`，打包＝在第 538 行插入一行 `<script>window.DECK_B64={…}</script>`。`teaching-cockpit-builder` 的 `build_artifact_bundle.py` 認不得帶 `?v=` 的 `data-src`，這週不能用。
27. Firebase 用專案裡的 `Firebase/`（不是旁邊舊的 `Firebase-AI-Language-Learning`），MCP `firebase_deploy`（`only: hosting`）。部署後用 `fetch(url, {cache:'no-store'})` 算 SHA-256 跟本機比對。

## Cockpit 原生分頁（Project 2，2026-10-19）

28. Teaching Cockpit 的原生分頁不是 SOIL 投影片，`build_motion.py` 不能用；改用該課程的專案技能 `translation-cockpit-motion`（插在指定位置、引擎放在 Cockpit 自己的 script 之後、切分頁時暫停並重新量高度）。
29. `makeMotion` 的 `$` 只找 `.mx-stage` 裡面；左欄步驟清單也要亮起來的話，`.mx-stage` 要包住整個左右兩欄。
30. 字塊下方的小標籤（HEAD、STRONG VERB 強動詞）不要用絕對定位：標籤比字寬時會換行、疊到字上。改成放在字下方的一般排版（`white-space: nowrap`、預留一行高度），檢查時順便比對標籤和字的位置。
