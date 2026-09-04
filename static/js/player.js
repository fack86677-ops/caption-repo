// Harsh Caption Generator - Video Player & Synchronized Live Caption Overlay Engine

class KalakarPlayer {
  constructor(videoElement, captionOverlayElement, safeZoneElement) {
    this.video = videoElement;
    this.captionOverlay = captionOverlayElement;
    this.safeZone = safeZoneElement;
    
    this.segments = [];
    this.currentStyle = { ...TEMPLATES[0].style };
    this.displayMode = 'chunk'; // 'chunk' (2-3 words), 'single' (1 word pop), 'full' (full line)
    this.currentTime = 0;
    this.duration = 0;
    this.isPlaying = false;
    this.isDragging = false;
    
    this.initEvents();
    this.initAspectRatioControls();
  }

  setSegments(segments) {
    this.segments = segments || [];
    let maxSegmentTime = 0;
    this.segments.forEach(seg => {
      if (seg.end > maxSegmentTime) maxSegmentTime = seg.end;
      (seg.words || []).forEach(w => {
        if (w.end > maxSegmentTime) maxSegmentTime = w.end;
      });
    });
    if (maxSegmentTime > this.duration) {
      this.duration = maxSegmentTime;
      if (window.kalakarTimeline) {
        window.kalakarTimeline.setDuration(this.duration);
      }
      this.updateTimeDisplay();
    }
    this.render();
  }

  setStyle(style) {
    this.currentStyle = { ...this.currentStyle, ...style };
    if (style.displayMode) this.displayMode = style.displayMode;
    this.applyOverlayStyle();
    this.render();
  }

  initEvents() {
    const updateDur = () => {
      const vidDur = this.video ? this.video.duration : 0;
      if (vidDur && !isNaN(vidDur) && vidDur > 0 && isFinite(vidDur)) {
        this.duration = vidDur;
        this.updateTimeDisplay();
        if (window.kalakarTimeline) {
          window.kalakarTimeline.setDuration(this.duration);
        }
        if (window.currentProject) {
          window.currentProject.duration = this.duration;
        }
      }
    };

    this.video.addEventListener('loadedmetadata', updateDur);
    this.video.addEventListener('durationchange', updateDur);
    this.video.addEventListener('canplay', updateDur);
    this.video.addEventListener('loadeddata', updateDur);

    this.video.addEventListener('timeupdate', () => {
      this.currentTime = this.video.currentTime;
      const vidDur = this.video.duration;
      if (vidDur && !isNaN(vidDur) && vidDur > 0 && isFinite(vidDur) && vidDur > this.duration) {
        this.duration = vidDur;
        if (window.kalakarTimeline) {
          window.kalakarTimeline.setDuration(this.duration);
        }
      }
      this.render();
      if (window.kalakarTimeline) {
        window.kalakarTimeline.updatePlayhead(this.currentTime);
      }
      this.updateTimeDisplay();
    });

    this.video.addEventListener('play', () => {
      this.isPlaying = true;
      this.updatePlayBtn();
    });

    this.video.addEventListener('pause', () => {
      this.isPlaying = false;
      this.updatePlayBtn();
      this.render(); // Ensure captions remain crisp on pause
    });

    // Click on video player frame to play/pause
    const frame = document.getElementById('player-frame');
    if (frame) {
      frame.addEventListener('click', (e) => {
        if (this.isDragging) return;
        if (e.target === this.captionOverlay || this.captionOverlay.contains(e.target)) return;
        this.togglePlay();
      });
    }

    // Make caption overlay draggable smoothly across video container
    this.captionOverlay.addEventListener('mousedown', (e) => {
      this.isDragging = true;
      this.captionOverlay.classList.add('dragging');
      e.stopPropagation();
    });

    window.addEventListener('mousemove', (e) => {
      if (!this.isDragging) return;
      const f = document.getElementById('player-frame') || this.video.parentElement;
      if (!f) return;

      const rect = f.getBoundingClientRect();
      let percentX = ((e.clientX - rect.left) / rect.width) * 100;
      let percentY = ((e.clientY - rect.top) / rect.height) * 100;

      percentX = Math.max(8, Math.min(92, percentX));
      percentY = Math.max(8, Math.min(92, percentY));

      this.currentStyle.posX = Math.round(percentX * 10) / 10;
      this.currentStyle.posY = Math.round(percentY * 10) / 10;

      this.applyOverlayStyle();
      if (window.kalakarEditor) {
        window.kalakarEditor.updatePositionInputs(this.currentStyle.posX, this.currentStyle.posY);
      }
    });

    window.addEventListener('mouseup', () => {
      if (this.isDragging) {
        setTimeout(() => { this.isDragging = false; }, 50);
        this.captionOverlay.classList.remove('dragging');
      }
    });
  }

