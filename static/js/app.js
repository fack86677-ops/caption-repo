// Main Application Controller for Harsh Caption Generator Studio

function getApiBase() {
  if (window.location.origin && window.location.origin.includes(':7860')) return '';
  return 'http://localhost:7860';
}
const API_BASE = getApiBase();

let currentProject = null;
let kalakarPlayer = null;
let kalakarTimeline = null;
let kalakarEditor = null;
let pendingUploadFile = null;

const DID_YOU_KNOW_TIPS = [
  "More than 200,000 creators and editors trust Harsh Caption Generator for fast viral captions.",
  "Adding animated captions increases video watch time and retention by over 80% on Instagram Reels and Shorts!",
  "Hinglish captions allow Indian creators to reach both regional and global youth audiences effortlessly.",
  "Word-level pop animations boost visual engagement and prevent users from scrolling away.",
  "You can drag and position your captions anywhere on the video in real-time!"
];

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initDropzone();
  initPrepareModal();
  initKeyboardShortcuts();
  loadRecentProjects();
});

function initKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Only if not typing in input or contenteditable
    const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
    const isEditing = activeTag === 'input' || activeTag === 'textarea' || document.activeElement?.isContentEditable;
    if (isEditing) return;

    if (e.code === 'Space') {
      e.preventDefault();
      window.toggleVideoPlayback();
    } else if (e.code === 'ArrowLeft') {
      e.preventDefault();
      if (kalakarPlayer) kalakarPlayer.seek(kalakarPlayer.currentTime - 1.0);
    } else if (e.code === 'ArrowRight') {
      e.preventDefault();
      if (kalakarPlayer) kalakarPlayer.seek(kalakarPlayer.currentTime + 1.0);
    }
  });
}

function initNavigation() {
  // Navigation back to dashboard
  const btnBackHome = document.getElementById('btn-back-home');
  if (btnBackHome) {
    btnBackHome.addEventListener('click', () => {
      showScreen('screen-dashboard');
      loadRecentProjects();
      if (window.setCredits && window.getCredits) {
        window.setCredits(window.getCredits());
      }
    });
  }

  // Safe zone toggle
  const safeZoneToggle = document.getElementById('btn-toggle-safe-zone');
  let safeZoneActive = false;
  if (safeZoneToggle) {
    safeZoneToggle.addEventListener('click', () => {
      safeZoneActive = !safeZoneActive;
      if (kalakarPlayer) kalakarPlayer.toggleSafeZone(safeZoneActive);
      safeZoneToggle.classList.toggle('text-[#00C48C]', safeZoneActive);
    });
  }

  // Project title editing
  const titleEl = document.getElementById('project-title-display');
  if (titleEl) {
    titleEl.addEventListener('blur', () => {
      if (currentProject) {
        currentProject.title = titleEl.textContent.trim() || 'Untitled Project';
        saveCurrentProject();
        if (window.showToast) window.showToast('Project title updated!');
      }
    });
  }
}

function showScreen(screenId) {
  document.querySelectorAll('.app-screen').forEach(s => s.classList.add('hidden'));
  const target = document.getElementById(screenId);
  if (target) target.classList.remove('hidden');
}

function initDropzone() {
  const dropzone = document.getElementById('main-dropzone');
  const fileInput = document.getElementById('file-upload-input');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', () => fileInput.click());

  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });
}

function handleFileSelected(file) {
  pendingUploadFile = file;
  // Open Screen 2: Prepare Your Media Modal
  const modal = document.getElementById('modal-prepare-media');
  const previewName = document.getElementById('prepare-file-name');
  if (previewName) previewName.textContent = `Selected: ${file.name}`;
  if (modal) modal.classList.remove('hidden');
}

