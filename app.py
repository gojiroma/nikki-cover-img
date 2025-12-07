from flask import Flask, send_file
import requests
import re
import random
from io import BytesIO
from datetime import datetime

app = Flask(__name__)

def fetch_entry_md(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_entries(markdown_content):
    entries = []
    for entry_block in re.findall(r'---(.*?)---', markdown_content, re.DOTALL):
        entry = {}
        date_match = re.search(r'^date:\s*(\d{8})', entry_block, re.MULTILINE)
        content_match = re.search(r'content:\s*\|\s*\n(.*?)(?=\n---|\n$|$)', entry_block, re.DOTALL)
        if date_match:
            entry['date'] = date_match.group(1)
            if content_match:
                content = content_match.group(1).strip()
                content = re.sub(r'^\s*\|?\s*', '', content, flags=re.MULTILINE)
                entry['content'] = content.replace('\n', ' ').strip()
            entries.append(entry)
    return entries

def to_kanji_number(num):
    kanji_numbers = ['〇', '一', '二', '三', '四', '五', '六', '七', '八', '九']
    return ''.join(kanji_numbers[int(d)] for d in str(num))

def to_kanji_month(month):
    return ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'][month - 1]

def to_kanji_day(day):
    if day in {10, 20, 30}: return {10:'十日', 20:'二十日', 30:'三十日'}[day]
    if day == 31: return '三十一日'
    if day < 10: return to_kanji_number(day) + '日'
    if day < 20: return '十' + to_kanji_number(day - 10) + '日'
    if day < 30: return '二十' + to_kanji_number(day - 20) + '日'
    return to_kanji_number(day) + '日'

def format_japanese_date_with_day(yyyymmdd):
    dt = datetime.strptime(yyyymmdd, '%Y%m%d')
    month = int(yyyymmdd[4:6])
    day = int(yyyymmdd[6:8])
    dow = '月火水木金土日'[dt.weekday()]
    return f"{to_kanji_month(month)}{to_kanji_day(day)}（{dow}）"

def random_pastel_color():
    r = random.randint(180, 255)
    g = random.randint(180, 255)
    b = random.randint(180, 255)
    return f"rgb({r},{g},{b})"

def generate_svg(date, content, width=328, height=140):
    kanji_date = format_japanese_date_with_day(date)
    bg_color = random_pastel_color()
    date_font_size = 14
    content_font_size = 14
    content_width = width - 40
    svg_content = f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="{bg_color}" />
        <style>
            .date {{
                font-family: 'Hiragino Mincho Pro', 'Yu Mincho', serif;
                font-size: {date_font_size}px;
                fill: #333333;
                text-anchor: end;
            }}
            foreignObject {{
                overflow: visible;
            }}
            .content {{
                font-family: 'Hiragino Mincho Pro', 'Yu Mincho', serif;
                font-size: {content_font_size}px;
                color: #333333;
                width: {content_width}px;
                word-wrap: break-word;
                white-space: pre-wrap;
            }}
        </style>
        <foreignObject x="20" y="15" width="{content_width}" height="{height-30}">
            <div xmlns="http://www.w3.org/1999/xhtml" class="content">{content}</div>
        </foreignObject>
        <text x="{width-20}" y="{height-10}" class="date">{kanji_date}</text>
    </svg>"""
    return svg_content

@app.route('/<yyyymmdd>')
def diary_svg(yyyymmdd):
    entry_md_url = "https://nikki.poet.blue/entry.md"
    markdown_content = fetch_entry_md(entry_md_url)
    entries = parse_entries(markdown_content)

    for entry in entries:
        if entry['date'] == yyyymmdd:
            svg = generate_svg(entry['date'], entry['content'])
            svg_io = BytesIO(svg.encode('utf-8'))
            return send_file(svg_io, mimetype='image/svg+xml', as_attachment=False)

    return "Entry not found", 404

if __name__ == '__main__':
    app.run(port=5002, debug=True)
