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
    title=esc(a['title']); desc=esc(str(a.get('summary') or a.get('lead') or a['title'])[:155])
    body=esc(a.get('body') or a.get('summary') or '').replace('\n','</p><p>')
    view=esc(a.get('market_view') or 'EXIMUTC follows verified developments in the natural gemstone and fine-jewelry market and separates sourced facts from market commentary.')
    src=esc(a['source_url']); source=esc(a.get('source') or urlparse(a['source_url']).netloc)
    canonical=f"{BASE_URL}/articles/{a['slug']}.html"
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} | EXIMUTC News</title><meta name="description" content="{desc}"><link rel="canonical" href="{canonical}"><meta property="og:type" content="article"><meta property="og:url" content="{canonical}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE_URL}/assets/gemstone-news.svg"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{BASE_URL}/assets/gemstone-news.svg"><style>*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;margin:auto;max-width:900px;padding:28px;color:#151515;line-height:1.65}}header{{border-bottom:1px solid #ddd;margin-bottom:32px}}a{{color:#075985;overflow-wrap:anywhere}}h1,h2,p{{overflow-wrap:anywhere}}@media(max-width:480px){{body{{padding:20px 16px}}}}.view{{background:#f5f7f8;padding:20px;margin:30px 0}}small{{color:#666}}</style></head><body><header><h2>EXIMUTC NEWS</h2><p><a href="../">Natural Gemstones & Fine Jewelry Market Intelligence</a></p></header><main><h1>{title}</h1><time datetime="{esc(a['published_at'])}">{esc(display_date(a['published_at']))}</time>{news_image('../assets/gemstone-news.svg')}<p>{body}</p><section class="view"><h2>EXIMUTC Market View</h2><p>{view}</p></section><h2>Source</h2><p>{source}: <a href="{src}" rel="nofollow noopener">{src}</a></p></main><footer><hr><p>EXIMUTC, INC. · <a href="https://eximutc.com">eximutc.com</a></p></footer></body></html>'''

def build_index(history):
    cards=''.join(f'<article><h2><a href="articles/{esc(x["slug"])}.html">{esc(x["title"])}</a></h2><p>{esc(x.get("summary",""))}</p><time datetime="{esc(x["published_at"])}">{esc(display_date(x["published_at"]))}</time></article>' for x in reversed(history))
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EXIMUTC News | Natural Gemstones & Fine Jewelry</title><meta name="description" content="EXIMUTC market news and analysis covering natural gemstones, gemology, auctions and fine jewelry."><link rel="canonical" href="{BASE_URL}/"><meta property="og:type" content="website"><meta property="og:url" content="{BASE_URL}/"><meta property="og:title" content="EXIMUTC News | Natural Gemstones &amp; Fine Jewelry"><meta property="og:description" content="EXIMUTC market news and analysis covering natural gemstones, gemology, auctions and fine jewelry."><meta property="og:image" content="{BASE_URL}/assets/gemstone-news.svg"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{BASE_URL}/assets/gemstone-news.svg"><style>*{{box-sizing:border-box}}body{{font-family:Arial,sans-serif;margin:auto;max-width:1000px;padding:28px;color:#151515}}header{{padding:35px 0;border-bottom:1px solid #ddd}}article{{padding:22px 0;border-bottom:1px solid #eee}}a{{color:#075985;overflow-wrap:anywhere}}h1,h2,p{{overflow-wrap:anywhere}}@media(max-width:480px){{body{{padding:20px 16px}}}}</style></head><body><header><h1>EXIMUTC NEWS</h1><p>Natural Gemstones & Fine Jewelry Market Intelligence</p><p><a href="https://eximutc.com">EXIMUTC.COM</a></p></header>{cards or '<p>Editorial feed is being prepared.</p>'}</body></html>'''

def build_embed(history, limit=3):
    latest=list(reversed(history[-limit:]))
    cards=''.join(
        f'<article><time datetime="{esc(x["published_at"])}">{esc(display_date(x["published_at"]))}</time>'
        f'<h3><a href="{BASE_URL}/articles/{esc(x["slug"])}.html" target="_top">{esc(x["title"])}</a></h3>'
        f'<p>{esc(str(x.get("summary",""))[:220])}</p></article>'
        for x in latest
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Latest EXIMUTC News</title><style>*{{box-sizing:border-box}}html,body{{margin:0;padding:0;background:transparent}}body{{font-family:Arial,sans-serif;color:#111}}.wrap{{max-width:1100px;margin:0 auto;padding:8px 4px 12px}}h2{{font-size:clamp(26px,4vw,42px);font-weight:600;letter-spacing:.01em;margin:0 0 18px}}article{{padding:18px 0;border-top:1px solid rgba(0,0,0,.14)}}article:first-of-type{{border-top:0;padding-top:0}}time{{display:block;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:#5f6570;margin-bottom:6px}}h3{{font-size:clamp(18px,2.4vw,26px);line-height:1.2;margin:0 0 7px}}p{{font-size:15px;line-height:1.5;margin:0;color:#333}}a{{color:#0b245c;text-decoration:none}}a:hover,a:focus{{text-decoration:underline}}.all{{display:inline-block;margin-top:18px;font-weight:600}}@media(max-width:480px){{.wrap{{padding:4px 2px 10px}}article{{padding:15px 0}}}}</style></head><body><section class="wrap" aria-labelledby="latest-news-title"><h2 id="latest-news-title">Latest News</h2>{cards or '<p>Editorial feed is being prepared.</p>'}<a class="all" href="{BASE_URL}/" target="_top">View all EXIMUTC News →</a></section></body></html>'''

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
    (OUT/'embed.html').write_text(build_embed(history))
    (OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n')
    urls=[f'{BASE_URL}/']+[f'{BASE_URL}/articles/{x["slug"]}.html' for x in history]
    (OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{esc(u)}</loc></url>' for u in urls)+'</urlset>')
    print(json.dumps({'status':'ok','new_article':bool(item),'articles':len(history)}))
if __name__=='__main__':main()