function initPrepareModal() {
  const modal = document.getElementById('modal-prepare-media');
  const closeBtn = document.getElementById('btn-close-prepare');
  const generateBtn = document.getElementById('btn-generate-transcription');

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      modal.classList.add('hidden');
      pendingUploadFile = null;
    });
  }

  if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
      const language = document.getElementById('select-spoken-language')?.value || 'hi';
      const script = document.getElementById('select-writing-script')?.value || 'roman';
      const audioEnhance = document.getElementById('toggle-audio-enhance')?.checked ?? true;
      const emojis = document.getElementById('toggle-emojis')?.checked ?? true;
      const translate = document.getElementById('toggle-translation')?.checked ?? false;

      modal.classList.add('hidden');
      await startUploadAndTranscription(pendingUploadFile, { language, script, audioEnhance, emojis, translate });
    });
  }
}

async function startUploadAndTranscription(file, options) {
  const processingModal = document.getElementById('modal-processing');
  const progressBar = document.getElementById('processing-progress-bar');
  const progressText = document.getElementById('processing-progress-text');
  const statusSubtext = document.getElementById('processing-status-subtext');
  const triviaEl = document.getElementById('processing-trivia');

  if (processingModal) processingModal.classList.remove('hidden');
  if (triviaEl) {
    triviaEl.textContent = DID_YOU_KNOW_TIPS[Math.floor(Math.random() * DID_YOU_KNOW_TIPS.length)];
  }

  let progress = 10;
  const updateProgress = (val, text) => {
    progress = val;
    if (progressBar) progressBar.style.width = `${val}%`;
    if (progressText) progressText.textContent = `${val}%`;
    if (statusSubtext && text) statusSubtext.textContent = text;
  };

  updateProgress(15, "Uploading your video media...");

  try {
    let uploadData = null;

    if (file) {
      try {
        // Try real upload to backend
        const res = await fetch(API_BASE + '/api/upload', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/octet-stream',
            'X-File-Name': encodeURIComponent(file.name)
          },
          body: file
        });
        const text = await res.text();
        try {
          uploadData = JSON.parse(text);
        } catch(e) {
          console.warn('Backend upload returned non-JSON, switching to local Blob URL:', text.slice(0, 100));
        }
      } catch (err) {
        console.warn('Upload network error, using local Blob URL:', err);
      }

      // If backend is not available or returned HTML 404 (e.g. static Vercel deployment)
      if (!uploadData || !uploadData.success) {
        const blobUrl = URL.createObjectURL(file);
        const tempVid = document.createElement('video');
        tempVid.preload = 'metadata';
        tempVid.src = blobUrl;
        
        const dur = await new Promise(resolve => {
          tempVid.onloadedmetadata = () => resolve(tempVid.duration || 15.0);
          tempVid.onerror = () => resolve(15.0);
          setTimeout(() => resolve(15.0), 2500);
        });

        uploadData = {
          success: true,
          filename: file.name,
          video_url: blobUrl,
          file_path: '',
          info: { duration: dur, width: 1080, height: 1920 }
        };
      }
    } else {
      // Use demo sample video
      uploadData = {
        success: true,
        filename: "siblings_walking_into_hallway_202608271637.mp4",
        video_url: "/static/assets/demo_video.mp4",
        file_path: "",
        info: { duration: 14.5, width: 1080, height: 1920 }
      };
    }

    const duration = uploadData.info?.duration || 15.0;

    // Deduct user credits before proceeding
    if (window.HCG && window.HCG.deductCredits) {
      const allowed = window.HCG.deductCredits(duration);
      if (!allowed) {
        if (processingModal) processingModal.classList.add('hidden');
        return;
      }
    }

    updateProgress(55, options.translate ? "Translating audio to English captions..." : "Audio cleaning & AI transcription running...");

    // Call Transcription API safely
    let transData = null;
    if (uploadData.file_path) {
      try {
        const transRes = await fetch(API_BASE + '/api/transcribe', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            file_path: uploadData.file_path,
            language: options.language,
            script: options.script,
            audio_enhance: options.audioEnhance,
            emojis: options.emojis,
            translate: options.translate
          })
        });
        const transText = await transRes.text();
        try {
          transData = JSON.parse(transText);
        } catch(e) {
          console.warn('Transcribe returned non-JSON:', transText.slice(0, 100));
        }
      } catch (err) {
        console.warn('Transcribe fetch failed:', err);
      }
    }

    // Check if transcription returned real segments or error
    if (transData && transData.error) {
      console.warn('Transcription API message:', transData.error);
    }

    const realSegments = (transData && Array.isArray(transData.segments)) ? transData.segments : [];

    if (transData && transData.remaining_credits !== undefined) {
      localStorage.setItem('hcg_credits', String(transData.remaining_credits));
      const credDisplay = document.getElementById('header-credits');
      if (credDisplay) credDisplay.textContent = transData.remaining_credits;
      const sideCred = document.getElementById('sidebar-credits-display');
      if (sideCred) sideCred.textContent = transData.remaining_credits;
    }

    updateProgress(90, "Synchronizing word-level animations & templates...");
    await new Promise(r => setTimeout(r, 600));
    updateProgress(100, "Ready!");

    if (processingModal) processingModal.classList.add('hidden');

    // Launch Studio Editor with real project data
    const project = {
      id: `proj_${Date.now()}`,
      title: uploadData.filename.replace(/\.[^/.]+$/, ""),
      filename: uploadData.filename,
      video_url: uploadData.video_url,
      file_path: uploadData.file_path || '',
      created_at: "Just now",
      language: options.language === 'hi' ? (options.script === 'roman' ? 'Hinglish' : 'Hindi (Native)') : 'English',
      duration: duration,
      segments: realSegments,
      style: { ...TEMPLATES[0].style }
    };

    openStudioEditor(project);

  } catch (err) {
    console.error("Studio processing error:", err);
    if (window.showToast) {
      window.showToast("Note: " + err.message, true);
    }
    if (processingModal) processingModal.classList.add('hidden');
  }
}

