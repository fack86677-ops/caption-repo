# -*- coding: utf-8 -*-
"""
Hinglish Engine
Converts Hindi (Devanagari script) into natural, modern, colloquial Hinglish (Roman script).
Handles vocabulary mapping, phonetics, schwa deletion, and loanwords preservation.
"""

import re
import sys

# Ensure UTF-8 stdout if run standalone
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Comprehensive Hindi & Hinglish colloquial words dictionary
COMMON_HINGLISH_WORDS = {
    # Pronouns & Demonstratives
    "यह": "yeh", "ये": "ye", "वह": "woh", "वो": "wo", "मैं": "mai", "मै": "mai",
    "हम": "hum", "आप": "aap", "तुम": "tum", "तू": "tu",
    "मेरा": "mera", "मेरी": "meri", "मेरे": "mere",
    "हमारा": "hamara", "हमारी": "hamari", "हमारे": "hamare",
    "आपका": "aapka", "आपकी": "aapki", "आपके": "aapke",
    "तुम्हारा": "tumhara", "तुम्हारी": "tumhari", "तुम्हारे": "tumhare",
    "इसका": "iska", "इसकी": "iski", "इसके": "iske",
    "उसका": "uska", "उसकी": "uski", "उसके": "uske",
    "इनका": "inka", "इनकी": "inki", "इनके": "inke",
    "उनका": "unka", "उनकी": "unki", "उनके": "unke",
    "किसे": "kise", "किस": "kis", "किसका": "kiska", "किसकी": "kiski", "किसके": "kiske",
    "खुद": "khud", "अपना": "apna", "अपनी": "apni", "अपने": "apne",

    # Question Words
    "क्या": "kya", "क्यों": "kyun", "क्यूँ": "kyun", "क्यूं": "kyun",
    "कैसे": "kaise", "कैसा": "kaisa", "कैसी": "kaisi",
    "कहाँ": "kahan", "कहा": "kaha", "कहाँ पर": "kahan par",
    "कब": "kab", "कौन": "kaun", "कितना": "kitna", "कितनी": "kitni", "कितने": "kitne",

    # Auxiliary Verbs & Tenses
    "है": "hai", "हैं": "hain", "हूँ": "hoon", "हूं": "hoon", "हो": "ho",
    "था": "tha", "थी": "thi", "थे": "the",
    "रहा": "raha", "रही": "rahi", "रहे": "rahe",
    "होगा": "hoga", "होगी": "hogi", "होंगे": "honge",
    "होता": "hota", "होती": "hoti", "होते": "hote", "होने": "hone", "होना": "hona", "हुआ": "hua", "हुई": "hui", "हुए": "hue",
    "सकता": "sakta", "सकती": "sakti", "सकते": "sakte", "सकेंगे": "sakenge",
    "चाहिए": "chahiye", "पड़ेगा": "padega", "पड़ेगी": "padegi", "पड़ेंगे": "padenge",

    # Common Verbs
    "करना": "karna", "करते": "karte", "करती": "karti", "करता": "karta", "कर": "kar", "करो": "karo", "कीजिये": "kijiye", "करें": "karein", "करे": "kare",
    "करेंगे": "karenge", "करूँगा": "karunga", "करूंगा": "karunga", "करूँगी": "karungi", "करूंगी": "karungi",
    "किया": "kiya", "किए": "kiye", "की": "ki", "के": "ke", "का": "ka", "को": "ko",
    "गया": "gaya", "गई": "gayi", "गए": "gaye", "जाना": "jaana", "जाते": "jaate", "जाती": "jaati", "जाता": "jaata", "जाओ": "jaao", "जाइए": "jaiye", "जाएंगे": "jaenge",
    "आना": "aana", "आते": "aate", "आती": "aati", "आता": "aata", "आओ": "aao", "आइए": "aaiye", "आया": "aaya", "आई": "aayi", "आए": "aaye", "आएंगे": "aaenge",
    "देखना": "dekhna", "देखते": "dekhte", "देखती": "dekhti", "देखता": "dekhta", "देखो": "dekho", "देखिए": "dekhiye", "देखा": "dekha", "देखी": "dekhi", "देखे": "dekhe", "देखें": "dekhein",
    "बोलना": "bolna", "बोलते": "bolte", "बोलती": "bolti", "बोलता": "bolta", "बोलो": "bolo", "बोलिए": "boliye", "बोला": "bola", "बोली": "boli", "बोले": "bole",
    "कहना": "kahna", "कहते": "kahte", "कहती": "kahti", "कहता": "kahta", "कहो": "kaho", "कहिए": "kahiye", "कहा": "kaha", "कही": "kahi", "कहे": "kahe",
    "सुनना": "sunna", "सुनते": "sunte", "सुनती": "sunti", "सुनता": "sunta", "सुनो": "suno", "सुनिए": "suniye", "सुना": "suna", "सुनी": "suni", "सुने": "sune",
    "बताना": "batana", "बताते": "batate", "बताती": "batati", "बताता": "batata", "बताओ": "batao", "बताइए": "bataiye", "बताया": "bataya", "बताई": "batai", "बताए": "batae", "बताएंगे": "bataenge",
    "सीखना": "seekhna", "सीखते": "seekhte", "सीखो": "seekho", "सीखेंगे": "seekhenge", "सिखाना": "sikhana",
    "बनाना": "banana", "बनाते": "banate", "बनाओ": "banao", "बनाया": "banaya", "बनाएंगे": "banaenge",
    "देना": "dena", "देते": "dete", "दो": "do", "दीजिए": "dijiye", "दिया": "diya", "दिए": "diye", "देंगे": "denge",
    "लेना": "lena", "लेते": "lete", "लो": "lo", "लीजिए": "lijiye", "लिया": "liya", "लिए": "liye", "लेंगे": "lenge",
    "रखना": "rakhna", "रखते": "rakhte", "रखो": "rakho", "रखा": "rakha", "रखेंगे": "rakhenge",
    "मिलना": "milna", "मिलते": "milte", "मिला": "mila", "मिली": "mili", "मिले": "mile", "मिलेंगे": "milenge",
    "समझना": "samajhna", "समझते": "samajhte", "समझा": "samjha", "समझे": "samjhe", "समझ": "samajh", "समझिए": "samjhiye",

    # Prepositions, Conjunctions & Particles
    "और": "aur", "या": "ya", "लेकिन": "lekin", "मगर": "magar", "परंतु": "parantu", "किंतु": "kintu",
    "अगर": "agar", "यदि": "yadi", "तो": "toh", "भी": "bhi", "ही": "hi", "तक": "tak",
    "में": "me", "पर": "par", "से": "se", "द्वारा": "dwara", "साथ": "saath", "बिना": "bina",
    "लिए": "liye", "वास्ते": "vaaste", "बारे": "baare", "बाद": "baad", "पहले": "pehle",
    "नहीं": "nahi", "ना": "na", "मत": "mat", "हाँ": "haan", "जी": "ji",

    # Adjectives & Adverbs
    "बहुत": "bahut", "ज़्यादा": "zyada", "ज्यादा": "zyada", "कम": "kam", "थोड़ा": "thoda", "थोड़ी": "thodi", "थोड़े": "thode",
    "अच्छा": "achha", "अच्छी": "achhi", "अच्छे": "achhe", "बुरा": "bura", "बुरी": "buri", "बुरे": "bure",
    "बड़ा": "bada", "बड़ी": "badi", "बड़े": "bade", "छोटा": "chhota", "छोटी": "chhoti", "छोटे": "chhote",
    "नया": "naya", "नई": "nayi", "नए": "naye", "पुराना": "purana", "पुरानी": "purani", "पुराने": "purane",
    "सही": "sahi", "गलत": "galat", "ज़रूरी": "zaroori", "जरूरी": "zaroori", "खास": "khaas", "ज़रूर": "zaroor", "जरूर": "zaroor",
    "पसंद": "pasand", "तरीका": "tarika", "तरीके": "tarike", "बात": "baat", "बातें": "baatein",
    "आसान": "aasan", "मुश्किल": "mushkil", "जल्दी": "jaldi", "धीरे": "dheere",
    "आज": "aaj", "कल": "kal", "परसों": "parso", "अब": "ab", "तब": "tab", "जब": "jab",
    "हमेशा": "hamesha", "कभी": "kabhi", "यहाँ": "yahan", "वहाँ": "wahan", "यहाँ पर": "yahan par",
    "एक": "ek", "दो": "do", "तीन": "teen", "चार": "chaar", "पांच": "paanch", "पाँच": "paanch",

    # Greetings & Salutations
    "नमस्ते": "namaste", "नमस्कार": "namaskar", "प्रणाम": "pranaam",
    "धन्यवाद": "dhanyawad", "शुक्रिया": "shukriya", "स्वागत": "swagat",
    "दोस्तों": "dosto", "दोस्तो": "dosto", "दोस्त": "dost", "मित्रों": "mitro",
    "भाइयों": "bhaiyo", "भाई": "bhai", "बहनों": "behno", "बहन": "behan",
    "यारों": "yaaro", "यार": "yaar", "सर": "sir", "मैम": "ma'am",

    # Tech, Social Media & Common English Loanwords transcribed in Hindi
    "वीडियो": "video", "ऑडियो": "audio", "चैनल": "channel", "सब्सक्राइब": "subscribe",
    "कैप्शन": "caption", "कैप्शन्स": "captions", "जनरेट": "generate", "क्रिएट": "create",
    "लाइक": "like", "शेयर": "share", "कमेंट": "comment", "फॉलो": "follow",
    "फास्ट": "fast", "स्लो": "slow", "सिस्टम": "system", "फ्री": "free",
    "लिंक": "link", "डिस्क्रिप्शन": "description", "बटन": "button", "क्लिक": "click",
    "स्क्रीन": "screen", "मोबाइल": "mobile", "कंप्यूटर": "computer", "लैपटॉप": "laptop",
    "इंटरनेट": "internet", "वेबसाइट": "website", "एप": "app", "ऐप": "app", "एप्लिकेशन": "application",
    "डाउनलोड": "download", "अपलोड": "upload", "ऑनलाइन": "online", "ऑफलाइन": "offline",
    "सेटिंग": "setting", "सेटिंग्स": "settings", "फाइल": "file", "फोल्डर": "folder",
    "गूगल": "google", "यूट्यूब": "youtube", "फेसबुक": "facebook", "इंस्टाग्राम": "instagram",
    "व्हाट्सएप": "whatsapp", "ट्विटर": "twitter", "कोड": "code", "प्रोजेक्ट": "project",
    "स्टार्ट": "start", "शुरू": "shuru", "खत्म": "khatam", "स्टेप": "step", "स्टेप्स": "steps",
    "टिप्स": "tips", "ट्रिक्स": "tricks", "प्रॉब्लम": "problem", "सॉल्यूशन": "solution",
}

