# 🎬 Kalakar AI Caption & Subtitle Studio (Web App)

A modern, high-performance web application matching `https://app.kalakar.io/` for auto-generating viral, animated captions and subtitles for South Asian creators (Hindi, Hinglish, English, Punjabi, Bengali, Marathi, etc.).

---

## 🌟 Key Features

### 1. 🖥️ Screen 1: Dashboard View
* **Sidebar:** Home, Tutorials, Manage Subscription, Manage Plugins, Refer & Earn, Help & Support, and Desktop App launcher.
* **Usage Quota Widget:** Storage quota, remaining AI transcription minutes, audio clean counter.
* **Top Navigation:** Title search (`Ctrl+K`), Upgrade button, Aura credits balance, User profile avatar.
* **Media Dropzone:** Drag-and-drop video/audio upload box (`Max: 2:00 mins, 1GB`).
* **Recent Videos Grid:** Project cards with video thumbnails, play button overlay, creation date, language tags, and project management.

### 2. ⚙️ Screen 2: "Prepare Your Media" Modal
* **Media Preview:** Video preview thumbnail with live status indicator (`• Ready for processing`).
* **Language Settings:**
  * Spoken Language selector (Hindi/Hinglish, English, Punjabi, Marathi, Bengali, Tamil, Telugu, Gujarati, Urdu).
  * Writing System selector (Roman script / Hinglish vs Native Devanagari script).
* **AI Feature Toggles:**
  * English Translation toggle (Creator Plan).
  * AI Audio Enhancement (Clean background noise & echo).
  * Auto Emojis toggle (Smart contextual emoji insertion e.g. 🎁, ✨, 🔥, 🚀).

### 3. ⏳ Screen 3: Uploading & AI Processing Modal
* **Animated Graphics:** Glowing vector illustration with floating particles.
* **Progress Bar:** Real-time upload and transcription gradient progress bar (`0%` -> `100%`).
* **Creator Trivia / Tips:** Dynamic *"DID YOU KNOW?"* creator growth cards.

### 4. 🎨 Screen 4: Full Video & Caption Studio
* **Left Transcript Editor:** Line-by-line & word-by-word interactive transcript list. Click any word to seek the player to that timestamp, toggle word highlights, split lines, or edit spellings.
* **Center 9:16 Video Player Canvas:**
  * Real-time synchronized active-word highlighting.
  * Draggable caption overlay directly on video canvas.
  * Instagram / TikTok safe-zone overlay toggle.
  * Aspect Ratio selector (`9:16`, `16:9`, `1:1`).
  * Player controls (Play/Pause, Volume, Millisecond Timecode, Fullscreen).
* **Bottom Multi-Track Timeline:**
  * Mode Switch: `[WORD]` vs `[LINE]`
  * Track 1: Captions (timed interactive word blocks)
  * Track 2: Video stream track
  * Track 3: Audio waveform visualizer track
  * Millisecond playhead scrubber with zoom slider (`-` / `+`).
* **Right Inspector / Styling Panel:**
  * **FONTS:** Font family (`Inter`, `Montserrat`, `Poppins`, `Outfit`, `Oswald`, `Bebas Neue`), Font weights, Size slider.
  * **FORMAT:** Case transformations (`TT`, `Tt`, `tt`), Text alignment (`Left`, `Center`, `Right`).
  * **POSITION:** `X: 50.0%`, `Y: 80.0%` with reset button.
  * **COLOR:** Solid & Gradient color picker (`#FFFFFF`).
  * **EMPHASIS:** Active word highlight palette (Neon Yellow, Neon Green, Electric Cyan, Hot Pink, Flame Orange).
  * **EFFECTS:** Stroke/Border outline, Drop Shadow, Background box.
  * **1-CLICK VIRAL PRESETS:**
    1. *The Hormozi* (Bold uppercase, Neon Yellow active highlight, Black stroke)
    2. *MrBeast Style* (Bouncy Pop animation, multi-color words, drop shadow, auto-emojis)
    3. *Iman Gadzhi / Minimal* (Clean Serif/Modern, Elegant White/Gold fade)
    4. *Ali Abdaal* (Clean Sans-Serif, pastel highlight, smooth timing)
    5. *Karaoke Glow* (Continuous line with glowing active word)
    6. *Cyberpunk Neon* (Neon Cyan/Pink glow, futuristic glitch vibe)
    7. *Dark Box / News* (High contrast dark pill background)
* **Export Dialog:**
  * Rendered MP4 Video with burned-in subtitles (`1080p / 4K`)
  * SubRip Subtitle file (`.SRT`)
  * WebVTT Subtitle file (`.VTT`)
  * Plain text transcript (`.TXT`)

---

## 🚀 How to Run the Web App

### Option 1: 1-Click Batch Launcher (Recommended)
Double click on `Launch_Kalakar_Studio.bat` located at:
`C:\Users\Abc\Documents\KalakarWebStudio\Launch_Kalakar_Studio.bat`

This will automatically start the server and open `http://localhost:7860` in your web browser.

### Option 2: Command Line
```powershell
cd C:\Users\Abc\Documents\KalakarWebStudio
& "C:\Users\Abc\AppData\Local\Programs\Python311\python.exe" server.py 7860
```
Open your browser and visit: `http://localhost:7860`
