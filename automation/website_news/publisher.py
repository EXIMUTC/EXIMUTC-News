#!/usr/bin/env python3
"""Build EXIMUTC Website News as a static, SEO-ready publication."""
from __future__ import annotations
import hashlib, html, json, re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs'
BASE_URL='https://news.eximutc.com'
STATE=ROOT/'pipeline_state'/'website_news_history.json'
QUEUE=ROOT/'EXIMUTC_NEWS_FEED_QUEUE.json'

def slugify(s):
    s=re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
    return s[:80] or 'news'

def fingerprint(item):
    key=(item.get('source_url','')+'|'+item.get('title','')).lower().strip()
    return hashlib.sha256(key.encode()).hexdigest()

def load_json(p, default):
    try:return json.loads(p.read_text())
    except (OSError,ValueError):return default

def pick_item(queue, history):
    items=queue if isinstance(queue,list) else queue.get('items') or queue.get('stories') or queue.get('queue') or []
    seen={x.get('fingerprint') for x in history}
    for raw in items:
        x={**raw, 'title':raw.get('title') or raw.get('headline'),
           'source_url':raw.get('source_url') or raw.get('url'),
           'source':raw.get('source') or raw.get('source_name')}
        if x.get('title') and x.get('source_url') and fingerprint(x) not in seen:return x
    return None

def esc(x):return html.escape(str(x or ''), quote=True)
def display_date(value):
    try:
        dt=datetime.fromisoformat(value).astimezone(ZoneInfo('America/New_York'))
        return dt.strftime('%B %-d, %Y at %-I:%M %p ET')
    except (ValueError, TypeError):
        return str(value)
def news_image(relative):
    return f'<figure><img src="{relative}" width="1200" height="630" alt="EXIMUTC editorial illustration of a blue-green faceted gemstone" style="width:100%;height:auto;border-radius:12px"><figcaption>EXIMUTC editorial illustration</figcaption></figure>'
def article_html(a):
    title=esc(a['title']); desc=esc(a.get('summary') or a.get('lead') or title)
    body=esc(a.get('body') or a.get('summary') or '').replace('\n','</p><p>')
    view=esc(a.get('market_view') or 'EXIMUTC follows verified developments in the natural gemstone and fine-jewelry market and separates sourced facts from market commentary.')
    src=esc(a['source_url']); source=esc(a.get('source') or urlparse(a['source_url']).netloc)
    canonical=f"{BASE_URL}/articles/{a['slug']}.html"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | EXIMUTC News</title><meta name="description" content="{desc[:155]}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc[:155]}"><meta property="og:image" content="{BASE_URL}/assets/gemstone-news.svg"><style>body{{font-family:Arial,sans-serif;margin:auto;max-width:900px;padding:28px;color:#151515;line-height:1.65}}header{{border-bottom:1px solid #ddd;margin-bottom:32px}}a{{color:#075985}}.view{{background:#f5f7f8;padding:20px;margin:30px 0}}small{{color:#666}}</style></head><body><header><h2>EXIMUTC NEWS</h2><p><a href="../">Natural Gemstones & Fine Jewelry Market Intelligence</a></p></header><main><h1>{title}</h1><time datetime="{esc(a['published_at'])}">{esc(display_date(a['published_at']))}</time>{news_image('../assets/gemstone-news.svg')}<p>{body}</p><section class="view"><h2>EXIMUTC Market View</h2><p>{view}</p></section><h2>Source</h2><p>{source}: <a href="{src}" rel="nofollow noopener">{src}</a></p></main><footer><hr><p>EXIMUTC, INC. · <a href="https://eximutc.com">eximutc.com</a></p></footer></body></html>'''

def build_index(history):
    cards=''.join(f'<article><h2><a href="articles/{esc(x["slug"])}.html">{esc(x["title"])}</a></h2><p>{esc(x.get("summary",""))}</p><time datetime="{esc(x["published_at"])}">{esc(display_date(x["published_at"]))}</time></article>' for x in reversed(history[-30:]))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EXIMUTC News | Natural Gemstones & Fine Jewelry</title><meta name="description" content="EXIMUTC market news and analysis covering natural gemstones, gemology, auctions and fine jewelry."><link rel="canonical" href="{BASE_URL}/"><style>body{{font-family:Arial,sans-serif;margin:auto;max-width:1000px;padding:28px;color:#151515}}header{{padding:35px 0;border-bottom:1px solid #ddd}}article{{padding:22px 0;border-bottom:1px solid #eee}}a{{color:#075985}}</style></head><body><header><h1>EXIMUTC NEWS</h1><p>Natural Gemstones & Fine Jewelry Market Intelligence</p><p><a href="https://eximutc.com">EXIMUTC.COM</a></p></header>{cards or '<p>Editorial feed is being prepared.</p>'}</body></html>'''

def main():
    OUT.mkdir(exist_ok=True); (OUT/'articles').mkdir(exist_ok=True); STATE.parent.mkdir(exist_ok=True)
    history=load_json(STATE,[]); queue=load_json(QUEUE,{})
    # Read existing editorial output without invoking or changing social routes.
    item=pick_item(queue,history)
    if item:
        now=datetime.now(timezone.utc).isoformat(); slug=slugify(item['title'])+'-'+fingerprint(item)[:8]
        record={**item,'slug':slug,'fingerprint':fingerprint(item),'published_at':now}
        (OUT/'articles'/f'{slug}.html').write_text(article_html(record))
        history.append(record); STATE.write_text(json.dumps(history,indent=2,ensure_ascii=False))
    STATE.write_text(json.dumps(history,indent=2,ensure_ascii=False))
    for record in history:
        (OUT/'articles'/f"{record['slug']}.html").write_text(article_html(record))
    (OUT/'index.html').write_text(build_index(history))
    (OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n')
    urls=[f'{BASE_URL}/']+[f'{BASE_URL}/articles/{x["slug"]}.html' for x in history]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{esc(u)}</loc></url>' for u in urls)+'</urlset>')
    print(json.dumps({'status':'ok','new_article':bool(item),'articles':len(history)}))
if __name__=='__main__':main()