function openStudioEditor(project) {
  currentProject = project;
  window.currentProject = project;

  showScreen('screen-studio');

  // Update Top Bar
  const titleDisplay = document.getElementById('project-title-display');
  if (titleDisplay) titleDisplay.textContent = project.title;

  const videoEl = document.getElementById('main-video-player');
  const captionOverlay = document.getElementById('caption-render-box');
  const safeZone = document.getElementById('safe-zone-box');

  let videoSrc = project.video_url;
  if (videoSrc && videoSrc.toLowerCase().endsWith('.mov')) {
    videoSrc = videoSrc.slice(0, -4) + '.mp4';
  }

  if (videoEl) {
    videoEl.pause();
    videoEl.currentTime = 0;
    videoEl.src = videoSrc;
    videoEl.load();
  }

  // Initialize Player
  kalakarPlayer = new KalakarPlayer(videoEl, captionOverlay, safeZone);
  window.kalakarPlayer = kalakarPlayer;

  // Initialize Timeline
  const timelineContainer = document.getElementById('timeline-container');
  kalakarTimeline = new KalakarTimeline(timelineContainer, kalakarPlayer);
  window.kalakarTimeline = kalakarTimeline;

  // Set initial duration & sync
  const initialDuration = project.duration || 30.0;
  kalakarPlayer.duration = initialDuration;
  kalakarTimeline.setDuration(initialDuration);
  kalakarTimeline.setVideoFilename(project.filename || project.title || 'video.mp4');

  kalakarPlayer.setSegments(project.segments);
  if (project.style) {
    kalakarPlayer.setStyle(project.style);
  }
  kalakarTimeline.setSegments(project.segments);
  kalakarTimeline.extractRealAudioWaveform(videoSrc);

  // Initialize Editor
  kalakarEditor = new KalakarEditor(kalakarPlayer, kalakarTimeline);
  kalakarEditor.setSegments(project.segments);
  window.kalakarEditor = kalakarEditor;

  // Listen to video element metadata load to dynamically adjust to exact video duration
  const onMetadata = () => {
    if (videoEl && videoEl.duration && !isNaN(videoEl.duration) && videoEl.duration > 0 && isFinite(videoEl.duration)) {
      project.duration = videoEl.duration;
      kalakarPlayer.duration = videoEl.duration;
      kalakarTimeline.setDuration(videoEl.duration);
      kalakarPlayer.updateTimeDisplay();
    }
  };

  if (videoEl) {
    videoEl.addEventListener('loadedmetadata', onMetadata);
    videoEl.addEventListener('durationchange', onMetadata);
    videoEl.addEventListener('canplay', onMetadata);
    videoEl.addEventListener('canplaythrough', onMetadata);
    videoEl.addEventListener('loadeddata', onMetadata);
    if (videoEl.readyState >= 1) {
      onMetadata();
    }
  }

  // Save to recent projects
  saveCurrentProject();
}