# Devanagari character mappings
INDEPENDENT_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo',
    'ऋ': 'ri', 'ॠ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'अं': 'an', 'अँ': 'an', 'अः': 'ah'
}

MATRAS = {
    'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'ॄ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ॉ': 'o', 'ं': 'n', 'ँ': 'n', 'ः': 'h'
}

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'f', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क्ष': 'ksh', 'त्र': 'tra', 'ज्ञ': 'gya'
}

NUKTA_CONSONANTS = {
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f'
}

HALANT = '्'
NUKTA = '़'

def is_devanagari(text: str) -> bool:
    """Checks if text contains Devanagari Unicode characters (U+0900 to U+097F)."""
    return any('\u0900' <= char <= '\u097f' for char in text)

def transliterate_devanagari_word(word: str) -> str:
    """Transliterates a single Devanagari Hindi word to natural Hinglish."""
    # Clean punctuation attached to word
    prefix = ""
    suffix = ""
    while word and not ('\u0900' <= word[0] <= '\u097f' or word[0].isalnum()):
        prefix += word[0]
        word = word[1:]
    while word and not ('\u0900' <= word[-1] <= '\u097f' or word[-1].isalnum()):
        suffix = word[-1] + suffix
        word = word[:-1]

    if not word:
        return prefix + suffix

    # Direct dictionary lookup
    if word in COMMON_HINGLISH_WORDS:
        return prefix + COMMON_HINGLISH_WORDS[word] + suffix

    # If it's pure English/numeric, return as is
    if not is_devanagari(word):
        return prefix + word + suffix

    # Normalize nukta combinations
    normalized_chars = []
    i = 0
    while i < len(word):
        char = word[i]
        if i + 1 < len(word) and word[i + 1] == NUKTA:
            combined = char + NUKTA
            normalized_chars.append(combined)
            i += 2
        else:
            normalized_chars.append(char)
            i += 1

    out = []
    length = len(normalized_chars)

    for idx, char in enumerate(normalized_chars):
        next_char = normalized_chars[idx + 1] if idx + 1 < length else None
        
        # Check Nukta consonant
        if char in NUKTA_CONSONANTS:
            base = NUKTA_CONSONANTS[char]
            if next_char == HALANT:
                out.append(base)
            elif next_char in MATRAS:
                out.append(base)
            else:
                # Schwa rule
                if idx == length - 1:
                    out.append(base)
                elif idx + 1 < length and normalized_chars[idx + 1] in CONSONANTS:
                    if idx + 2 < length and normalized_chars[idx + 2] in MATRAS:
                        out.append(base)
                    else:
                        out.append(base + 'a')
                else:
                    out.append(base + 'a')
            continue

        # Check Independent Vowel
        if char in INDEPENDENT_VOWELS:
            out.append(INDEPENDENT_VOWELS[char])
            continue

        # Check Consonant
        if char in CONSONANTS:
            base = CONSONANTS[char]
            if next_char == HALANT:
                out.append(base)
            elif next_char in MATRAS:
                out.append(base)
            else:
                # Schwa handling
                if idx == length - 1:
                    out.append(base)
                elif idx + 1 < length and normalized_chars[idx + 1] in CONSONANTS:
                    if idx + 2 < length and (normalized_chars[idx + 2] in MATRAS or normalized_chars[idx + 2] == HALANT):
                        out.append(base)
                    else:
                        out.append(base + 'a')
                else:
                    out.append(base + 'a')
            continue

        # Check Matra
        if char in MATRAS:
            out.append(MATRAS[char])
            continue

        # Halant is handled by preceding consonant
        if char == HALANT:
            continue

        # Other characters
        out.append(char)

    res = "".join(out)

    # Post-process common phonetic cleanups
    res = re.sub(r'ee(?=[aeiou])', 'iy', res)
    res = re.sub(r'oo(?=[aeiou])', 'uv', res)
    res = re.sub(r'aaa+', 'aa', res)
    res = re.sub(r'eee+', 'ee', res)
    res = re.sub(r'nn(?=[bcdfghjklmnpqrstvwxyz])', 'n', res)
    
    # Endings with 'ee' often look better as 'i' (e.g. 'tariki' -> 'tariki')
    if res.endswith("ee"):
        res = res[:-2] + "i"

    return prefix + res + suffix

