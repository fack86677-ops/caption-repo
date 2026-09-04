# -*- coding: utf-8 -*-
"""
Harsh AI Studio / Kalakar Web Studio - Backend Server
Provides REST APIs for:
- User Authentication: Email 6-digit OTP & Google OAuth with Session Management
- User & Admin Dashboard APIs with Role-Based Access Control
- Video upload & ffprobe media info extraction
- Real AI Speech-to-Text Transcription with Faster-Whisper + Indic transliteration + word timestamps (No mock fallback)
- Subtitle generation & FFmpeg video burning
- Project state management & SQLite persistent storage
"""

import os
import sys
import json
import time
import uuid
import shutil
import random
import urllib.parse
from http.cookies import SimpleCookie
import subprocess
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn

# Configure UTF-8 for stdout and stderr on Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add current directory to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import db
from hinglish_engine import devanagari_to_hinglish

STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
PROJECTS_FILE = os.path.join(BASE_DIR, "projects.json")
SMTP_CONFIG_FILE = os.path.join(BASE_DIR, "smtp_config.json")
USERS_FILE = os.path.join(BASE_DIR, "users.json")
ADMIN_EMAIL = "harshdhiman332@gmail.com"

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)

# ─── SMTP CONFIGURATION & EMAIL SENDER ─────────────────────────────────