  togglePlay() {
    if (!this.video) return;
    if (this.video.paused) {
      const p = this.video.play();
      if (p !== undefined) {
        p.catch(e => console.warn("Video playback resumed:", e));
      }
    } else {
      this.video.pause();
    }
  }

  seek(timeInSeconds) {
    const vidDur = (this.video && this.video.duration && !isNaN(this.video.duration) && this.video.duration > 0 && isFinite(this.video.duration))
      ? this.video.duration
      : (this.duration || 3600);
    const target = Math.max(0, Math.min(vidDur, timeInSeconds));
    if (this.video) {
      this.video.currentTime = target;
    }
    this.currentTime = target;
    this.render();
    this.updateTimeDisplay();
    if (window.kalakarTimeline) {
      window.kalakarTimeline.updatePlayhead(this.currentTime);
    }
  }

  initAspectRatioControls() {
    const btn916 = document.getElementById('btn-aspect-9-16');
    const btn169 = document.getElementById('btn-aspect-16-9');
    const btn11 = document.getElementById('btn-aspect-1-1');

    const updateBtns = (active) => {
      [btn916, btn169, btn11].forEach(b => {
        if (!b) return;
        b.className = 'px-2 py-0.5 text-[11px] font-medium text-[#9CA3AF] hover:text-white rounded transition';
      });
      if (active === '9:16' && btn916) btn916.className = 'px-2 py-0.5 text-[11px] font-bold rounded bg-[#00C48C] text-black transition';
      if (active === '16:9' && btn169) btn169.className = 'px-2 py-0.5 text-[11px] font-bold rounded bg-[#00C48C] text-black transition';
      if (active === '1:1' && btn11) btn11.className = 'px-2 py-0.5 text-[11px] font-bold rounded bg-[#00C48C] text-black transition';
    };

    if (btn916) btn916.addEventListener('click', () => { this.setAspectRatio('9:16'); updateBtns('9:16'); });
    if (btn169) btn169.addEventListener('click', () => { this.setAspectRatio('16:9'); updateBtns('16:9'); });
    if (btn11) btn11.addEventListener('click', () => { this.setAspectRatio('1:1'); updateBtns('1:1'); });
  }

  setAspectRatio(ratio) {
    const frame = document.getElementById('player-frame');
    if (!frame) return;
    this.aspectRatio = ratio;

    if (ratio === '16:9') {
      frame.style.aspectRatio = '16/9';
      frame.style.width = '85%';
      frame.style.maxHeight = '65vh';
    } else if (ratio === '1:1') {
      frame.style.aspectRatio = '1/1';
      frame.style.width = 'auto';
      frame.style.maxHeight = '65vh';
    } else {
      frame.style.aspectRatio = '9/16';
      frame.style.width = 'auto';
      frame.style.maxHeight = '75vh';
    }
    this.render();
    if (window.showToast) window.showToast(`Canvas switched to <b>${ratio}</b> aspect ratio`);
  }

  toggleSafeZone(visible) {
    if (visible) {
      this.safeZone.classList.remove('hidden');
    } else {
      this.safeZone.classList.add('hidden');
    }
  }

