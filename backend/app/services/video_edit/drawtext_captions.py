import subprocess
import shlex


PURPLE = "0x6d0ef1"


def render_karaoke_captions(
    input_video: str,
    output_video: str,
    words: list,
    font_path: str,
):
    """
    words format:

    [
        {"word": "WHAT", "start": 1.2, "end": 1.8},
        {"word": "WOULD", "start": 1.8, "end": 2.3},
    ]
    """

    filters = []

    y_pos = "h*0.78"

    for i, w in enumerate(words):

        word = w["word"]
        start = w["start"]
        end = w["end"]

        # inactive text
        filters.append(
            f"drawtext="
            f"text='{word}':"
            f"fontfile={font_path}:"
            f"fontsize=80:"
            f"fontcolor=white:"
            f"shadowcolor=black:"
            f"shadowx=4:"
            f"shadowy=4:"
            f"x=(w-text_w)/2:"
            f"y={y_pos}:"
            f"enable='between(t,{start},{end})'"
        )

        # active highlight box
        filters.append(
            f"drawtext="
            f"text='{word}':"
            f"fontfile={font_path}:"
            f"fontsize=80:"
            f"fontcolor=white:"
            f"box=1:"
            f"boxcolor={PURPLE}@0.9:"
            f"boxborderw=20:"
            f"x=(w-text_w)/2:"
            f"y={y_pos}:"
            f"enable='between(t,{start},{end})'"
        )

    filter_complex = ",".join(filters)

    cmd = f"""
    ffmpeg -y
    -i {shlex.quote(input_video)}
    -vf "{filter_complex}"
    -codec:a copy
    {shlex.quote(output_video)}
    """

    subprocess.run(cmd, shell=True, check=True)