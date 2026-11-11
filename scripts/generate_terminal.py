#!/usr/bin/env python3
"""Build a deterministic looping portfolio terminal GIF from approved public JSON.

No tokens, GitHub API, secret data, network access, or arbitrary visitor input required.
Intended for local regeneration and scheduled GitHub Actions runs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'terminal_display.json'
FACTS = ROOT / 'config' / 'profile_knowledge.json'
PROJECTS = ROOT / 'config' / 'projects.json'
OUTPUT = ROOT / 'assets' / 'terminal-status.gif'

W, H = 1000, 324
BACKGROUND = '#091726'
PANEL = '#0e2134'
WHITE = '#eef7ff'
MUTED = '#aec5d8'
GREEN = '#3bf74e'  # matches the supplied Readme Typing SVG color
TEAL = '#43e4cc'
PURPLE = '#9c9cff'
BORDER = '#37546b'


def font(size: int, bold: bool = False, mono: bool = False):
    choices = (
        ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']
        if mono and bold else
        ['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf']
        if mono else
        ['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
        if bold else
        ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']
    )
    for f in choices:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            continue
    return ImageFont.load_default()


FONT_TITLE = font(23, bold=True)
FONT_TAG = font(17, bold=True, mono=True)
FONT_BODY = font(22)
FONT_CMD = font(23, mono=True)
FONT_FOOT = font(14, mono=True)


def safe_text(v: str) -> str:
    if not isinstance(v, str):
        raise ValueError('Text fields must contain strings')
    v = re.sub(r'[\x00-\x1f\x7f]', ' ', v)
    return re.sub(r'\s+', ' ', v).strip()


def short_fact(fact: str, limit: int = 245) -> str:
    """Display a concise excerpt, not an invented claim or generated summary."""
    fact = safe_text(fact)
    # One or two complete sentences if they fit; otherwise a visibly truncated excerpt.
    fragments = re.split(r'(?<=[.!?])\s+', fact)
    text = fragments[0]
    for f in fragments[1:]:
        if len(text) + len(f) + 1 > limit:
            break
        text += ' ' + f
    if len(text) > limit:
        text = text[:limit-1].rsplit(' ', 1)[0] + '…'
    return text


def load_slides():
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    facts = {f['id']: f['text'] for f in json.loads(FACTS.read_text(encoding='utf-8'))['facts']}
    projects = json.loads(PROJECTS.read_text(encoding='utf-8'))
    output=[]
    valid_commands={'whoami','experience','qa','projects','stack','ai','ask','architecture','contact'}
    for row in config['slides']:
        cmd = safe_text(row['command'])
        if cmd not in valid_commands:
            raise ValueError(f'Unknown/unsafe command {cmd!r}')
        label = safe_text(row['label'])
        if len(label) > 43:
            raise ValueError('Slide label too long')
        if row.get('type') == 'projects':
            names = [safe_text(projects['catalog'][pid]['title']) for pid in projects['featured']]
            body = names[:4]  # top four featured projects, in JSON order
        elif row.get('type') == 'message':
            body = [safe_text(row['text'])]
        else:
            fid = row['fact_id']
            if fid not in facts:
                raise ValueError(f'Unknown fact {fid!r}')
            body = [short_fact(facts[fid])]
        output.append((cmd, label, body))
    if not (2 <= len(output) <= 10):
        raise ValueError('Choose between two and ten terminal scenes')
    return output


def wrapped(draw: ImageDraw.ImageDraw, lines: list[str], max_width: int, max_lines: int):
    result=[]
    for text in lines:
        row=''
        for word in text.split(' '):
            attempt=(row + ' ' + word).strip()
            if row and draw.textlength(attempt, FONT_BODY) > max_width:
                result.append(row)
                row=word
            else:
                row=attempt
        if row: result.append(row)
    if len(result)>max_lines:
        result=result[:max_lines]
        while result[-1] and draw.textlength(result[-1]+'…', FONT_BODY)>max_width:
            result[-1]=result[-1][:-1]
        result[-1]=result[-1].rstrip(' ,;:')+'…'
    return result


def draw_frame(cmd: str, label: str, body: list[str], progress: float, scene: int, total: int):
    im=Image.new('RGB', (W,H), BACKGROUND)
    d=ImageDraw.Draw(im)
    # Faint technical grid, kept dark enough for high-contrast text.
    for x in range(24, W, 40):
        d.line((x,55,x,H-23),fill='#12283b',width=1)
    for y in range(63,H-23,40):
        d.line((14,y,W-14,y),fill='#12283b',width=1)
    d.rounded_rectangle((1,1,W-2,H-2),radius=19,outline=BORDER,width=2)
    d.rounded_rectangle((2,2,W-3,54),radius=17,fill='#182d41')
    d.rectangle((2,35,W-3,54),fill='#182d41')
    for x,color in [(24,'#fb7185'),(43,'#ffc970'),(62,'#46d6ad')]:
        d.ellipse((x,22,x+10,32),fill=color)
    d.text((85,17),'gino@portfolio:~/terminal',font=FONT_TAG,fill=WHITE)
    d.text((W-189,18),'AUTO-GENERATED',font=FONT_FOOT,fill=TEAL)

    d.text((26,75),'GINO.OS  /  '+label,font=FONT_TITLE,fill=GREEN)
    d.line((26,115,W-26,115),fill='#34566a',width=1)

    partial=cmd[:max(0,int(round(len(cmd)*progress)))]
    d.text((27,126),'visitor@github:~$',font=FONT_CMD,fill=TEAL)
    d.text((305,126),' '+partial + ('▌' if progress < 1 else ''),font=FONT_CMD,fill=WHITE)
    if progress>=0.85:
        displayed=wrapped(d,body,W-65,4)
        for i,line in enumerate(displayed):
            d.text((29,173+i*28),line,font=FONT_BODY,fill=WHITE if i==0 else MUTED)
    else:
        d.text((29,180),'loading portfolio context...',font=FONT_BODY,fill='#6e8fa5')

    d.line((25,H-45,W-26,H-45),fill='#29485e',width=1)
    d.text((28,H-35),'PUBLIC PORTFOLIO DATA  •  NOT LIVE TELEMETRY',font=FONT_FOOT,fill='#9db7c8')
    for i in range(total):
        cx=W-26-(total-1-i)*19
        d.ellipse((cx-4,H-34,cx+4,H-26),fill=GREEN if i==scene else '#3a6473')
    return im


def build():
    scenes=load_slides()
    frames=[]
    durations=[]
    for i,(cmd,label,body) in enumerate(scenes):
        for progress, duration in [(0.18,150),(0.55,170),(0.86,210),(1.0,1750)]:
            frames.append(draw_frame(cmd,label,body,progress,i,len(scenes)))
            durations.append(duration)
    # Palette optimization keeps the downloadable GIF fairly small.
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(OUTPUT,save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True,disposal=2)
    print(f'Generated {OUTPUT.relative_to(ROOT)} ({len(scenes)} scenes; {len(frames)} frames; {OUTPUT.stat().st_size/1024:.0f} KiB)')
    return frames


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true',help='Validate JSON and slides without writing')
    args=parser.parse_args()
    if args.check:
        print(f'{len(load_slides())} terminal scenes validated')
    else:
        build()