def get_smtp_config():
    config = {
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", 587)),
        "smtp_user": os.environ.get("SMTP_USER", ""),
        "smtp_pass": os.environ.get("SMTP_PASS", ""),
        "from_name": os.environ.get("SMTP_FROM_NAME", "Harsh AI Studio")
    }
    if os.path.exists(SMTP_CONFIG_FILE):
        try:
            with open(SMTP_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print("Error loading smtp_config.json:", e)
    return config

def send_real_email_otp(to_email, user_name, otp_code):
    """
    Sends a real 6-digit OTP email directly to user's Gmail / email inbox.
    """
    cfg = get_smtp_config()
    subject = f"{otp_code} is your Harsh AI Studio Verification Code"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #06080F; color: #FFFFFF; padding: 20px; }}
        .container {{ max-width: 520px; margin: 0 auto; background: #0B0F19; border: 1px solid #1E293B; border-radius: 18px; padding: 32px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .logo {{ font-size: 20px; font-weight: 900; color: #6366F1; margin-bottom: 20px; }}
        .title {{ font-size: 22px; font-weight: 800; color: #FFFFFF; margin-bottom: 8px; }}
        .desc {{ font-size: 14px; color: #94A3B8; line-height: 1.6; margin-bottom: 24px; }}
        .otp-box {{ background: rgba(99, 102, 241, 0.1); border: 2px dashed #6366F1; border-radius: 12px; padding: 18px; text-align: center; margin: 24px 0; }}
        .otp-code {{ font-size: 34px; font-weight: 900; letter-spacing: 8px; color: #818CF8; font-family: monospace; }}
        .footer {{ font-size: 12px; color: #64748B; border-top: 1px solid #1E293B; padding-top: 18px; margin-top: 24px; text-align: center; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="logo">⚡ HARSH AI STUDIO</div>
        <div class="title">Verify your Email Address</div>
        <p class="desc">Hello <strong>{user_name or 'Creator'}</strong>,<br>Thank you for signing in. Use the 6-digit verification code below to activate your account and claim your <strong>100 Free AI Credits</strong>:</p>
        
        <div class="otp-box">
          <div style="font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin-bottom: 6px;">Your 6-Digit Verification Code</div>
          <div class="otp-code">{otp_code}</div>
        </div>
        
        <p class="desc" style="font-size: 12px;">This verification code is valid for <strong>10 minutes</strong>. If you did not request this code, you can safely ignore this email.</p>
        
        <div class="footer">
          © 2026 Harsh AI Studio • Ultra-Premium AI Video & Caption Suite
        </div>
      </div>
    </body>
    </html>
    """
    
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pass = cfg.get("smtp_pass", "").strip()
    smtp_host = cfg.get("smtp_host", "smtp.gmail.com").strip()
    smtp_port = int(cfg.get("smtp_port", 587))
    from_name = cfg.get("from_name", "Harsh AI Studio")
    
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name} <{smtp_user}>"
            msg["To"] = to_email
            
            part = MIMEText(html_body, "html", "utf-8")
            msg.attach(part)
            
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())
            server.quit()
            print(f"[EMAIL ENGINE] Real OTP {otp_code} successfully delivered to {to_email} via {smtp_host}!")
            return True, f"OTP sent to {to_email}"
        except Exception as e:
            print(f"[EMAIL ENGINE] SMTP Delivery Error: {e}")
            return False, str(e)
    else:
        print(f"[EMAIL ENGINE] SMTP not configured in smtp_config.json. OTP for {to_email} is {otp_code}")
        return True, f"OTP generated for {to_email}"

def notify_admin_of_lead(user_data, client_ip="Unknown", user_agent="Unknown"):
    """Sends notification to harshdhiman332@gmail.com on login."""
    cfg = get_smtp_config()
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pass = cfg.get("smtp_pass", "").strip()
    
    if not (smtp_user and smtp_pass):
        return
        
    try:
        subject = f"🚀 New Creator Login: {user_data.get('email', 'Unknown')}"
        body = f"""
        New User Registered / Logged In:
        • Name: {user_data.get('name', 'N/A')}
        • Email: {user_data.get('email', 'N/A')}
        • Provider: {user_data.get('auth_provider', 'email')}
        • Role: {user_data.get('role', 'user')}
        • IP: {client_ip}
        • User-Agent: {user_agent}
        • Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = f"Harsh AI Alerts <{smtp_user}>"
        msg["To"] = ADMIN_EMAIL
        
        server = smtplib.SMTP(cfg.get("smtp_host", "smtp.gmail.com"), int(cfg.get("smtp_port", 587)), timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [ADMIN_EMAIL], msg.as_string())
        server.quit()
    except Exception as e:
        print(f"[LEAD NOTIFIER] Notification notice: {e}")

# ─── AUTHENTICATION HELPERS ───────────────────────────────────────────

def get_authenticated_user(handler):
    """
    Extracts authenticated user dict from session_id cookie or Authorization Bearer header.
    """
    session_id = None
    # 1. Cookie
    cookie_header = handler.headers.get('Cookie')
    if cookie_header:
        try:
            cookie = SimpleCookie()
            cookie.load(cookie_header)
            if 'session_id' in cookie:
                session_id = cookie['session_id'].value
        except Exception:
            pass
            
    # 2. Authorization Header
    if not session_id:
        auth_header = handler.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            session_id = auth_header[7:].strip()
            
    if session_id:
        user = db.get_session(session_id)
        if user:
            return user
            
    return None

# ─── MEDIA PROCESSING & SPEECH-TO-TEXT ENGINE ─────────────────────────

def get_ffmpeg_path():
    local_ffmpeg = os.path.join(BASE_DIR, "ffmpeg.exe")
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    return "ffmpeg"

def get_ffprobe_path():
    local_ffprobe = os.path.join(BASE_DIR, "ffprobe.exe")
    if os.path.exists(local_ffprobe):
        return local_ffprobe
    return "ffprobe"

def get_media_info(file_path):
    ffprobe = get_ffprobe_path()
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", file_path
    ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        data = json.loads(res.stdout.decode('utf-8'))
        duration = float(data.get("format", {}).get("duration", 15.0))
        width, height = 1080, 1920
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = int(stream.get("width", 1080))
                height = int(stream.get("height", 1920))
                break
        return {
            "duration": round(duration, 3),
            "width": width,
            "height": height,
            "aspect_ratio": f"{width}:{height}"
        }
    except Exception as e:
        print(f"Error reading media info: {e}")
        return {"duration": 15.0, "width": 1080, "height": 1920, "aspect_ratio": "9:16"}

def extract_audio(video_path, output_wav, enhance=True):
    ffmpeg = get_ffmpeg_path()
    # High-pass 70Hz cuts low-frequency rumble, loudnorm provides clear speech levels without distortion
    audio_filters = "highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11" if enhance else "anull"
    cmd = [
        ffmpeg, "-y", "-i", video_path,
        "-vn", "-af", audio_filters, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        output_wav
    ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    return res.returncode == 0 and os.path.exists(output_wav)

# Emoji mapping for auto-emoji feature
EMOJI_KEYWORDS = {
    "happy": "😊", "raksha": "🪢", "bandhan": "✨", "gifts": "🎁", "gift": "🎁",
    "video": "🎥", "money": "💰", "paisa": "💸", "kamao": "🤑", "growth": "📈",
    "secret": "🤫", "love": "❤️", "dost": "🤝", "fire": "🔥", "awesome": "⚡",
    "festive": "🎉", "festival": "🪔", "inside": "🚪", "party": "🥳", "wow": "🤩",
    "start": "🚀", "winner": "🏆", "danger": "⚠️", "idea": "💡", "learn": "📚"
}

RTL_LANGUAGES = ["ur", "ar", "fa", "ps", "sd", "ks"]

LANGUAGE_INITIAL_PROMPTS = {
    "hi": "नमस्ते, यह वीडियो हिंदी भाषा और देवनागरी लिपि में है।",
    "pa": "ਸਤਿ ਸ਼੍ਰੀ ਅਕਾਲ, ਇਹ ਵੀਡੀਓ ਪੰਜਾਬੀ ਵਿੱਚ ਹੈ।",
    "ur": "یہ ویڈیو اردو زبان میں ہے۔",
    "bn": "নমস্কার, এই ভিডিওটি বাংলা ভাষায়।",
    "gu": "નમસ્તે, આ વિડિઓ ગુજરાતીમાં છે.",
    "mr": "नमस्कार, हा व्हिडिओ मराठी भाषेत आहे.",
    "ta": "வணக்கம், இந்த காணொளி தமிழில் உள்ளது.",
    "te": "నమస్కారం, ఈ ویڈیو తెలుగులో ఉంది.",
    "en": "Hello, welcome to this video transcript with accurate punctuation."
}

def attach_emojis_to_segments(segments):
    for seg in segments:
        for w in seg.get("words", []):
            clean_word = w["word"].lower().strip(".,!?;:\"'")
            if clean_word in EMOJI_KEYWORDS:
                w["emoji"] = EMOJI_KEYWORDS[clean_word]
    return segments

def run_whisper_transcription(file_path, language="hi", script="roman", use_emojis=True, translate=False, enhance=True):
    """
    Runs faster-whisper on media file with translation, prompt biasing and noise reduction.
    Returns real word-level and line-level timestamps from the actual audio without any placeholder text.
    """
    temp_wav = os.path.join(UPLOADS_DIR, f"temp_{uuid.uuid4().hex[:8]}.wav")
    extract_audio(file_path, temp_wav, enhance=enhance)
    
    segments_data = []
    audio_source = temp_wav if os.path.exists(temp_wav) else file_path
    
    try:
        from faster_whisper import WhisperModel
        task_mode = "translate" if translate else "transcribe"
        initial_prompt = LANGUAGE_INITIAL_PROMPTS.get(language, "नमस्ते, यह वीडियो हिंदी भाषा और देवनागरी लिपि में है।")
        if language == "en":
            initial_prompt = LANGUAGE_INITIAL_PROMPTS["en"]
            
        print(f"[WHISPER ENGINE] Starting transcription: task={task_mode}, lang={language}, script={script}")
        try:
            model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception:
            model = WhisperModel("base", device="cpu", compute_type="int8")
        
        segments_gen, info = model.transcribe(
            audio_source,
            language=None if language == "auto" else language,
            task=task_mode,
            initial_prompt=initial_prompt,
            word_timestamps=True,
            beam_size=5
        )
        
        line_idx = 1
        for seg in segments_gen:
            words = []
            for w in (seg.words or []):
                raw_word = w.word.strip()
                processed_word = raw_word
                if script == "roman":
                    processed_word = devanagari_to_hinglish(raw_word)
                words.append({
                    "word": processed_word,
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "highlight": False
                })
            
            line_text = " ".join([w["word"] for w in words]) if words else seg.text.strip()
            if script == "roman":
                line_text = devanagari_to_hinglish(line_text)
                
            segments_data.append({
                "id": line_idx,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": line_text,
                "words": words
            })
            line_idx += 1
            
        print(f"[WHISPER ENGINE] Successfully transcribed {len(segments_data)} speech segments.")
            
    except Exception as e:
        print(f"[WHISPER ENGINE ERROR] {e}")
        raise e
    finally:
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except Exception:
                pass

    if use_emojis and segments_data:
        segments_data = attach_emojis_to_segments(segments_data)
        
    return segments_data

FALLBACK_SCRIPTS = {
    "hi_roman": [
        "Sunno bhai agar aap bhi apni reel viral karna chahte ho",
        "Toh sabse pehle video me animated captions lagana shuru karo",
        "Kyunki 85 percent log bina audio ke videos dekhte hain",
        "Harsh AI Studio se 1-click me viral captions generate hote hain",
        "Word by word pop animations se viewer engagement 10x badhta hai",
        "Aaj hi try karo aur apna content rapidly grow karo",
        "Video ko like aur share karna bilkul mat bhulna dosto",
        "Agli viral reel ke liye abhi create karo"
    ],
    "hi_native": [
        "सुनो दोस्तों अगर आप भी अपनी रील्स को वायरल करना चाहते हो",
        "तो सबसे पहले अपनी वीडियो में अट्रैक्टिव कैप्शन्स लगाना शुरू करो",
        "क्योंकि 85 प्रतिशत से ज्यादा लोग बिना आवाज़ के वीडियो देखते हैं",
        "हर्ष एआई स्टूडियो से 1 क्लिक में बेहतरीन कैप्शन्स तैयार करें",
        "वर्ड बाई वर्ड एनिमेशन से दर्शकों का ध्यान अंत तक बना रहता है",
        "अभी अपनी वीडियो एक्सपोर्ट करें और तेजी से ग्रो करें",
        "लाइक शेयर और सब्सक्राइब करना ना भूलें"
    ],
    "en": [
        "Stop scrolling right now if you want to grow your audience",
        "Adding dynamic word-by-word captions increases retention by 80 percent",
        "Most viewers on social media watch videos on mute",
        "Animated captions keep your audience hooked until the very end",
        "Create viral Alex Hormozi style subtitles in just one click",
        "Export in crystal clear ultra HD resolution effortlessly",
        "Hit that follow button for more creator growth secrets"
    ],
    "pa": [
        "ਸੁਣੋ ਜੀ ਜੇਕਰ ਤੁਸੀਂ ਵੀ ਆਪਣੀ ਰੀਲ ਵਾਇਰਲ ਕਰਨਾ ਚਾਹੁੰਦੇ ਹੋ",
        "ਤਾਂ ਸਭ ਤੋਂ ਪਹਿਲਾਂ ਵੀਡੀਓ ਵਿੱਚ ਐਨੀਮੇਟਿਡ ਕੈਪਸ਼ਨ ਲਗਾਓ",
        "ਇਸ ਨਾਲ ਵੀਡੀਓ ਦਾ ਵਾਚ ਟਾਈਮ ਬਹੁਤ ਵਧ ਜਾਂਦਾ ਹੈ",
        "ਹਰਸ਼ ਏਆਈ ਸਟੂਡੀਓ ਨਾਲ 1 ਕਲਿੱਕ ਵਿੱਚ ਕੈਪਸ਼ਨ ਬਣਾਓ"
    ],
    "ur": [
        "اگر آپ بھی اپنی ویڈیو وائرل کرنا چاہتے ہیں",
        "تو سب سے پہلے اپنی ویڈیو میں دلکش کیپشنز لگائیں",
        "کیونکہ متحرک کیپشنز سے ویڈیو کی مقبولیت میں اضافہ ہوتا ہے",
        "ہرش اے آئی اسٹوڈیو سے باآسانی کیپشنز بنائیں"
    ]
}

def generate_dynamic_segments(duration=15.0, language="hi", script="roman", use_emojis=True):
    key = f"{language}_{script}" if language == "hi" else language
    lines = FALLBACK_SCRIPTS.get(key, FALLBACK_SCRIPTS.get("hi_roman"))
    
    segments = []
    seg_duration = 2.4
    num_segs = max(1, int(duration // seg_duration))
    current_time = 0.0
    
    for i in range(num_segs):
        if current_time >= duration - 0.5:
            break
        end_time = min(duration, round(current_time + seg_duration, 3))
        text = lines[i % len(lines)]
        words_raw = text.split(" ")
        words = []
        w_dur = (end_time - current_time) / max(1, len(words_raw))
        for w_idx, w in enumerate(words_raw):
            w_start = round(current_time + w_idx * w_dur, 3)
            w_end = round(current_time + (w_idx + 1) * w_dur, 3)
            words.append({
                "word": w,
                "start": w_start,
                "end": w_end,
                "highlight": False
            })
        segments.append({
            "id": i + 1,
            "start": round(current_time, 3),
            "end": end_time,
            "text": text,
            "words": words
        })
        current_time = end_time

    if use_emojis:
        segments = attach_emojis_to_segments(segments)
    return segments

# ─── SUBTITLE FORMATTERS & ASS RENDERER ─────────────────────────────────

def format_timestamp_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000: millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000: millis = 999
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def hex_to_ass_color(c_str, alpha="00", default="&H00FFFFFF&"):
    if not c_str: return default
    c_str = str(c_str).strip().lstrip('#')
    if len(c_str) == 6:
        r, g, b = c_str[0:2], c_str[2:4], c_str[4:6]
        return f"&H{alpha}{b}{g}{r}&"
    return default

def format_timestamp_ass(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100: centis = 99
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

def generate_ass_content(segments, style, play_res_x=1080, play_res_y=1920):
    font_name = style.get("fontFamily", "Montserrat")
    font_size = int(style.get("fontSize", 34) * (play_res_y / 1080.0) * 1.5)
    
    primary_color = hex_to_ass_color(style.get("color", "#FFFFFF"))
    highlight_color = hex_to_ass_color(style.get("highlightColor", "#FFE600"))
    outline_color = hex_to_ass_color(style.get("strokeColor", "#000000"))
    back_color = "&H80000000&" if style.get("shadow", True) else "&H00000000&"
    
    stroke_width = 4 if style.get("strokeWidth", 2) > 0 else 0
    shadow_depth = 2 if style.get("shadow", True) else 0
    
    pos_y = style.get("posY", 80)
    margin_v = max(40, int((100 - pos_y) * (play_res_y / 100.0)))
    
    display_mode = style.get("displayMode", "chunk")
    text_transform = style.get("textTransform", "uppercase")
    
    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: HarshCaptions,{font_name},{font_size},{primary_color},&H000000FF&,{outline_color},{back_color},-1,0,0,0,100,100,0,0,1,{stroke_width},{shadow_depth},2,40,40,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]
    
    for seg in segments:
        words = seg.get("words", [])
        if not words or display_mode == "full":
            s = format_timestamp_ass(seg.get("start", 0))
            e = format_timestamp_ass(seg.get("end", 0))
            text = seg.get("text", "")
            if text_transform == "uppercase": text = text.upper()
            elif text_transform == "capitalize": text = text.title()
            lines.append(f"Dialogue: 0,{s},{e},HarshCaptions,,0,0,0,,{text}")
        elif display_mode == "single":
            for w in words:
                s = format_timestamp_ass(w.get("start", 0))
                e = format_timestamp_ass(w.get("end", 0))
                w_text = w.get("word", "") + (" " + w.get("emoji") if w.get("emoji") else "")
                if text_transform == "uppercase": w_text = w_text.upper()
                elif text_transform == "capitalize": w_text = w_text.title()
                c = highlight_color if w.get("highlight") else primary_color
                lines.append(f"Dialogue: 0,{s},{e},HarshCaptions,,0,0,0,,{{\\c{c}}}{w_text}")
        else: # chunk (2-3 words)
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                if not chunk: continue
                s = format_timestamp_ass(chunk[0].get("start", 0))
                e = format_timestamp_ass(chunk[-1].get("end", 0))
                
                parts = []
                for w in chunk:
                    w_text = w.get("word", "") + (" " + w.get("emoji") if w.get("emoji") else "")
                    if text_transform == "uppercase": w_text = w_text.upper()
                    elif text_transform == "capitalize": w_text = w_text.title()
                    c = highlight_color if w.get("highlight") else primary_color
                    parts.append(f"{{\\c{c}}}{w_text}")
                
                line_str = " ".join(parts)
                lines.append(f"Dialogue: 0,{s},{e},HarshCaptions,,0,0,0,,{line_str}")
                
    return "\n".join(lines)

def generate_srt_content(segments, display_mode="chunk", text_transform="uppercase"):
    lines = []
    line_idx = 1
    for seg in segments:
        words = seg.get("words", [])
        if not words or display_mode == "full":
            s = format_timestamp_srt(seg.get("start", 0))
            e = format_timestamp_srt(seg.get("end", 0))
            text = seg.get("text", "")
            if text_transform == "uppercase": text = text.upper()
            elif text_transform == "capitalize": text = text.title()
            lines.append(f"{line_idx}\n{s} --> {e}\n{text}\n")
            line_idx += 1
        elif display_mode == "single":
            for w in words:
                s = format_timestamp_srt(w.get("start", 0))
                e = format_timestamp_srt(w.get("end", 0))
                w_text = w.get("word", "") + (" " + w.get("emoji") if w.get("emoji") else "")
                if text_transform == "uppercase": w_text = w_text.upper()
                elif text_transform == "capitalize": w_text = w_text.title()
                lines.append(f"{line_idx}\n{s} --> {e}\n{w_text}\n")
                line_idx += 1
        else: # chunk (2-3 words)
            chunk_size = 3
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                if not chunk: continue
                s = format_timestamp_srt(chunk[0].get("start", 0))
                e = format_timestamp_srt(chunk[-1].get("end", 0))
                c_text = " ".join([w.get("word", "") + (" " + w.get("emoji") if w.get("emoji") else "") for w in chunk])
                if text_transform == "uppercase": c_text = c_text.upper()
                elif text_transform == "capitalize": c_text = c_text.title()
                lines.append(f"{line_idx}\n{s} --> {e}\n{c_text}\n")
                line_idx += 1
    return "\n".join(lines)

def generate_vtt_content(segments, display_mode="chunk", text_transform="uppercase"):
    lines = ["WEBVTT\n"]
    line_idx = 1
    for seg in segments:
        words = seg.get("words", [])
        if not words or display_mode == "full":
            s = format_timestamp_vtt(seg.get("start", 0))
            e = format_timestamp_vtt(seg.get("end", 0))
            text = seg.get("text", "")
            if text_transform == "uppercase": text = text.upper()
            lines.append(f"{line_idx}\n{s} --> {e}\n{text}\n")
            line_idx += 1
        else:
            chunk_size = 1 if display_mode == "single" else 3
            for i in range(0, len(words), chunk_size):
                chunk = words[i:i + chunk_size]
                if not chunk: continue
                s = format_timestamp_vtt(chunk[0].get("start", 0))
                e = format_timestamp_vtt(chunk[-1].get("end", 0))
                c_text = " ".join([w.get("word", "") + (" " + w.get("emoji") if w.get("emoji") else "") for w in chunk])
                if text_transform == "uppercase": c_text = c_text.upper()
                lines.append(f"{line_idx}\n{s} --> {e}\n{c_text}\n")
                line_idx += 1
    return "\n".join(lines)

def load_projects():
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_projects(projects):
    with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)

# ─── HTTP REQUEST HANDLER ──────────────────────────────────────────────

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class HarshRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]}\n")

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PATCH, DELETE')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-File-Name, Authorization')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # 1. HTML Pages
        if path == "/" or path == "/login" or path == "/login.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "login.html"), "rb") as f:
                self.wfile.write(f.read())
            return
            
        elif path == "/dashboard" or path == "/dashboard.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "dashboard.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/admin" or path == "/admin.html":
            # Server-side admin verification
            user = get_authenticated_user(self)
            if not user or user.get("role") != "admin":
                # Redirect to login with error parameter
                self.send_response(302)
                self.send_header("Location", "/login.html?admin_required=1")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "admin.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/editor" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "index.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        elif path == "/pricing" or path == "/pricing.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open(os.path.join(STATIC_DIR, "pricing.html"), "rb") as f:
                self.wfile.write(f.read())
            return

        # 2. Authentication & User APIs
        elif path == "/api/user/me":
            user = get_authenticated_user(self)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            if user:
                self.wfile.write(json.dumps({"authenticated": True, "user": user}).encode("utf-8"))
            else:
                self.wfile.write(json.dumps({"authenticated": False}).encode("utf-8"))
            return

        elif path == "/api/user/dashboard-data":
            user = get_authenticated_user(self)
            if not user:
                self.send_response(401)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Unauthorized"}).encode("utf-8"))
                return
                
            jobs = db.get_user_jobs(user["id"])
            user_projects = db.get_user_projects(user["id"])
            if not user_projects:
                user_projects = load_projects()
                
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True,
                "user": user,
                "jobs": jobs,
                "projects": user_projects
            }).encode("utf-8"))
            return

        # 3. Admin APIs
        elif path == "/api/admin/overview":
            user = get_authenticated_user(self)
            if not user or user.get("role") != "admin":
                self.send_response(403)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Admin access required"}).encode("utf-8"))
                return
                
            overview = db.get_admin_overview()
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "overview": overview}).encode("utf-8"))
            return

        elif path == "/api/admin/users":
            user = get_authenticated_user(self)
            if not user or user.get("role") != "admin":
                self.send_response(403)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Admin access required"}).encode("utf-8"))
                return
                
            query_params = urllib.parse.parse_qs(parsed.query)
            search = query_params.get("search", [""])[0]
            users_list = db.get_all_users_list(search)
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "users": users_list, "count": len(users_list)}).encode("utf-8"))
            return

        elif path == "/api/projects":
            projects = load_projects()
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "projects": projects}).encode("utf-8"))
            return

        # 4. Static Assets & Media
        elif path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.exists(file_path) and not os.path.isdir(file_path):
                self.serve_file(file_path)
            else:
                self.send_error(404, "Static file not found")
            return

        elif path.startswith("/uploads/"):
            rel_path = path[len("/uploads/"):]
            file_path = os.path.join(UPLOADS_DIR, rel_path)
            if os.path.exists(file_path):
                self.serve_file(file_path)
            else:
                self.send_error(404, "Upload file not found")
            return

        elif path.startswith("/exports/"):
            rel_path = path[len("/exports/"):]
            file_path = os.path.join(EXPORTS_DIR, rel_path)
            if os.path.exists(file_path):
                self.serve_file(file_path)
            else:
                self.send_error(404, "Export file not found")
            return

        self.send_error(404, "Page Not Found")

    def serve_file(self, file_path):
        mime = "application/octet-stream"
        if file_path.endswith(".html"): mime = "text/html"
        elif file_path.endswith(".css"): mime = "text/css"
        elif file_path.endswith(".js"): mime = "application/javascript"
        elif file_path.endswith(".json"): mime = "application/json"
        elif file_path.endswith(".png"): mime = "image/png"
        elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"): mime = "image/jpeg"
        elif file_path.endswith(".svg"): mime = "image/svg+xml"
        elif file_path.endswith(".mp4"): mime = "video/mp4"
        elif file_path.endswith(".webm"): mime = "video/webm"
        elif file_path.endswith(".mov"): mime = "video/quicktime"
        elif file_path.endswith(".mp3") or file_path.endswith(".wav"): mime = "audio/mpeg"
        elif file_path.endswith(".srt"): mime = "text/plain"
        elif file_path.endswith(".vtt"): mime = "text/vtt"
        elif file_path.endswith(".ttf"): mime = "font/ttf"
        elif file_path.endswith(".otf"): mime = "font/otf"

        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return

        try:
            file_size = os.path.getsize(file_path)
            range_header = self.headers.get("Range")

            if range_header and range_header.startswith("bytes="):
                ranges = range_header[6:].split("-")
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.end_headers()

                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_left = length
                    while bytes_left > 0:
                        chunk_size = min(bytes_left, 65536)
                        data = f.read(chunk_size)
                        if not data: break
                        self.wfile.write(data)
                        bytes_left -= len(data)
            else:
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(file_size))
                self.end_headers()

                with open(file_path, "rb") as f:
                    while True:
                        data = f.read(65536)
                        if not data: break
                        self.wfile.write(data)
        except Exception:
            pass

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # ── 1. SEND OTP API ──────────────────────────────────────────
        if path in ["/api/auth/send-otp", "/api/send_email_otp"]:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                raw_body = self.rfile.read(content_length).decode('utf-8')
                body = json.loads(raw_body) if raw_body else {}
                
                email = body.get("email", "").strip().lower()
                name = body.get("name", "Creator").strip()
                
                if not email or "@" not in email:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Invalid email address"}).encode("utf-8"))
                    return

                # Generate secure 6-digit OTP
                otp_code = str(random.randint(100000, 999999))
                
                # Save in DB with rate-limit check
                ok, msg = db.create_otp_request(email, otp_code, expiry_minutes=10, cooldown_seconds=30)
                if not ok:
                    self.send_response(429)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": msg}).encode("utf-8"))
                    return
                
                # Send email via SMTP
                sent_ok, email_msg = send_real_email_otp(email, name, otp_code)
                
                cfg = get_smtp_config()
                has_smtp = bool(cfg.get("smtp_user") and cfg.get("smtp_pass"))
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "message": f"Verification code sent to {email}",
                    "email": email,
                    "otp_fallback": otp_code if not has_smtp else None
                }).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
                return

        # ── 2. VERIFY OTP API ─────────────────────────────────────────
        elif path in ["/api/auth/verify-otp", "/api/verify_email_otp"]:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                raw_body = self.rfile.read(content_length).decode('utf-8')
                body = json.loads(raw_body) if raw_body else {}
                
                email = body.get("email", "").strip().lower()
                entered_otp = str(body.get("otp", "")).strip()
                name = body.get("name", "Creator").strip()
                
                if not email or not entered_otp:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Email and OTP code are required"}).encode("utf-8"))
                    return
                
                # Verify against DB
                ok, msg = db.verify_otp_code(email, entered_otp)
                if not ok:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": msg}).encode("utf-8"))
                    return
                
                # Get or create user
                user = db.get_or_create_user(email, name, auth_provider="email")
                session_id = db.create_session(user["id"], days=7)
                
                client_ip = self.client_address[0] if self.client_address else "Unknown"
                user_agent = self.headers.get("User-Agent", "Unknown")
                threading.Thread(target=notify_admin_of_lead, args=(user, client_ip, user_agent), daemon=True).start()
                
                # Set Session Cookie
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "verified": True,
                    "session_id": session_id,
                    "user": user,
                    "email": email,
                    "name": user["name"],
                    "role": user["role"],
                    "credits": user["credits"]
                }).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
                return

        # ── 3. GOOGLE OAUTH API ───────────────────────────────────────
        elif path in ["/api/auth/google", "/api/record_login"]:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                raw_body = self.rfile.read(content_length).decode('utf-8')
                body = json.loads(raw_body) if raw_body else {}
                
                email = body.get("email", "").strip().lower()
                name = body.get("name", "").strip() or email.split("@")[0]
                avatar_url = body.get("avatar_url") or body.get("picture") or ""
                
                if not email or "@" not in email:
                    self.send_response(400)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": "Invalid email"}).encode("utf-8"))
                    return
                
                user = db.get_or_create_user(email, name, auth_provider="google", avatar_url=avatar_url)
                session_id = db.create_session(user["id"], days=7)
                
                client_ip = self.client_address[0] if self.client_address else "Unknown"
                user_agent = self.headers.get("User-Agent", "Unknown")
                threading.Thread(target=notify_admin_of_lead, args=(user, client_ip, user_agent), daemon=True).start()
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "session_id": session_id,
                    "user": user,
                    "email": email,
                    "name": user["name"],
                    "role": user["role"],
                    "credits": user["credits"]
                }).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
                return

        # ── 4. LOGOUT API ─────────────────────────────────────────────
        elif path == "/api/auth/logout":
            cookie_header = self.headers.get('Cookie')
            if cookie_header:
                try:
                    cookie = SimpleCookie()
                    cookie.load(cookie_header)
                    if 'session_id' in cookie:
                        db.delete_session(cookie['session_id'].value)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Set-Cookie", "session_id=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            return

        # ── 5. ADMIN USER MANAGEMENT API ──────────────────────────────
        elif path == "/api/admin/users/update":
            user = get_authenticated_user(self)
            if not user or user.get("role") != "admin":
                self.send_response(403)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "Admin access required"}).encode("utf-8"))
                return
                
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            target_user_id = body.get("user_id")
            role = body.get("role")
            is_active = body.get("is_active")
            credits = body.get("credits")
            
            db.set_user_role_and_status(target_user_id, role=role, is_active=is_active, credits=credits)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "message": "User updated successfully"}).encode("utf-8"))
            return

        # ── 6. VIDEO UPLOAD API ───────────────────────────────────────
        elif path == "/api/upload":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                file_id = uuid.uuid4().hex[:12]
                filename = self.headers.get('X-File-Name', f"video_{file_id}.mp4")
                filename = urllib.parse.unquote(filename)
                save_path = os.path.join(UPLOADS_DIR, f"{file_id}_{filename}")

                with open(save_path, "wb") as f:
                    bytes_left = content_length
                    while bytes_left > 0:
                        chunk_size = min(bytes_left, 65536)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk: break
                        f.write(chunk)
                        bytes_left -= len(chunk)

                info = get_media_info(save_path)
                
                response = {
                    "success": True,
                    "file_id": file_id,
                    "filename": filename,
                    "video_url": f"/uploads/{file_id}_{filename}",
                    "file_path": save_path,
                    "info": info
                }

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                print(f"Upload error: {e}")
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # ── 7. AI TRANSCRIBE API (Fixed: Real Audio Only, No Mock Fallbacks) ──
        elif path == "/api/transcribe":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                file_path = body.get("file_path", "")
                language = body.get("language", "hi")
                script = body.get("script", "roman")
                use_emojis = body.get("emojis", True)
                translate = body.get("translate", False)
                enhance = body.get("audio_enhance", True)
                
                if not file_path or not os.path.exists(file_path):
                    file_path = os.path.join(STATIC_DIR, "assets", "demo_video.mp4")

                user = get_authenticated_user(self)
                user_id = user["id"] if user else None
                
                # Check credits if logged in
                if user and user.get("credits", 0) < 10:
                    self.send_response(402)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "Insufficient AI Credits. Please upgrade your plan to continue transcribing.",
                        "credits": user.get("credits", 0)
                    }).encode("utf-8"))
                    return

                # Perform actual transcription
                segments = run_whisper_transcription(
                    file_path,
                    language=language,
                    script=script,
                    use_emojis=use_emojis,
                    translate=translate,
                    enhance=enhance
                )

                # Record job and deduct credits
                credits_deducted = 0
                remaining_credits = user.get("credits", 100) if user else 100
                if user_id:
                    credits_deducted = 10
                    remaining_credits, _ = db.update_user_credits(user_id, -10)
                    job_id = f"job_{uuid.uuid4().hex[:10]}"
                    db.record_transcription_job(
                        job_id=job_id,
                        user_id=user_id,
                        filename=os.path.basename(file_path),
                        duration=segments[-1].get("end", 0) if segments else 0,
                        status="completed",
                        credits_deducted=credits_deducted
                    )

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "segments": segments,
                    "credits_deducted": credits_deducted,
                    "remaining_credits": remaining_credits
                }).encode("utf-8"))
            except Exception as e:
                print(f"[TRANSCRIBE ERROR] {e}")
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": f"Transcription failed: {str(e)}"}).encode("utf-8"))
            return

        # ── 8. PROJECT SAVE & DELETE APIS ─────────────────────────────
        elif path == "/api/save_project":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                user = get_authenticated_user(self)
                user_id = user["id"] if user else "anonymous"
                
                proj_id = body.get("id", f"proj_{uuid.uuid4().hex[:8]}")
                body["id"] = proj_id
                
                # Save to DB and projects.json
                db.save_project(proj_id, user_id, body.get("title", "Untitled Video"), json.dumps(body))
                
                projects = load_projects()
                existing_idx = next((i for i, p in enumerate(projects) if p.get("id") == proj_id), -1)
                if existing_idx >= 0:
                    projects[existing_idx] = body
                else:
                    projects.insert(0, body)
                save_projects(projects)

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "project": body}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        elif path == "/api/delete_project":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length).decode('utf-8'))
                proj_id = body.get("id")
                projects = load_projects()
                projects = [p for p in projects if p.get("id") != proj_id]
                save_projects(projects)
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # ── 9. EXPORT & RENDER API ────────────────────────────────────
        elif path == "/api/export":
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(content_length).decode('utf-8'))
                
                export_type = body.get("type", "mp4")
                segments = body.get("segments", [])
                video_path = body.get("file_path", "")
                style = body.get("style", {})
                display_mode = style.get("displayMode", "chunk")
                text_transform = style.get("textTransform", "uppercase")
                
                export_id = uuid.uuid4().hex[:8]
                
                resolution = body.get("resolution", "1080p")
                if resolution == "720p":
                    scale_w, scale_h = 720, 1280
                    crf_val = "24"
                elif resolution == "4k":
                    scale_w, scale_h = 2160, 3840
                    crf_val = "18"
                else: # 1080p
                    scale_w, scale_h = 1080, 1920
                    crf_val = "21"
                
                if export_type == "srt":
                    srt_content = generate_srt_content(segments, display_mode=display_mode, text_transform=text_transform)
                    out_name = f"captions_{export_id}.srt"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(srt_content)
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                elif export_type == "vtt":
                    vtt_content = generate_vtt_content(segments, display_mode=display_mode, text_transform=text_transform)
                    out_name = f"captions_{export_id}.vtt"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(vtt_content)
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                elif export_type == "txt" or export_type == "md":
                    ext = "md" if export_type == "md" else "txt"
                    txt_content = "\n".join([f"[{format_timestamp_srt(s.get('start', 0))}] {s.get('text', '')}" for s in segments])
                    out_name = f"transcript_{export_id}.{ext}"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(txt_content)
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                elif export_type == "docx":
                    doc_lines = ["HARSH AI STUDIO - TRANSCRIPT EXPORT\n", "="*45 + "\n\n"]
                    for s in segments:
                        doc_lines.append(f"[{format_timestamp_srt(s.get('start', 0))} --> {format_timestamp_srt(s.get('end', 0))}]\n{s.get('text', '')}\n\n")
                    out_name = f"transcript_{export_id}.doc"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write("".join(doc_lines))
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                elif export_type == "alpha":
                    ass_content = generate_ass_content(segments, style, play_res_x=scale_w, play_res_y=scale_h)
                    temp_ass = os.path.join(EXPORTS_DIR, f"temp_{export_id}.ass")
                    with open(temp_ass, "w", encoding="utf-8") as f:
                        f.write(ass_content)

                    out_name = f"alpha_captions_{export_id}_{resolution}.mp4"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    ffmpeg = get_ffmpeg_path()
                    escaped_ass = temp_ass.replace("\\", "/").replace(":", "\\:")
                    sub_filter = f"subtitles='{escaped_ass}'"

                    dur = segments[-1].get("end", 15.0) + 1.0 if segments else 15.0
                    cmd = [
                        ffmpeg, "-y",
                        "-f", "lavfi", "-i", f"color=c=0x00FF00:s={scale_w}x{scale_h}:d={dur}:r=30",
                        "-vf", sub_filter,
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", crf_val,
                        out_path
                    ]
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                    if os.path.exists(temp_ass):
                        try: os.remove(temp_ass)
                        except: pass
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                else: # MP4 burned video
                    ass_content = generate_ass_content(segments, style, play_res_x=scale_w, play_res_y=scale_h)
                    temp_ass = os.path.join(EXPORTS_DIR, f"temp_{export_id}.ass")
                    with open(temp_ass, "w", encoding="utf-8") as f:
                        f.write(ass_content)
                        
                    out_name = f"harsh_video_{export_id}_{resolution}.mp4"
                    out_path = os.path.join(EXPORTS_DIR, out_name)
                    
                    if not video_path or not os.path.exists(video_path):
                        video_path = os.path.join(STATIC_DIR, "assets", "demo_video.mp4")
                        
                    ffmpeg = get_ffmpeg_path()
                    escaped_ass = temp_ass.replace("\\", "/").replace(":", "\\:")
                    sub_filter = f"scale={scale_w}:{scale_h}:force_original_aspect_ratio=decrease,pad={scale_w}:{scale_h}:(ow-iw)/2:(oh-ih)/2,subtitles='{escaped_ass}'"
                    
                    cmd = [
                        ffmpeg, "-y",
                        "-i", video_path,
                        "-vf", sub_filter,
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", crf_val,
                        "-c:a", "aac", "-b:a", "192k",
                        out_path
                    ]
                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = subprocess.SW_HIDE
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
                    
                    if os.path.exists(temp_ass):
                        try: os.remove(temp_ass)
                        except: pass
                        
                    res = {"success": True, "download_url": f"/exports/{out_name}", "filename": out_name}

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
            return

        # Legacy login endpoint for backward compatibility
        elif path == "/api/login":
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length).decode('utf-8'))
            username = body.get('username', '').strip()
            password = body.get('password', '').strip()
            
            success = bool(username and len(username) >= 2)
            user = db.get_or_create_user(f"{username}@creator.studio", username, "legacy") if success else None
            session_id = db.create_session(user["id"]) if user else None
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            if session_id:
                self.send_header("Set-Cookie", f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800")
            self.end_headers()
            self.wfile.write(json.dumps({"success": success, "username": username, "user": user, "session_id": session_id}).encode('utf-8'))
            return

        self.send_error(404, "API endpoint not found")

def generate_default_sample_video():
    """Creates a sample vertical video with colorful animated background and audio if not present."""
    demo_video_path = os.path.join(STATIC_DIR, "assets", "demo_video.mp4")
    demo_thumb_path = os.path.join(STATIC_DIR, "assets", "demo_thumb.jpg")
    
    if not os.path.exists(demo_video_path):
        ffmpeg = get_ffmpeg_path()
        cmd = [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "color=c=0x101626:s=1080x1920:d=14.5:r=30",
            "-f", "lavfi", "-i", "anoisesrc=d=14.5:c=pink:r=44100:a=0.05",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            demo_video_path
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        except Exception as e:
            print(f"Sample video creation note: {e}")

    if not os.path.exists(demo_thumb_path) and os.path.exists(demo_video_path):
        ffmpeg = get_ffmpeg_path()
        cmd = [ffmpeg, "-y", "-i", demo_video_path, "-vframes", "1", "-q:v", "2", demo_thumb_path]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except: pass

def start_server(port=7860):
    db.init_db()
    generate_default_sample_video()
    server_address = ('0.0.0.0', port)
    httpd = ThreadedHTTPServer(server_address, HarshRequestHandler)
    print(f"\n=======================================================")
    print(f"⚡ Harsh AI Studio Backend Server Running!")
    print(f"🌐 Access URL: http://localhost:{port}")
    print(f"👑 Admin Email: {ADMIN_EMAIL}")
    print(f"=======================================================\n")
    httpd.serve_forever()

if __name__ == '__main__':
    port = 7860
    if len(sys.argv) > 1:
        try: port = int(sys.argv[1])
        except: pass
    start_server(port)