def devanagari_to_hinglish(text: str) -> str:
    """
    Converts a full Hindi string containing sentences or phrases into smooth, readable Hinglish.
    Preserves existing English words, URLs, mentions, emojis, and punctuation.
    Replaces Hindi full-stop (।) with English period (.).
    """
    if not text:
        return ""

    # Replace Devanagari full stop / purnaviram with English dot
    text = text.replace("॥", ".").replace("।", ".")

    # Split by whitespace while preserving punctuation
    tokens = text.split(" ")
    converted_tokens = []

    for token in tokens:
        if is_devanagari(token):
            converted_tokens.append(transliterate_devanagari_word(token))
        else:
            converted_tokens.append(token)

    result = " ".join(converted_tokens)

    # Clean up multiple spaces
    result = re.sub(r'\s+', ' ', result).strip()
    
    # Capitalize sentence beginnings
    def cap_match(m):
        return m.group(1) + m.group(2).upper()

    result = re.sub(r'(^|[.!?]\s+)([a-z])', cap_match, result)

    return result

if __name__ == "__main__":
    test_phrases = [
        "नमस्ते दोस्तों, आज के इस वीडियो में हम बात करेंगे कैसे आप वीडियो के कैप्शन जनरेट कर सकते हैं।",
        "अगर आपको यह वीडियो पसंद आया तो चैनल को लाइक, शेयर और सब्सक्राइब जरूर करें!",
        "यह एक बहुत ही आसान और फास्ट तरीका है।"
    ]
    for p in test_phrases:
        print("Original :", p)
        print("Hinglish :", devanagari_to_hinglish(p))
        print("-" * 50)
