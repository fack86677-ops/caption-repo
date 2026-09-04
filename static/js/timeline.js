// Multi-track Timeline Visualizer with Real Audio Waveform & Interactive Word Edge Trimming for Harsh Caption Generator

class KalakarTimeline {
  constructor(containerElement, player) {
    this.container = containerElement;
    this.player = player;
    this.segments = [];
    this.duration = 15.0;
    this.zoom = 1.0; // scale factor
    this.pixelsPerSecond = 80;
    this.mode = 'word'; // 'word' or 'line'
    this.videoFilename = 'siblings_walking_into_hallway.mp4';
    this.audioPeaks = null;
    
    this.initDOM();
    this.initEvents();
  }

  initDOM() {
    this.container.innerHTML = `
      <!-- Vertical Timeline Resize Bar Handle -->
      <div id="timeline-resizer-handle" class="h-2.5 bg-[#161D26] hover:bg-[#00C48C] cursor-row-resize flex items-center justify-center transition group border-t border-[#1F2732]" title="Drag up/down to adjust timeline height">
        <div class="w-10 h-1 bg-[#374151] group-hover:bg-[#00C48C] rounded-full"></div>
      </div>

      <div class="flex items-center justify-between px-4 py-2 border-b border-[#1F2732] bg-[#0E1318] text-xs">
        <div class="flex items-center gap-3">
          <div class="flex bg-[#161D26] p-0.5 rounded-lg border border-[#232D3B]">
            <button id="timeline-mode-word" class="px-3 py-1 rounded font-semibold text-[11px] bg-[#00C48C] text-black">WORD</button>
            <button id="timeline-mode-line" class="px-3 py-1 rounded font-medium text-[11px] text-[#9CA3AF] hover:text-white">LINE</button>
          </div>
          <button id="btn-add-word" class="flex items-center gap-1 px-2.5 py-1 bg-[#1A222C] hover:bg-[#242F3D] border border-[#2A3543] rounded text-white font-medium text-[11px]" title="Add new word at current time">
            <span>+ Word</span>
          </button>
          <button id="btn-split-word" title="Split line at playhead" class="p-1 text-[#9CA3AF] hover:text-white rounded hover:bg-[#1E2632]">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z"/></svg>
          </button>
          <button id="btn-magnet" title="Magnet Snapping" class="p-1 text-[#00C48C] rounded hover:bg-[#1E2632]">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C8.69 2 6 4.69 6 8v6c0 3.31 2.69 6 6 6s6-2.69 6-6V8c0-3.31-2.69-6-6-6zm4 12c0 2.21-1.79 4-4 4s-4-1.79-4-4V8c0-2.21 1.79-4 4-4s4 1.79 4 4v6z"/></svg>
          </button>
        </div>

        <div class="flex items-center gap-3">
          <span class="text-[#6B7280] text-[11px]">Zoom:</span>
          <button id="btn-zoom-out" class="text-[#9CA3AF] hover:text-white p-0.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4"/></svg>
          </button>
          <input id="timeline-zoom-slider" type="range" min="0.5" max="3.5" step="0.1" value="1.0" class="w-20 accent-[#00C48C] h-1.5 bg-[#232D3B] rounded cursor-pointer" />
          <button id="btn-zoom-in" class="text-[#9CA3AF] hover:text-white p-0.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          </button>
        </div>
      </div>

      <div class="relative flex-1 overflow-x-auto overflow-y-hidden bg-[#0A0D11] select-none" id="timeline-scroll-area">
        <div id="timeline-track-wrapper" class="relative h-full" style="min-width: 100%; width: 1200px;">
          <!-- Time Rulers -->
          <div id="timeline-ruler" class="h-6 border-b border-[#1A222C] flex items-center text-[10px] text-[#6B7280] relative"></div>

          <!-- Track 1: Captions Track -->
          <div class="flex items-center h-9 border-b border-[#161D26] relative">
            <div class="w-20 px-3 flex items-center gap-1 text-[11px] font-semibold text-[#F59E0B] shrink-0 sticky left-0 z-20 bg-[#0A0D11]/90 backdrop-blur">
              <span>✨ Captions</span>
            </div>
            <div id="captions-track-content" class="relative flex-1 h-full"></div>
          </div>

          <!-- Track 2: Video Track -->
          <div class="flex items-center h-8 border-b border-[#161D26] relative">
            <div class="w-20 px-3 flex items-center gap-1 text-[11px] font-medium text-[#38BDF8] shrink-0 sticky left-0 z-20 bg-[#0A0D11]/90 backdrop-blur">
              <span>📹 Video 1</span>
            </div>
            <div id="video-track-content" class="relative flex-1 h-full flex items-center">
              <div id="timeline-video-name" class="h-6 w-full bg-[#0284C7]/20 border border-[#0284C7]/40 rounded flex items-center px-2 text-[10px] text-[#38BDF8] truncate">
                ${this.videoFilename}
              </div>
            </div>
          </div>

          <!-- Track 3: Audio Track with Real Decoded Waveform -->
          <div class="flex items-center h-10 relative">
            <div class="w-20 px-3 flex items-center gap-1 text-[11px] font-medium text-[#10B981] shrink-0 sticky left-0 z-20 bg-[#0A0D11]/90 backdrop-blur">
              <span>🔊 Audio 1</span>
            </div>
            <div id="audio-track-content" class="relative flex-1 h-full flex items-center">
              <div id="audio-waveform-container" class="h-8 w-full bg-[#059669]/15 border border-[#059669]/30 rounded overflow-hidden flex items-center gap-0.5 px-1">
                <!-- Generated or Decoded Waveform Bars -->
              </div>
            </div>
          </div>

          <!-- Red Playhead Scrubber -->
          <div id="timeline-playhead" class="timeline-playhead" style="left: 80px;"></div>
        </div>
      </div>
    `;

    this.rulerEl = document.getElementById('timeline-ruler');
    this.trackWrapperEl = document.getElementById('timeline-track-wrapper');
    this.captionsTrackEl = document.getElementById('captions-track-content');
    this.audioWaveformEl = document.getElementById('audio-waveform-container');
    this.playheadEl = document.getElementById('timeline-playhead');
    this.scrollAreaEl = document.getElementById('timeline-scroll-area');
    this.initVerticalResizer();
    this.generateWaveformBars();
  }