async function loadRecentProjects() {
  const container = document.getElementById('recent-videos-grid');
  if (!container) return;

  try {
    const res = await fetch(API_BASE + '/api/projects');
    const data = await res.json();
    const projects = data.projects || [];

    container.innerHTML = '';
    projects.forEach(proj => {
      const card = document.createElement('div');
      card.className = 'bg-[#141A21] hover:bg-[#1A222C] border border-[#1F2732] hover:border-[#374659] rounded-xl overflow-hidden cursor-pointer transition group flex flex-col';

      card.innerHTML = `
        <div class="relative aspect-[9/16] bg-[#0A0E13] flex items-center justify-center overflow-hidden">
          <img src="${proj.thumbnail || '/static/assets/demo_thumb.jpg'}" class="w-full h-full object-cover" onerror="this.src='/static/assets/demo_thumb.jpg'" />
          <div class="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition flex items-center justify-center">
            <div class="w-12 h-12 rounded-full bg-white/90 text-black flex items-center justify-center shadow-lg transform group-hover:scale-110 transition">
              <svg class="w-6 h-6 ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
            </div>
          </div>
          <div class="absolute bottom-3 left-3 right-3 h-4 border border-[#FFE600] rounded bg-black/40"></div>
        </div>
        <div class="p-3 flex items-start justify-between">
          <div class="flex-1 min-w-0 pr-2">
            <h4 class="text-sm font-semibold text-white group-hover:text-[#00C48C] transition truncate">${proj.title}</h4>
            <p class="text-xs text-[#6B7280] mt-0.5">${proj.created_at} • ${proj.language}</p>
          </div>
          <button class="btn-delete-proj text-[#6B7280] hover:text-red-400 p-1.5 rounded-lg hover:bg-[#232D3B] transition shrink-0" title="Delete Project">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      `;

      // Open project on card click
      card.addEventListener('click', () => {
        openStudioEditor(proj);
      });

      // Delete project on delete button click
      const delBtn = card.querySelector('.btn-delete-proj');
      if (delBtn) {
        delBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (confirm(`Kya aap project "${proj.title}" ko permanently delete karna chahte hain?`)) {
            try {
              await fetch(API_BASE + '/api/delete_project', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: proj.id })
              });
              if (window.showToast) window.showToast(`🗑️ Project "${proj.title}" delete ho gaya!`);
              loadRecentProjects();
            } catch (err) {
              alert("Delete error: " + err.message);
            }
          }
        });
      }

      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading recent projects:", err);
  }
}

async function saveCurrentProject() {
  if (!currentProject) return;
  const badge = document.getElementById('auto-save-badge');
  if (badge) {
    badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-[#F59E0B] animate-ping"></span><span>Saving...</span>`;
    badge.className = 'flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium text-[#F59E0B] bg-[#F59E0B]/10 border border-[#F59E0B]/25 ml-1';
  }

  try {
    currentProject.style = kalakarPlayer?.currentStyle || currentProject.style;
    currentProject.segments = kalakarEditor?.segments || currentProject.segments;
    await fetch(API_BASE + '/api/save_project', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentProject)
    });

    if (badge) {
      setTimeout(() => {
        badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse"></span><span>Saved ✓</span>`;
        badge.className = 'flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium text-[#10B981] bg-[#10B981]/10 border border-[#10B981]/25 ml-1';
      }, 300);
    }
  } catch (err) {
    console.error("Failed saving project:", err);
    if (badge) {
      badge.innerHTML = `<span class="text-red-400">Save failed</span>`;
    }
  }
}

// Global player trigger
window.toggleVideoPlayback = () => {
  if (kalakarPlayer) kalakarPlayer.togglePlay();
};