  applyOverlayStyle() {
    const s = this.currentStyle;
    this.captionOverlay.style.left = `${s.posX}%`;
    this.captionOverlay.style.top = `${s.posY}%`;
    this.captionOverlay.style.fontFamily = s.fontFamily || 'Montserrat';
    this.captionOverlay.style.fontWeight = s.fontWeight || '900';
    this.captionOverlay.style.fontSize = `${s.fontSize}px`;
    this.captionOverlay.style.textAlign = s.textAlign || 'center';
    this.captionOverlay.style.textTransform = (s.textTransform !== undefined) ? s.textTransform : 'uppercase';
    this.captionOverlay.style.color = s.color || '#FFFFFF';
    this.captionOverlay.style.paintOrder = 'stroke fill markers';

    if (s.bgBox) {
      this.captionOverlay.style.backgroundColor = s.bgColor || 'rgba(0,0,0,0.75)';
      this.captionOverlay.style.padding = '8px 18px';
      this.captionOverlay.style.borderRadius = '10px';
    } else {
      this.captionOverlay.style.backgroundColor = 'transparent';
      this.captionOverlay.style.padding = '6px 12px';
    }

    // High quality stroke that NEVER hollows out or splits the text
    if (s.strokeWidth > 0) {
      const strokePx = Math.min(s.strokeWidth, 2.5);
      this.captionOverlay.style.webkitTextStroke = `${strokePx}px ${s.strokeColor || '#000000'}`;
    } else {
      this.captionOverlay.style.webkitTextStroke = '0px transparent';
    }

    // Crisp high-contrast drop shadow
    if (s.shadow) {
      this.captionOverlay.style.textShadow = `0 3px 6px rgba(0,0,0,0.9), 0 0 2px #000, 0 1px 3px rgba(0,0,0,0.8)`;
    } else {
      this.captionOverlay.style.textShadow = 'none';
    }
  }

  render() {
    const now = this.currentTime;
    // Find active segment
    const activeSeg = this.segments.find(seg => now >= (seg.start - 0.05) && now <= (seg.end + 0.15));

    if (!activeSeg) {
      this.captionOverlay.innerHTML = '';
      this.captionOverlay.style.opacity = '0';
      return;
    }

    this.captionOverlay.style.opacity = '1';
    const s = this.currentStyle;
    const words = activeSeg.words || [];

    if (words.length === 0) {
      this.captionOverlay.innerHTML = `<span class="word-span">${activeSeg.text}</span>`;
      return;
    }

    // Determine words to display based on displayMode
    let visibleWords = words;

    if (this.displayMode === 'single') {
      // Show ONLY the single active word currently spoken
      const activeWord = words.find(w => now >= w.start && now <= w.end);
      if (activeWord) {
        visibleWords = [activeWord];
      } else {
        visibleWords = [words[0]];
      }
    } else if (this.displayMode === 'chunk') {
      // Chunk into 2-3 words per burst (Modern Reels / Hormozi style)
      const chunkSize = 3;
      const activeWordIdx = words.findIndex(w => now >= w.start && now <= w.end);
      let chunkStart = 0;
      if (activeWordIdx >= 0) {
        chunkStart = Math.floor(activeWordIdx / chunkSize) * chunkSize;
      }
      visibleWords = words.slice(chunkStart, chunkStart + chunkSize);
    }

    // Render words cleanly with vibrant highlight
    let html = '';
    visibleWords.forEach(w => {
      const isWordActive = (now >= (w.start - 0.02) && now <= (w.end + 0.05));
      let wordStyle = 'display: inline-block; margin: 0 4px; paint-order: stroke fill markers;';
      let wordClass = 'word-span';

      if (isWordActive) {
        wordClass += ' active';
        const hlColor = s.highlightColor || '#FFE600';
        wordStyle += `color: ${hlColor}; font-weight: 900; filter: drop-shadow(0 0 10px ${hlColor}); transform: scale(1.15);`;
      } else if (w.highlight) {
        wordStyle += `color: ${s.highlightColor || '#FFE600'};`;
      } else {
        wordStyle += `color: ${s.color || '#FFFFFF'};`;
      }

      const emojiBadge = w.emoji ? `<span style="margin-left: 3px;">${w.emoji}</span>` : '';
      html += `<span class="${wordClass}" style="${wordStyle}">${w.word}${emojiBadge}</span> `;
    });

    this.captionOverlay.innerHTML = html;
  }

  updatePlayBtn() {
    const playIcon = document.getElementById('player-play-icon');
    if (playIcon) {
      playIcon.innerHTML = this.isPlaying 
        ? `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>`
        : `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>`;
    }
  }

  updateTimeDisplay() {
    const el = document.getElementById('player-time-display');
    if (el) {
      const formatTime = (secs) => {
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        const ms = Math.floor((secs % 1) * 100);
        return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}:${String(ms).padStart(2, '0')}`;
      };
      el.textContent = `${formatTime(this.currentTime)} / ${formatTime(this.duration)}`;
    }
  }
}

window.KalakarPlayer = KalakarPlayer;
