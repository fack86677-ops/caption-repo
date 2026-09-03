// Inspector Styling Controls, Transcript List Editor, and Export Modal for Harsh Caption Generator

class KalakarEditor {
  constructor(player, timeline) {
    this.player = player;
    this.timeline = timeline;
    this.segments = [];
    this.selectedWord = null;
    this.historyStack = [];
    this.redoStack = [];

    this.initLeftTabs();
    this.initCustomFontUploader();
    this.initInspectorDOM();
    this.initTranscriptDOM();
    this.initTemplatesGrid();
    this.initExportModal();
    this.initHistoryAndShortcuts();
    this.loadSavedFonts();
  }

  setSegments(segments) {
    this.segments = segments || [];
    this.renderTranscriptList();
  }

  pushStateToHistory() {
    if (this.segments && this.segments.length) {
      this.historyStack.push(JSON.parse(JSON.stringify(this.segments)));
      if (this.historyStack.length > 40) this.historyStack.shift();
      this.redoStack = [];
      this.updateUndoRedoUI();
    }
  }

  undo() {
    if (this.historyStack.length > 0) {
      this.redoStack.push(JSON.parse(JSON.stringify(this.segments)));
      this.segments = this.historyStack.pop();
      this.applyStateChange();
      if (window.showToast) window.showToast('↶ Action Undone');
    } else {
      if (window.showToast) window.showToast('No more actions to undo');
    }
  }

  redo() {
    if (this.redoStack.length > 0) {
      this.historyStack.push(JSON.parse(JSON.stringify(this.segments)));
      this.segments = this.redoStack.pop();
      this.applyStateChange();
      if (window.showToast) window.showToast('↷ Action Redone');
    } else {
      if (window.showToast) window.showToast('No more actions to redo');
    }
  }

  applyStateChange() {
    this.renderTranscriptList();
    if (this.timeline) this.timeline.setSegments(this.segments);
    if (this.player) this.player.setSegments(this.segments);
    this.updateUndoRedoUI();
    if (window.saveCurrentProject) window.saveCurrentProject();
  }

  updateUndoRedoUI() {
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    if (undoBtn) undoBtn.style.opacity = this.historyStack.length > 0 ? '1' : '0.4';
    if (redoBtn) redoBtn.style.opacity = this.redoStack.length > 0 ? '1' : '0.4';
  }

