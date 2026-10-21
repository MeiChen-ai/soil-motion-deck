/* Checks for motion slides, pasted into the Browser pane's javascript tool (page context).
   Load the deck over http (the course's `slides` server in .claude/launch.json, port 8765):
   the pane won't open a local file over ~500 KB, and a deck with narration is bigger.

   Then call, e.g.:
     mxReport()                 every motion slide: fit, height and clipping, sampled over time
     mxStates('g6', 21, ['#g6S3', '#g6P3'])   what is visible at one moment
   After resize_window, call  window.dispatchEvent(new Event('resize'))  first: a hidden pane
   draws no frames, so it fires neither resize events nor ResizeObserver callbacks.
   Live playback (requestAnimationFrame) also stalls in a hidden pane; check with seek(t),
   and leave listening to the user's own browser. */
window.mxM = name => MOTIONS.find(m => m.root.dataset.motion === name);
window.mxQuiet = fn => { const st = document.createElement('style'); st.textContent = '*{transition:none!important;animation:none!important}'; document.head.appendChild(st); void document.body.offsetWidth; try { return fn(); } finally { st.remove(); } };
window.mxSlideOf = m => Array.from(document.querySelectorAll('.slide')).indexOf(m.root.closest('.slide')) + 1;

/* overflow of the active slide / top of its content / horizontal scroll */
window.mxFit = () => mxQuiet(() => { const s = document.querySelector('.slide.active'); s.scrollTop = 0;
  return (s.scrollHeight - s.clientHeight) + '/' + Math.round(s.querySelector('.slide-inner').getBoundingClientRect().top) + (document.documentElement.scrollWidth > innerWidth ? '/HSCROLL' : ''); });

/* content sticking out of a fixed-height window (elements inside closed folds are skipped) */
window.mxClip = m => mxQuiet(() => { let need = 0; m.root.querySelectorAll('.gx-body,.mx-body,.win-body').forEach(b => {
  const br = b.getBoundingClientRect();
  b.querySelectorAll('*').forEach(e => { if(e.closest('.mx-fold:not(.show)') || e.closest('.gone') || !e.offsetHeight) return;
    const r = e.getBoundingClientRect(); if(r.bottom > br.bottom + 1) need = Math.max(need, Math.round(r.bottom - br.bottom)); }); }); return need; });

window.mxReport = (step = 2) => innerWidth + 'x' + innerHeight + '\n' + MOTIONS.map(m => {
  goTo(mxSlideOf(m)); const st = m.root.querySelector('.mx-stage'); const fits = new Set(), hs = new Set(), clips = [];
  for(let t = 0; t <= m.end + 0.001; t += step){ m.seek(Math.min(t, m.end)); fits.add(mxFit()); hs.add(st.offsetHeight); const c = mxClip(m); if(c) clips.push(t + ':' + c); }
  m.seek(0);
  return m.root.dataset.motion + '  fit(over/top) ' + [...fits].join(' ') + '  stage ' + [...hs].join('/') + ' (reserved ' + st.style.minHeight + ')  clip ' + (clips.join(' ') || 'ok');
}).join('\n');

window.mxStates = (name, t, sels) => { const m = mxM(name); goTo(mxSlideOf(m)); m.seek(t);
  return mxQuiet(() => sels.map(s => { const el = document.querySelector(s); if(!el) return s + ' MISSING';
    let p = el, vis = true; while(p && !(p.classList && p.classList.contains('slide'))){ const c = getComputedStyle(p); if(c.opacity === '0' || c.maxHeight === '0px' || c.display === 'none'){ vis = false; break; } p = p.parentElement; }
    return s + (vis ? ' ✔ ' + (el.getAttribute('class') || '') + ' | ' + (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60) : ' (hidden)'); }).join('\n')); };
'motion checks loaded: mxReport(), mxStates(name, t, selectors)';