  initVerticalResizer() {
    const handle = document.getElementById('timeline-resizer-handle');
    if (!handle || !this.container) return;

    let isResizing = false;
    let startY = 0;
    let startHeight = 0;

    handle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      isResizing = true;
      startY = e.clientY;
      startHeight = this.container.getBoundingClientRect().height;
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';

      const onMouseMove = (moveEvt) => {
        if (!isResizing) return;
        const deltaY = startY - moveEvt.clientY; // dragging up increases height
        const newHeight = Math.max(130, Math.min(500, startHeight + deltaY));
        this.container.style.height = `${newHeight}px`;
      };

      const onMouseUp = () => {
        isResizing = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    });
  }

  setVideoFilename(name) {
    this.videoFilename = name || 'video.mp4';
    if (this.videoNameEl) {
      this.videoNameEl.textContent = this.videoFilename;
    }
  }

  async extractRealAudioWaveform(videoUrl) {
    if (!videoUrl) return;
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const response = await fetch(videoUrl);
      const arrayBuffer = await response.arrayBuffer();
      const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
      
      const rawData = audioBuffer.getChannelData(0);
      const totalSamples = Math.max(100, Math.floor((this.duration || 30) * 12 * this.zoom));
      const blockSize = Math.floor(rawData.length / totalSamples);
      const peaks = [];

      for (let i = 0; i < totalSamples; i++) {
        const start = blockSize * i;
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(rawData[start + j] || 0);
        }
        peaks.push(sum / Math.max(1, blockSize));
      }

      // Normalize peaks
      const maxPeak = Math.max(...peaks) || 1;
      this.audioPeaks = peaks.map(p => Math.max(4, Math.round((p / maxPeak) * 24)));
      this.renderWaveform();
    } catch (e) {
      console.log("Real audio decode fallback to simulated waveform:", e);
      this.generateWaveformBars();
    }
  }

  renderWaveform() {
    if (!this.audioWaveformEl) return;
    if (this.audioPeaks && this.audioPeaks.length) {
      let html = '';
      this.audioPeaks.forEach(h => {
        html += `<div class="w-1 bg-[#10B981] rounded-full opacity-80 shrink-0" style="height: ${h}px;"></div>`;
      });
      this.audioWaveformEl.innerHTML = html;
    } else {
      this.generateWaveformBars();
    }
  }

  generateWaveformBars() {
    let barsHtml = '';
    const numBars = Math.max(100, Math.floor((this.duration || 30) * 10 * this.zoom));
    for (let i = 0; i < numBars; i++) {
      const height = Math.floor(Math.sin(i * 0.25) * 12 + Math.cos(i * 0.15) * 10 + 14);
      barsHtml += `<div class="w-1 bg-[#10B981] rounded-full opacity-70 shrink-0" style="height: ${Math.max(4, height)}px;"></div>`;
    }
    if (this.audioWaveformEl) {
      this.audioWaveformEl.innerHTML = barsHtml;
    }
  }

  setDuration(duration) {
    if (!duration || isNaN(duration) || duration <= 0) return;
    this.duration = duration;
    this.updateDimensions();
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
    }
    this.updateDimensions();
  }

  updateDimensions() {
    if (!this.trackWrapperEl) return;
    const totalWidth = Math.max(800, (this.duration * this.pixelsPerSecond * this.zoom) + 120);
    this.trackWrapperEl.style.width = `${totalWidth}px`;
    this.renderRuler();
    this.renderCaptionBlocks();
    this.renderWaveform();
  }

  renderRuler() {
    if (!this.rulerEl) return;
    this.rulerEl.innerHTML = '';
    
    // Adaptive step size based on duration and zoom
    let step = 1.0;
    if (this.duration > 300) step = 10.0;
    else if (this.duration > 120) step = 5.0;
    else if (this.duration > 60) step = 2.0;
    else if (this.zoom > 1.5) step = 0.5;

    const offsetLeft = 80;

    for (let t = 0; t <= this.duration + 0.05; t += step) {
      const x = offsetLeft + (t * this.pixelsPerSecond * this.zoom);
      const marker = document.createElement('div');
      marker.className = 'absolute top-0 bottom-0 flex flex-col justify-end';
      marker.style.left = `${x}px`;
      
      const mm = Math.floor(t / 60);
      const ss = Math.floor(t % 60);
      const ms = Math.round((t % 1) * 10);
      const label = `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.${ms}`;

      marker.innerHTML = `
        <span class="text-[9px] text-[#6B7280] leading-none mb-1 select-none">${label}</span>
        <div class="h-2 w-[1px] bg-[#232D3B]"></div>
      `;
      this.rulerEl.appendChild(marker);
    }
  }

  renderCaptionBlocks() {
    if (!this.captionsTrackEl) return;
    this.captionsTrackEl.innerHTML = '';

    if (this.mode === 'word') {
      this.segments.forEach(seg => {
        (seg.words || []).forEach(w => {
          const startX = (w.start * this.pixelsPerSecond * this.zoom);
          const blockWidth = Math.max(32, ((w.end - w.start) * this.pixelsPerSecond * this.zoom) - 2);

          const block = document.createElement('div');
          block.className = 'caption-block flex items-center justify-between group/block relative cursor-grab active:cursor-grabbing select-none';
          block.style.left = `${startX}px`;
          block.style.width = `${blockWidth}px`;
          block.title = `${w.word} (${w.start}s - ${w.end}s)\n• Drag block to move timing\n• Drag green edges to trim duration\n• Double click to edit text & time`;

          // Left trim handle
          const leftHandle = document.createElement('div');
          leftHandle.className = 'absolute left-0 top-0 bottom-0 w-2.5 cursor-ew-resize hover:bg-[#00C48C] bg-[#00C48C]/40 opacity-0 group-hover/block:opacity-100 transition z-20 rounded-l';
          
          // Center word text
          const textSpan = document.createElement('span');
          textSpan.className = 'truncate px-1.5 pointer-events-none text-[10px] font-bold text-white';
          textSpan.textContent = `${w.word}${w.emoji ? ' ' + w.emoji : ''}`;

          // Right trim handle
          const rightHandle = document.createElement('div');
          rightHandle.className = 'absolute right-0 top-0 bottom-0 w-2.5 cursor-ew-resize hover:bg-[#00C48C] bg-[#00C48C]/40 opacity-0 group-hover/block:opacity-100 transition z-20 rounded-r';

          block.appendChild(leftHandle);
          block.appendChild(textSpan);
          block.appendChild(rightHandle);

          // Double click: Quick edit modal
          block.addEventListener('dblclick', (e) => {
            e.stopPropagation();
            const newText = prompt(`Edit Word & Timings\nWord text:`, w.word);
            if (newText !== null && newText.trim() !== '') {
              w.word = newText.trim();
              this.renderCaptionBlocks();
              this.player.render();
              if (window.kalakarEditor?.renderTranscriptList) window.kalakarEditor.renderTranscriptList();
            }
          });

          // Single click: seek
          block.addEventListener('click', (e) => {
            e.stopPropagation();
            this.player.seek(w.start);
            if (window.kalakarEditor) {
              window.kalakarEditor.highlightWordInTranscript(w);
            }
          });

          // 1. Whole Block Drag-and-Move
          block.addEventListener('mousedown', (e) => {
            if (e.target === leftHandle || e.target === rightHandle) return;
            e.stopPropagation();
            const startMouseX = e.clientX;
            const originalStart = w.start;
            const originalEnd = w.end;
            const blockDur = originalEnd - originalStart;

            const onMouseMove = (moveEvt) => {
              const deltaX = moveEvt.clientX - startMouseX;
              const deltaSec = deltaX / (this.pixelsPerSecond * this.zoom);
              const newStart = Math.max(0, Math.min(this.duration - blockDur, originalStart + deltaSec));
              w.start = Math.round(newStart * 100) / 100;
              w.end = Math.round((w.start + blockDur) * 100) / 100;
              this.renderCaptionBlocks();
              this.player.render();
            };

            const onMouseUp = () => {
              window.removeEventListener('mousemove', onMouseMove);
              window.removeEventListener('mouseup', onMouseUp);
              if (window.kalakarEditor?.pushStateToHistory) {
                window.kalakarEditor.pushStateToHistory();
              }
            };

            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
          });

          // 2. Trim Left Handle Drag
          leftHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            const startMouseX = e.clientX;
            const originalStart = w.start;

            const onMouseMove = (moveEvt) => {
              const deltaX = moveEvt.clientX - startMouseX;
              const deltaSec = deltaX / (this.pixelsPerSecond * this.zoom);
              w.start = Math.max(0, Math.min(w.end - 0.08, Math.round((originalStart + deltaSec) * 100) / 100));
              this.renderCaptionBlocks();
              this.player.render();
            };

            const onMouseUp = () => {
              window.removeEventListener('mousemove', onMouseMove);
              window.removeEventListener('mouseup', onMouseUp);
              if (window.kalakarEditor?.pushStateToHistory) {
                window.kalakarEditor.pushStateToHistory();
              }
            };

            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
          });

          // 3. Trim Right Handle Drag
          rightHandle.addEventListener('mousedown', (e) => {
            e.stopPropagation();
            const startMouseX = e.clientX;
            const originalEnd = w.end;

            const onMouseMove = (moveEvt) => {
              const deltaX = moveEvt.clientX - startMouseX;
              const deltaSec = deltaX / (this.pixelsPerSecond * this.zoom);
              w.end = Math.max(w.start + 0.08, Math.min(this.duration, Math.round((originalEnd + deltaSec) * 100) / 100));
              this.renderCaptionBlocks();
              this.player.render();
            };

            const onMouseUp = () => {
              window.removeEventListener('mousemove', onMouseMove);
              window.removeEventListener('mouseup', onMouseUp);
              if (window.kalakarEditor?.pushStateToHistory) {
                window.kalakarEditor.pushStateToHistory();
              }
            };

            window.addEventListener('mousemove', onMouseMove);
            window.addEventListener('mouseup', onMouseUp);
          });

          this.captionsTrackEl.appendChild(block);
        });
      });
    } else {
      // Line mode
      this.segments.forEach(seg => {
        const startX = (seg.start * this.pixelsPerSecond * this.zoom);
        const blockWidth = Math.max(40, ((seg.end - seg.start) * this.pixelsPerSecond * this.zoom) - 4);

        const block = document.createElement('div');
        block.className = 'caption-block flex items-center px-1.5 cursor-grab active:cursor-grabbing';
        block.style.left = `${startX}px`;
        block.style.width = `${blockWidth}px`;
        block.innerHTML = `<span class="truncate text-[10px] font-bold select-none text-white">${seg.text}</span>`;

        block.addEventListener('click', (e) => {
          e.stopPropagation();
          this.player.seek(seg.start);
        });

        this.captionsTrackEl.appendChild(block);
      });
    }
  }

  updatePlayhead(timeInSeconds) {
    if (!this.playheadEl) return;
    const offsetLeft = 80;
    const x = offsetLeft + (timeInSeconds * this.pixelsPerSecond * this.zoom);
    this.playheadEl.style.left = `${x}px`;
  }

  initEvents() {
    // Click and continuous drag scrubbing on timeline
    let isScrubbing = false;

    const handleSeek = (clientX) => {
      const rect = this.trackWrapperEl.getBoundingClientRect();
      const clickX = clientX - rect.left - 80;
      if (clickX >= 0) {
        const targetTime = Math.max(0, Math.min(this.duration, clickX / (this.pixelsPerSecond * this.zoom)));
        this.player.seek(targetTime);
      }
    };

    this.scrollAreaEl.addEventListener('mousedown', (e) => {
      if (e.target.closest('.caption-block')) return; // caption blocks handle their own drags
      isScrubbing = true;
      handleSeek(e.clientX);
    });

    window.addEventListener('mousemove', (e) => {
      if (isScrubbing) {
        handleSeek(e.clientX);
      }
    });

    window.addEventListener('mouseup', () => {
      if (isScrubbing) {
        isScrubbing = false;
      }
    });

    // Zoom controls
    const zoomSlider = document.getElementById('timeline-zoom-slider');
    const zoomInBtn = document.getElementById('btn-zoom-in');
    const zoomOutBtn = document.getElementById('btn-zoom-out');

    if (zoomSlider) {
      zoomSlider.addEventListener('input', (e) => {
        this.zoom = parseFloat(e.target.value);
        this.updateDimensions();
        this.updatePlayhead(this.player.currentTime);
      });
    }

    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', () => {
        this.zoom = Math.min(3.0, this.zoom + 0.3);
        if (zoomSlider) zoomSlider.value = this.zoom;
        this.updateDimensions();
        this.updatePlayhead(this.player.currentTime);
      });
    }

    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', () => {
        this.zoom = Math.max(0.5, this.zoom - 0.3);
        if (zoomSlider) zoomSlider.value = this.zoom;
        this.updateDimensions();
        this.updatePlayhead(this.player.currentTime);
      });
    }

    // Mode toggles
    const wordModeBtn = document.getElementById('timeline-mode-word');
    const lineModeBtn = document.getElementById('timeline-mode-line');

    if (wordModeBtn && lineModeBtn) {
      wordModeBtn.addEventListener('click', () => {
        this.mode = 'word';
        wordModeBtn.className = 'px-3 py-1 rounded font-semibold text-[11px] bg-[#00C48C] text-black';
        lineModeBtn.className = 'px-3 py-1 rounded font-medium text-[11px] text-[#9CA3AF] hover:text-white';
        this.renderCaptionBlocks();
      });

      lineModeBtn.addEventListener('click', () => {
        this.mode = 'line';
        lineModeBtn.className = 'px-3 py-1 rounded font-semibold text-[11px] bg-[#00C48C] text-black';
        wordModeBtn.className = 'px-3 py-1 rounded font-medium text-[11px] text-[#9CA3AF] hover:text-white';
        this.renderCaptionBlocks();
      });
    }

    // Add Word Button
    const addWordBtn = document.getElementById('btn-add-word');
    if (addWordBtn) {
      addWordBtn.addEventListener('click', () => {
        const wordText = prompt('Naya word daalein:');
        if (!wordText || !wordText.trim()) return;

        if (window.kalakarEditor?.pushStateToHistory) {
          window.kalakarEditor.pushStateToHistory();
        }

        const curTime = this.player.currentTime;
        const newWord = {
          word: wordText.trim(),
          start: Math.round(curTime * 100) / 100,
          end: Math.round((curTime + 0.5) * 100) / 100,
          highlight: false
        };

        // Find or create segment around current time
        let seg = this.segments.find(s => curTime >= s.start && curTime <= s.end);
        if (seg) {
          seg.words = seg.words || [];
          seg.words.push(newWord);
          seg.words.sort((a, b) => a.start - b.start);
          seg.text = seg.words.map(w => w.word).join(' ');
        } else {
          seg = {
            id: this.segments.length + 1,
            start: newWord.start,
            end: newWord.end,
            text: newWord.word,
            words: [newWord]
          };
          this.segments.push(seg);
          this.segments.sort((a, b) => a.start - b.start);
        }

        this.render();
        if (window.kalakarEditor) window.kalakarEditor.setSegments(this.segments);
        if (this.player) this.player.render();
        if (window.showToast) window.showToast(`✨ Word "${newWord.word}" add ho gaya!`);
      });
    }

    // Split Line Button
    const splitBtn = document.getElementById('btn-split-word');
    if (splitBtn) {
      splitBtn.addEventListener('click', () => {
        const curTime = this.player.currentTime;
        const segIdx = this.segments.findIndex(s => curTime >= s.start && curTime <= s.end);
        if (segIdx < 0) {
          if (window.showToast) window.showToast('Split karne ke liye playhead ko kisi caption ke upar rakhein.', true);
          return;
        }

        if (window.kalakarEditor?.pushStateToHistory) {
          window.kalakarEditor.pushStateToHistory();
        }

        const seg = this.segments[segIdx];
        const words = seg.words || [];
        const splitIdx = words.findIndex(w => curTime <= w.end);

        if (splitIdx <= 0 || splitIdx >= words.length) {
          if (window.showToast) window.showToast('Caption line ko beech se split karein.', true);
          return;
        }

        const firstWords = words.slice(0, splitIdx);
        const secondWords = words.slice(splitIdx);

        const firstSeg = {
          id: seg.id,
          start: firstWords[0].start,
          end: firstWords[firstWords.length - 1].end,
          text: firstWords.map(w => w.word).join(' '),
          words: firstWords
        };

        const secondSeg = {
          id: seg.id + 1,
          start: secondWords[0].start,
          end: secondWords[secondWords.length - 1].end,
          text: secondWords.map(w => w.word).join(' '),
          words: secondWords
        };

        this.segments.splice(segIdx, 1, firstSeg, secondSeg);
        this.segments.forEach((s, i) => s.id = i + 1);

        this.render();
        if (window.kalakarEditor) window.kalakarEditor.setSegments(this.segments);
        if (this.player) this.player.render();
        if (window.showToast) window.showToast('✂️ Caption line split ho gayi!');
      });
    }
  }

  render() {
    this.updateDimensions();
  }
}

window.KalakarTimeline = KalakarTimeline;