  initHistoryAndShortcuts() {
    const undoBtn = document.getElementById('btn-undo');
    const redoBtn = document.getElementById('btn-redo');
    const shortcutsBtn = document.getElementById('btn-open-shortcuts');
    const shortcutsModal = document.getElementById('modal-shortcuts');
    const closeShortcutsBtn = document.getElementById('btn-close-shortcuts');

    if (undoBtn) undoBtn.addEventListener('click', () => this.undo());
    if (redoBtn) redoBtn.addEventListener('click', () => this.redo());

    if (shortcutsBtn && shortcutsModal) {
      shortcutsBtn.addEventListener('click', () => shortcutsModal.classList.remove('hidden'));
    }
    if (closeShortcutsBtn && shortcutsModal) {
      closeShortcutsBtn.addEventListener('click', () => shortcutsModal.classList.add('hidden'));
    }

    window.addEventListener('keydown', (e) => {
      // Don't trigger if user is typing in input or contenteditable
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) return;

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey) {
        e.preventDefault();
        this.undo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) {
        e.preventDefault();
        this.redo();
      } else if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        if (shortcutsModal) shortcutsModal.classList.toggle('hidden');
      }
    });

    this.updateUndoRedoUI();
  }

  initLeftTabs() {
    const tabs = [
      { btn: 'left-tab-captions', content: 'left-content-captions' },
      { btn: 'left-tab-fonts', content: 'left-content-fonts' },
      { btn: 'left-tab-library', content: 'left-content-library' }
    ];

    tabs.forEach(t => {
      const btnEl = document.getElementById(t.btn);
      const contentEl = document.getElementById(t.content);
      if (btnEl && contentEl) {
        btnEl.addEventListener('click', () => {
          tabs.forEach(x => {
            const b = document.getElementById(x.btn);
            const c = document.getElementById(x.content);
            if (b) {
              b.className = 'flex-1 py-2.5 text-xs font-medium text-[#9CA3AF] hover:text-white flex items-center justify-center gap-1.5 border-b-2 border-transparent';
            }
            if (c) c.classList.add('hidden');
          });
          btnEl.className = 'flex-1 py-2.5 text-xs font-semibold text-[#00C48C] border-b-2 border-[#00C48C] flex items-center justify-center gap-1.5';
          contentEl.classList.remove('hidden');
        });
      }
    });

    window.applyFontDirectly = (fontName) => {
      if (this.player) {
        this.player.setStyle({ fontFamily: fontName });
        const fontSelect = document.getElementById('input-font-family');
        if (fontSelect) fontSelect.value = fontName;
        if (window.showToast) window.showToast(`Font applied: <b>${fontName}</b>`);
      }
    };
  }

  loadSavedFonts() {
    try {
      const saved = JSON.parse(localStorage.getItem('hcg_custom_fonts') || '[]');
      saved.forEach(f => {
        if (f.name && f.data) {
          const newStyle = document.createElement('style');
          newStyle.appendChild(document.createTextNode(`
            @font-face {
              font-family: '${f.name}';
              src: url('${f.data}');
            }
          `));
          document.head.appendChild(newStyle);

          const fontSelect = document.getElementById('input-font-family');
          if (fontSelect) {
            const opt = document.createElement('option');
            opt.value = f.name;
            opt.textContent = `Custom: ${f.name}`;
            fontSelect.prepend(opt);
          }
        }
      });
    } catch (e) {
      console.log('Saved fonts load note:', e);
    }
  }

  initCustomFontUploader() {
    const fileInput = document.getElementById('font-file-input');
    if (!fileInput) return;

    fileInput.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const fontName = file.name.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9]/g, "");
      const reader = new FileReader();

      reader.onload = (re) => {
        const fontData = re.target.result;

        // Save to localStorage
        try {
          const saved = JSON.parse(localStorage.getItem('hcg_custom_fonts') || '[]');
          if (!saved.find(x => x.name === fontName)) {
            saved.push({ name: fontName, data: fontData });
            localStorage.setItem('hcg_custom_fonts', JSON.stringify(saved));
          }
        } catch (err) {
          console.warn('Font storage error:', err);
        }

        // Create font-face dynamically
        const newStyle = document.createElement('style');
        newStyle.appendChild(document.createTextNode(`
          @font-face {
            font-family: '${fontName}';
            src: url('${fontData}');
          }
        `));
        document.head.appendChild(newStyle);

        // Add to select dropdown
        const fontSelect = document.getElementById('input-font-family');
        if (fontSelect) {
          const opt = document.createElement('option');
          opt.value = fontName;
          opt.textContent = `Custom: ${fontName}`;
          opt.selected = true;
          fontSelect.prepend(opt);
        }

        if (this.player) {
          this.player.setStyle({ fontFamily: fontName });
        }

        if (window.showToast) window.showToast(`✨ Custom font <b>${fontName}</b> loaded & saved!`);
      };

      reader.readAsDataURL(file);
    });
  }

  initExportModal() {
    const exportBtn = document.getElementById('btn-open-export');
    const modal = document.getElementById('modal-export');
    const closeBtn = document.getElementById('btn-close-export');
    const confirmExportBtn = document.getElementById('btn-confirm-export');

    if (exportBtn && modal) {
      exportBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
      });
    }

    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
    }

    if (confirmExportBtn) {
      confirmExportBtn.addEventListener('click', async () => {
        const exportType = document.querySelector('input[name="export-format"]:checked')?.value || 'mp4';
        const exportRes = document.querySelector('input[name="export-res"]:checked')?.value || '1080p';

        confirmExportBtn.disabled = true;
        confirmExportBtn.innerHTML = `
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-black inline" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg> Rendering ${exportRes.toUpperCase()}...
        `;

        try {
          const res = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: exportType,
              resolution: exportRes,
              segments: this.segments,
              file_path: window.currentProject?.file_path || '',
              style: this.player.currentStyle
            })
          });

          const data = await res.json();
          if (data.success) {
            // Trigger automatic download
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = data.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            modal.classList.add('hidden');
            if (window.showToast) {
              window.showToast(`🎉 Exported successfully: <b>${data.filename}</b>`);
            } else {
              alert(`🎉 Exported successfully! File: ${data.filename}`);
            }
          } else {
            if (window.showToast) {
              window.showToast('Export error: ' + (data.error || 'Failed to render'), true);
            } else {
              alert('Export error: ' + (data.error || 'Failed to render'));
            }
          }
        } catch (err) {
          if (window.showToast) {
            window.showToast('Network error: ' + err.message, true);
          } else {
            alert('Network error: ' + err.message);
          }
        } finally {
          confirmExportBtn.disabled = false;
          confirmExportBtn.innerHTML = `
            <span>Download Now</span>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          `;
        }
      });
    }
  }

  initInspectorDOM() {
    // Tab switcher (Text, Templates, Transitions, AI Audio)
    const tabs = ['text', 'templates', 'transitions', 'audio'];
    tabs.forEach(tab => {
      const btn = document.getElementById(`tab-btn-${tab}`);
      const content = document.getElementById(`tab-content-${tab}`);
      if (btn && content) {
        btn.addEventListener('click', () => {
          tabs.forEach(t => {
            const b = document.getElementById(`tab-btn-${t}`);
            const c = document.getElementById(`tab-content-${t}`);
            if (b) b.className = 'px-3 py-2 text-xs font-medium text-[#9CA3AF] hover:text-white border-b-2 border-transparent';
            if (c) c.classList.add('hidden');
          });
          btn.className = 'px-3 py-2 text-xs font-semibold text-[#00C48C] border-b-2 border-[#00C48C]';
          content.classList.remove('hidden');
        });
      }
    });

    // Display Mode Controls (2-3 Words, 1 Word, Full Line)
    const btnChunk = document.getElementById('btn-display-chunk');
    const btnSingle = document.getElementById('btn-display-single');
    const btnFull = document.getElementById('btn-display-full');

    const updateDisplayModeBtns = (mode) => {
      if (btnChunk) btnChunk.className = mode === 'chunk' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
      if (btnSingle) btnSingle.className = mode === 'single' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
      if (btnFull) btnFull.className = mode === 'full' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
    };

    if (btnChunk) {
      btnChunk.addEventListener('click', () => {
        this.player.setStyle({ displayMode: 'chunk' });
        updateDisplayModeBtns('chunk');
      });
    }
    if (btnSingle) {
      btnSingle.addEventListener('click', () => {
        this.player.setStyle({ displayMode: 'single' });
        updateDisplayModeBtns('single');
      });
    }
    if (btnFull) {
      btnFull.addEventListener('click', () => {
        this.player.setStyle({ displayMode: 'full' });
        updateDisplayModeBtns('full');
      });
    }

    // Font controls
    const fontSelect = document.getElementById('input-font-family');
    const fontWeight = document.getElementById('input-font-weight');
    const fontSizeSlider = document.getElementById('slider-font-size');
    const fontSizeDisplay = document.getElementById('display-font-size');

    if (fontSelect) {
      fontSelect.addEventListener('change', (e) => {
        this.player.setStyle({ fontFamily: e.target.value });
      });
    }

    if (fontWeight) {
      fontWeight.addEventListener('change', (e) => {
        this.player.setStyle({ fontWeight: e.target.value });
      });
    }

    if (fontSizeSlider && fontSizeDisplay) {
      fontSizeSlider.addEventListener('input', (e) => {
        const val = parseInt(e.target.value);
        fontSizeDisplay.textContent = `${val} px`;
        this.player.setStyle({ fontSize: val });
      });
    }

    // Format (Case transform & alignment)
    const btnUpper = document.getElementById('btn-case-upper');
    const btnTitle = document.getElementById('btn-case-title');
    const btnLower = document.getElementById('btn-case-lower');

    if (btnUpper) btnUpper.addEventListener('click', () => this.player.setStyle({ textTransform: 'uppercase' }));
    if (btnTitle) btnTitle.addEventListener('click', () => this.player.setStyle({ textTransform: 'capitalize' }));
    if (btnLower) btnLower.addEventListener('click', () => this.player.setStyle({ textTransform: 'lowercase' }));

    const btnAlignLeft = document.getElementById('btn-align-left');
    const btnAlignCenter = document.getElementById('btn-align-center');
    const btnAlignRight = document.getElementById('btn-align-right');

    if (btnAlignLeft) btnAlignLeft.addEventListener('click', () => this.player.setStyle({ textAlign: 'left' }));
    if (btnAlignCenter) btnAlignCenter.addEventListener('click', () => this.player.setStyle({ textAlign: 'center' }));
    if (btnAlignRight) btnAlignRight.addEventListener('click', () => this.player.setStyle({ textAlign: 'right' }));

    // Position controls
    const posXInput = document.getElementById('input-pos-x');
    const posYInput = document.getElementById('input-pos-y');
    const btnResetPos = document.getElementById('btn-reset-pos');

    if (posXInput) {
      posXInput.addEventListener('change', (e) => {
        const val = parseFloat(e.target.value);
        this.player.setStyle({ posX: val });
      });
    }
    if (posYInput) {
      posYInput.addEventListener('change', (e) => {
        const val = parseFloat(e.target.value);
        this.player.setStyle({ posY: val });
      });
    }
    if (btnResetPos) {
      btnResetPos.addEventListener('click', () => {
        this.player.setStyle({ posX: 50, posY: 80 });
        this.updatePositionInputs(50, 80);
      });
    }

    // Color Pickers
    const primaryColorInput = document.getElementById('input-primary-color');
    if (primaryColorInput) {
      primaryColorInput.addEventListener('input', (e) => {
        this.player.setStyle({ color: e.target.value });
      });
    }

    // Emphasis Palette
    const emphasisBtns = document.querySelectorAll('.emphasis-color-btn');
    emphasisBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const color = btn.getAttribute('data-color');
        this.player.setStyle({ highlightColor: color });
        emphasisBtns.forEach(b => b.classList.remove('ring-2', 'ring-white'));
        btn.classList.add('ring-2', 'ring-white');
      });
    });

    // Effects: Stroke, Shadow, Background Box
    const strokeToggle = document.getElementById('toggle-stroke');
    const shadowToggle = document.getElementById('toggle-shadow');
    const bgBoxToggle = document.getElementById('toggle-bg-box');

    if (strokeToggle) {
      strokeToggle.addEventListener('change', (e) => {
        this.player.setStyle({ strokeWidth: e.target.checked ? 2 : 0 });
      });
    }
    if (shadowToggle) {
      shadowToggle.addEventListener('change', (e) => {
        this.player.setStyle({ shadow: e.target.checked });
      });
    }
    if (bgBoxToggle) {
      bgBoxToggle.addEventListener('change', (e) => {
        this.player.setStyle({ bgBox: e.target.checked, bgColor: 'rgba(0,0,0,0.75)' });
      });
    }
  }

  updatePositionInputs(x, y) {
    const posXInput = document.getElementById('input-pos-x');
    const posYInput = document.getElementById('input-pos-y');
    if (posXInput) posXInput.value = `${x.toFixed(1)} %`;
    if (posYInput) posYInput.value = `${y.toFixed(1)} %`;
  }

  initTemplatesGrid() {
    const grid = document.getElementById('templates-grid');
    if (!grid) return;

    grid.innerHTML = '';
    TEMPLATES.forEach(tpl => {
      const card = document.createElement('div');
      card.className = `template-card p-3 flex flex-col gap-2 ${tpl.id === 'hormozi' ? 'selected' : ''}`;
      card.id = `template-card-${tpl.id}`;
      
      card.innerHTML = `
        <div class="h-20 bg-[#0B0E12] rounded-lg flex items-center justify-center border border-[#1A222C] relative overflow-hidden">
          <span style="font-family: ${tpl.style.fontFamily}; font-weight: ${tpl.style.fontWeight}; color: ${tpl.style.color}; ${tpl.style.strokeWidth ? `-webkit-text-stroke: 1.5px ${tpl.style.strokeColor}; paint-order: stroke fill;` : ''} font-size: 15px; text-transform: ${tpl.style.textTransform};">
            <span style="color: ${tpl.style.highlightColor};">${tpl.previewText.split(' ')[0]}</span> ${tpl.previewText.split(' ').slice(1).join(' ')}
          </span>
        </div>
        <div class="flex items-center justify-between">
          <div>
            <div class="text-xs font-semibold text-white">${tpl.name}</div>
            <div class="text-[10px] text-[#6B7280]">${tpl.creator}</div>
          </div>
          <span class="w-2 h-2 rounded-full ${tpl.id === 'hormozi' ? 'bg-[#00C48C]' : 'bg-[#232D3B]'}"></span>
        </div>
      `;

      card.addEventListener('click', () => {
        document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        this.player.setStyle(tpl.style);
        this.syncInspectorControls(tpl.style);
      });

      grid.appendChild(card);
    });
  }

  syncInspectorControls(style) {
    const fontSelect = document.getElementById('input-font-family');
    const fontWeight = document.getElementById('input-font-weight');
    const fontSizeSlider = document.getElementById('slider-font-size');
    const fontSizeDisplay = document.getElementById('display-font-size');
    const strokeToggle = document.getElementById('toggle-stroke');
    const shadowToggle = document.getElementById('toggle-shadow');
    const bgBoxToggle = document.getElementById('toggle-bg-box');

    if (fontSelect && style.fontFamily) fontSelect.value = style.fontFamily;
    if (fontWeight && style.fontWeight) fontWeight.value = style.fontWeight;
    if (fontSizeSlider && style.fontSize) {
      fontSizeSlider.value = style.fontSize;
      if (fontSizeDisplay) fontSizeDisplay.textContent = `${style.fontSize} px`;
    }
    if (strokeToggle) strokeToggle.checked = (style.strokeWidth > 0);
    if (shadowToggle) shadowToggle.checked = !!style.shadow;
    if (bgBoxToggle) bgBoxToggle.checked = !!style.bgBox;
    if (style.posX && style.posY) this.updatePositionInputs(style.posX, style.posY);

    // Update display mode buttons
    const mode = style.displayMode || 'chunk';
    const btnChunk = document.getElementById('btn-display-chunk');
    const btnSingle = document.getElementById('btn-display-single');
    const btnFull = document.getElementById('btn-display-full');

    if (btnChunk) btnChunk.className = mode === 'chunk' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
    if (btnSingle) btnSingle.className = mode === 'single' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
    if (btnFull) btnFull.className = mode === 'full' ? 'py-1.5 px-2 rounded-lg text-[11px] font-semibold bg-[#00C48C] text-black transition' : 'py-1.5 px-2 rounded-lg text-[11px] font-medium text-[#9CA3AF] hover:text-white transition';
  }

  initTranscriptDOM() {
    const searchInput = document.getElementById('transcript-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        const items = document.querySelectorAll('.transcript-line-item');
        items.forEach(item => {
          const text = item.getAttribute('data-text').toLowerCase();
          item.style.display = text.includes(q) ? 'flex' : 'none';
        });
      });
    }
  }

  renderTranscriptList() {
    const listContainer = document.getElementById('transcript-list');
    if (!listContainer) return;

    listContainer.innerHTML = '';
    this.segments.forEach((seg, idx) => {
      const row = document.createElement('div');
      row.className = 'transcript-line-item flex items-start gap-3 p-2.5 rounded-lg hover:bg-[#151C24] border border-transparent hover:border-[#1F2732] transition group cursor-pointer';
      row.setAttribute('data-text', seg.text);
      row.setAttribute('data-seg-id', seg.id);

      // Line number
      const numSpan = document.createElement('div');
      numSpan.className = 'text-xs font-semibold text-[#6B7280] w-5 pt-0.5 select-none';
      numSpan.textContent = seg.id || (idx + 1);

      // Content with interactive clickable word chips
      const textContainer = document.createElement('div');
      textContainer.className = 'flex-1 flex flex-wrap gap-1.5 items-center';

      (seg.words || []).forEach(w => {
        const wordChip = document.createElement('span');
        wordChip.className = `px-2 py-0.5 rounded text-xs transition select-none flex items-center gap-1 cursor-pointer ${
          w.highlight 
            ? 'bg-[#00C48C]/20 text-[#00C48C] font-semibold border border-[#00C48C]/40' 
            : 'bg-[#1A222C] text-[#D1D5DB] hover:bg-[#26313F]'
        }`;
        wordChip.title = "Click to seek/highlight. Double click to edit.";
        wordChip.textContent = `${w.word}${w.emoji ? ' ' + w.emoji : ''}`;

        // Single click: seek and toggle highlight
        wordChip.addEventListener('click', (e) => {
          e.stopPropagation();
          this.player.seek(w.start);
          w.highlight = !w.highlight;
          this.renderTranscriptList();
          this.player.render();
        });

        // Double click: Edit word text
        wordChip.addEventListener('dblclick', (e) => {
          e.stopPropagation();
          const edited = prompt('Edit word text:', w.word);
          if (edited !== null && edited.trim() !== '') {
            w.word = edited.trim();
            seg.text = seg.words.map(x => x.word).join(' ');
            this.renderTranscriptList();
            this.player.render();
            if (this.timeline) this.timeline.render();
            if (window.showToast) window.showToast(`Word updated: "${w.word}"`);
          }
        });

        textContainer.appendChild(wordChip);
      });

      // Quick Actions (Split, Duplicate, Delete)
      const actions = document.createElement('div');
      actions.className = 'opacity-0 group-hover:opacity-100 flex items-center gap-1 shrink-0 transition text-[#9CA3AF]';

      const splitBtn = document.createElement('button');
      splitBtn.className = 'p-1 hover:text-white hover:bg-[#232D3B] rounded';
      splitBtn.title = 'Split line in two';
      splitBtn.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12M8 12h12M8 17h12M4 7h.01M4 12h.01M4 17h.01"/></svg>`;
      splitBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.splitSegment(idx);
      });

      const dupBtn = document.createElement('button');
      dupBtn.className = 'p-1 hover:text-white hover:bg-[#232D3B] rounded';
      dupBtn.title = 'Duplicate this line';
      dupBtn.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>`;
      dupBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.duplicateSegment(idx);
      });

      const delBtn = document.createElement('button');
      delBtn.className = 'p-1 hover:text-red-400 hover:bg-[#232D3B] rounded';
      delBtn.title = 'Delete this line';
      delBtn.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>`;
      delBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.deleteSegment(idx);
      });

      actions.appendChild(splitBtn);
      actions.appendChild(dupBtn);
      actions.appendChild(delBtn);

      row.appendChild(numSpan);
      row.appendChild(textContainer);
      row.appendChild(actions);

      row.addEventListener('click', () => {
        this.player.seek(seg.start);
      });

      listContainer.appendChild(row);
    });
  }

  splitSegment(idx) {
    const seg = this.segments[idx];
    const words = seg.words || [];
    if (words.length <= 1) {
      if (window.showToast) window.showToast('Is line mein kam se kam 2 words hone chahiye split karne ke liye.', true);
      return;
    }

    const mid = Math.floor(words.length / 2);
    const firstWords = words.slice(0, mid);
    const secondWords = words.slice(mid);

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

    this.segments.splice(idx, 1, firstSeg, secondSeg);
    this.segments.forEach((s, i) => s.id = i + 1);

    this.renderTranscriptList();
    if (this.timeline) this.timeline.setSegments(this.segments);
    this.player.render();
    if (window.showToast) window.showToast('✂️ Line split ho gayi!');
  }

  duplicateSegment(idx) {
    const seg = this.segments[idx];
    const newSeg = JSON.parse(JSON.stringify(seg));
    newSeg.start = Math.round((newSeg.end + 0.1) * 100) / 100;
    const dur = (seg.end - seg.start);
    newSeg.end = Math.round((newSeg.start + dur) * 100) / 100;

    let shift = newSeg.start - seg.start;
    (newSeg.words || []).forEach(w => {
      w.start = Math.round((w.start + shift) * 100) / 100;
      w.end = Math.round((w.end + shift) * 100) / 100;
    });

    this.segments.splice(idx + 1, 0, newSeg);
    this.segments.forEach((s, i) => s.id = i + 1);

    this.renderTranscriptList();
    if (this.timeline) this.timeline.setSegments(this.segments);
    this.player.render();
    if (window.showToast) window.showToast('📋 Line duplicate ho gayi!');
  }

  deleteSegment(idx) {
    const seg = this.segments[idx];
    if (confirm(`Kya aap line ${seg.id} delete karna chahte hain?`)) {
      this.segments.splice(idx, 1);
      this.segments.forEach((s, i) => s.id = i + 1);

      this.renderTranscriptList();
      if (this.timeline) this.timeline.setSegments(this.segments);
      this.player.render();
      if (window.showToast) window.showToast('🗑️ Line delete ho gayi!');
    }
  }

  highlightWordInTranscript(targetWord) {
    const chips = document.querySelectorAll('.transcript-line-item span');
    chips.forEach(chip => {
      if (chip.textContent.trim().startsWith(targetWord.word)) {
        chip.classList.add('ring-2', 'ring-[#FFE600]');
        setTimeout(() => chip.classList.remove('ring-2', 'ring-[#FFE600]'), 1200);
      }
    });
  }

  initExportModal() {
    const exportBtn = document.getElementById('btn-open-export');
    const modal = document.getElementById('modal-export');
    const closeBtn = document.getElementById('btn-close-export');
    const confirmExportBtn = document.getElementById('btn-confirm-export');

    if (exportBtn && modal) {
      exportBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
      });
    }

    if (closeBtn && modal) {
      closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
      });
    }

    if (confirmExportBtn) {
      confirmExportBtn.addEventListener('click', async () => {
        const exportType = document.querySelector('input[name="export-format"]:checked')?.value || 'mp4';
        confirmExportBtn.disabled = true;
        confirmExportBtn.innerHTML = `
          <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-black inline" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg> Rendering...
        `;

        try {
          const res = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: exportType,
              segments: this.segments,
              file_path: window.currentProject?.file_path || '',
              style: this.player.currentStyle
            })
          });

          const data = await res.json();
          if (data.success) {
            // Trigger automatic download
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = data.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            modal.classList.add('hidden');
            if (window.showToast) {
              window.showToast(`🎉 Exported successfully: <b>${data.filename}</b>`);
            } else {
              alert(`🎉 Exported successfully! File: ${data.filename}`);
            }
          } else {
            if (window.showToast) {
              window.showToast('Export error: ' + (data.error || 'Failed to render'), true);
            } else {
              alert('Export error: ' + (data.error || 'Failed to render'));
            }
          }
        } catch (err) {
          if (window.showToast) {
            window.showToast('Network error: ' + err.message, true);
          } else {
            alert('Network error: ' + err.message);
          }
        } finally {
          confirmExportBtn.disabled = false;
          confirmExportBtn.textContent = 'Download Now';
        }
      });
    }
  }
}

window.KalakarEditor = KalakarEditor;
