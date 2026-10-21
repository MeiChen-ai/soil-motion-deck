/* 🎬 Motion slides. Each [data-motion] block has its own narration. While it plays,
   the audio's currentTime is the clock (muted or not), so the pictures never drift
   from the voice; action times come from the narration's word timings (edge-tts). */
const MOTIONS = [];
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
function makeMotion(name, cfg){
  const root = document.querySelector('[data-motion="' + name + '"]');
  if(!root) return;
  const stage = root.querySelector('.mx-stage'), INIT = stage.innerHTML;
  const q = s => root.querySelector(s);
  const audio = q('audio'), playBtn = q('.mx-play'), narrBtn = q('.mx-narr');
  const chips = Array.from(root.querySelectorAll('.mx-chip'));
  const END = cfg.end;
  let t = 0, idx = 0, playing = false, last = 0;
  const $ = s => stage.querySelector(s);
  const h = {
    $,
    cls: (s, c, on = true) => $(s).classList.toggle(c, on),
    text: (s, v) => { $(s).textContent = v; },
    html: (s, v) => { $(s).innerHTML = v; }
  };
  const acts = cfg.acts(h).sort((a, b) => a[0] - b[0]);
  const tracks = cfg.tracks ? cfg.tracks(h) : [];
  const fmt = s => Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');

  function advance(){
    while(idx < acts.length && acts[idx][0] <= t){ acts[idx][1](); idx++; }
    tracks.forEach(([a, b, f]) => { if(t >= a) f(Math.min(1, (t - a) / (b - a))); });
    chips.forEach((c, i) => c.classList.toggle('on', t >= parseFloat(c.dataset.seek) && (i === chips.length - 1 || t < parseFloat(chips[i + 1].dataset.seek))));
    q('.mx-bar div').style.width = (t / END * 100) + '%';
    q('.mx-time').textContent = fmt(t) + ' / ' + fmt(END);
  }
  function setBtn(){ playBtn.textContent = playing ? '❚❚ Pause' : (t >= END ? '▶ Play again' : (t > 0 ? '▶ Resume' : '▶ Play')); }
  function frame(now){
    if(!playing) return;
    const audioClock = !audio.paused && !audio.ended && audio.currentTime > 0;
    t = Math.min(END, audioClock ? audio.currentTime : t + (now - last) / 1000); last = now;
    advance();
    if(t >= END){ playing = false; if(reserveLater) setTimeout(reserve); }
    setBtn();
    if(playing) requestAnimationFrame(frame);
  }
  function seek(target){
    playing = false;
    audio.pause();
    try { audio.currentTime = Math.min(target, audio.duration || target); } catch(e){}
    root.classList.add('mx-instant');
    stage.innerHTML = INIT; idx = 0; t = target; advance();
    void root.offsetWidth;
    root.classList.remove('mx-instant');
    setBtn();
  }
  function play(){
    if(t >= END) seek(0);
    playing = true; last = performance.now(); setBtn();
    // Start the voice unless it has already ended; also when its length is not known yet
    if(!(t >= audio.duration)){ try { audio.currentTime = t; } catch(e){} audio.play().catch(() => {}); }
    requestAnimationFrame(frame);
  }
  function pause(){ playing = false; audio.pause(); setBtn(); if(reserveLater) setTimeout(reserve); }
  function setNarr(){ narrBtn.textContent = audio.muted ? '🔇 Voice off' : '🔊 Voice on'; narrBtn.setAttribute('aria-pressed', String(!audio.muted)); }
  narrBtn.addEventListener('click', () => { audio.muted = !audio.muted; setNarr(); });
  setNarr();
  playBtn.addEventListener('click', () => playing ? pause() : play());
  q('.mx-replay').addEventListener('click', () => { seek(0); play(); });
  chips.forEach(c => c.addEventListener('click', () => seek(parseFloat(c.dataset.seek))));
  // Reserve the stage's tallest height over the whole timeline, so the slide (and its
  // title) never shifts while content appears. Re-measured on resize, when not playing.
  let reserveLater = false;
  function reserve(){
    if(playing){ reserveLater = true; return; }
    reserveLater = false;
    const keep = t;
    stage.style.minHeight = '';
    let tallest = 0;
    for(let s = 0; s <= END; s += 1.5){ seek(s); tallest = Math.max(tallest, stage.offsetHeight); }
    seek(END); tallest = Math.max(tallest, stage.offsetHeight);
    stage.style.minHeight = tallest + 'px';
    seek(keep);
  }
  MOTIONS.push({ root, seek, pause, reserve, end: END });
}
window.mxOnSlide = el => MOTIONS.forEach(m => el.contains(m.root) ? m.seek(reduceMotion ? m.end : 0) : m.pause());
// Re-measure when the page width changes (rotation, window resize). ResizeObserver also
// catches size changes that fire no window "resize" event; only width matters, because
// reserve() itself changes the height.
let mxResizeTimer, mxLastWidth = 0;
const mxRemeasure = () => { clearTimeout(mxResizeTimer); mxResizeTimer = setTimeout(() => MOTIONS.forEach(m => m.reserve()), 250); };
window.addEventListener('resize', mxRemeasure);
if(window.ResizeObserver) new ResizeObserver(entries => {
  const w = Math.round(entries[0].contentRect.width);
  if(mxLastWidth && w !== mxLastWidth) mxRemeasure();
  mxLastWidth = w;
}).observe(document.documentElement);
window.addEventListener('load', () => MOTIONS.forEach(m => m.reserve()));


/* Typing helper: write the first p×text characters, only when the count changes. */
const typeInto = (el, text, p) => { const n = String(Math.round(p * text.length)); if(el.dataset.n !== n){ el.dataset.n = n; el.textContent = text.slice(0, +n); } };
const pressEl = el => { el.classList.add('press'); setTimeout(() => el.classList.remove('press'), 160); };

