import os
import re


# ------------------------------------------------------------
# Default caption style
# ------------------------------------------------------------
DEFAULT_STYLE = os.getenv("CAPTION_STYLE", "karaoke").lower()


# ------------------------------------------------------------
# ASS Template
# ------------------------------------------------------------
ASS_HEADER = """
[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
{style}

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""


# ------------------------------------------------------------
# Caption Style Definitions
# ------------------------------------------------------------
STYLES = {

    "bold_stroke":
        "Style: BoldStroke,The Bold Font,118,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,22,3,3,40,40,320,1",

    "red_highlight":
        "Style: RedHighlight,The Bold Font,108,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,6,3,3,40,40,320,1",

    "sleek":
        "Style: Sleek,Montserrat,92,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,3,2,2,40,40,320,1",

    "karaoke":
        "Style: Karaoke,DM Sans,105,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,5,3,2,40,40,320,1",

    "majestic":
        "Style: Majestic,Oswald,94,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,3,4,2,40,40,320,1",

    "beast":
        "Style: Beast,Komika Axis,115,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,20,3,2,40,40,320,1",

    "elegant":
        "Style: Elegant,Cormorant Garamond,92,&H00FFFFFF,&H00000000,&H00000000,0,0,1,3,2,2,40,40,320,1",

    "clarity":
        "Style: Clarity,Inter,88,&H00FFFFFF,&H00000000,&H00000000,-1,0,1,3,2,2,40,40,320,1",
}


STYLE_NAMES = {
    "bold_stroke": "BoldStroke",
    "red_highlight": "RedHighlight",
    "sleek": "Sleek",
    "karaoke": "Karaoke",
    "majestic": "Majestic",
    "beast": "Beast",
    "elegant": "Elegant",
    "clarity": "Clarity",
}


# ------------------------------------------------------------
# Time Utilities
# ------------------------------------------------------------
def _time_to_seconds(t: str):

    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def _seconds_to_time(seconds):

    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60

    return f"{h}:{m:02}:{s:05.2f}"


# ------------------------------------------------------------
# Keyword Emphasis
# ------------------------------------------------------------
def _emphasize_keywords(text: str):

    keywords = {
        "CHANGE",
        "SECRET",
        "SHOCKING",
        "NEVER",
        "TRUTH",
        "HIDDEN",
        "INSANE",
        "BIGGEST",
        "SUCCESS",
        "MONEY",
    }

    words = text.split()
    styled_words = []

    for word in words:

        clean = re.sub(r"[.,!?]", "", word)

        if clean.upper() in keywords:
            styled_words.append(f"{{\\fs120\\c&H00FFFF&}}{word}{{\\r}}")
        else:
            styled_words.append(word)

    return " ".join(styled_words)


# ------------------------------------------------------------
# Caption Chunk Splitting
# ------------------------------------------------------------
def _split_chunks(text):

    words = text.upper().split()

    if not words:
        return [text]

    chunks = []
    current = []

    for w in words:

        current.append(w)

        if len(current) >= 3:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# ------------------------------------------------------------
# Highlight Active Word
# CSS-style purple pill simulation
# ------------------------------------------------------------
def _highlight_karaoke(text: str, start: str, end: str):

    words = text.split()

    if not words:
        return text

    duration = _time_to_seconds(end) - _time_to_seconds(start)
    per_word = max(int((duration * 100) / len(words)), 30)

    styled = []

    for i, w in enumerate(words):

        if i == 0:
            styled.append(f"{{\\k{per_word}}}{w}")

        else:

            styled.append(
                f"{{\\k{per_word}"
                f"\\1c&H00FFFFFF&"
                f"\\3c&H00F10E6D&"
                f"\\bord14"
                f"\\blur3"
                f"\\shad3"
                f"\\fsp2"
                f"\\t(0,120,\\fscx108\\fscy108)"
                f"}}{w}{{\\r}}"
            )

    return " ".join(styled)


# ------------------------------------------------------------
# Style Resolver
# ------------------------------------------------------------
def _resolve_style(style_name: str | None):

    if style_name:
        style_name = style_name.lower()

    if not style_name:
        style_name = DEFAULT_STYLE

    if style_name not in STYLES:
        style_name = "karaoke"

    return style_name


# ------------------------------------------------------------
# Convert SRT → ASS
# ------------------------------------------------------------
def srt_to_ass(srt_path: str, style_name: str | None = None):

    if not os.path.exists(srt_path):
        raise RuntimeError(f"SRT not found: {srt_path}")

    style_name = _resolve_style(style_name)

    style_definition = STYLES[style_name]
    style_event = STYLE_NAMES[style_name]

    ass_path = srt_path.replace(".srt", ".ass")

    with open(srt_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines()]

    events = []
    i = 0

    while i < len(lines):

        if "-->" in lines[i]:

            times = lines[i].replace(",", ".")
            start, end = times.split(" --> ")

            text_lines = []
            i += 1

            while i < len(lines) and lines[i] != "":
                text_lines.append(lines[i])
                i += 1

            text = " ".join(text_lines)
            text = _emphasize_keywords(text)

            chunks = _split_chunks(text)

            start_sec = _time_to_seconds(start)
            end_sec = _time_to_seconds(end)

            duration = (end_sec - start_sec) / len(chunks)

            current = start_sec

            for chunk in chunks:

                chunk_start = _seconds_to_time(current)
                chunk_end = _seconds_to_time(current + duration)

                if style_name in ["karaoke", "red_highlight"]:
                    chunk = _highlight_karaoke(chunk, chunk_start, chunk_end)

                chunk = f"{{\\t(0,150,\\fscx110\\fscy110)}}{chunk}"

                events.append(
                    f"Dialogue: 0,{chunk_start},{chunk_end},{style_event},,0,0,0,,{chunk}"
                )

                current += duration

        i += 1

    with open(ass_path, "w", encoding="utf-8") as f:

        f.write(ASS_HEADER.format(style=style_definition))

        for event in events:
            f.write(event + "\n")

    return ass_path