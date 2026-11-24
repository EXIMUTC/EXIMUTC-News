import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from automation.website_news import publisher, verify_production


class Metadata(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.values = {}
        self.links = []
        self.images = []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.values[attrs.get('name') or attrs.get('property')] = attrs.get('content')
        if tag == 'a':
            self.links.append(attrs.get('href'))
        if tag == 'img':
            self.images.append(attrs.get('src'))


def article(i=0):
    return dict(title=f'Gemology news {i}', summary='Natural gemstone research.',
                body='Verified source summary.', market_view='EXIMUTC market view.',
                source_url='https://example.org/research', source='Research institution',
                slug=f'gemology-news-{i}', published_at='2026-10-07T02:35:37+00:00')


class PublicNewsPresentationTests(unittest.TestCase):
    def test_description_truncates_text_before_escaping(self):
        item = article()
        item['summary'] = 'a' * 154 + '" & gem research'
        meta = Metadata(publisher.article_html(item))
        self.assertEqual(meta.values['description'], item['summary'][:155])
        self.assertEqual(meta.values['og:description'], item['summary'][:155])

    def test_archive_retains_every_existing_article_url(self):
        history = [article(i) for i in range(35)]
        links = Metadata(publisher.build_index(history)).links
        for item in history:
            self.assertIn('articles/' + item['slug'] + '.html', links)
        self.assertEqual(len([x for x in links if x.startswith('articles/')]), 35)

    def test_social_preview_binds_exact_production_url(self):
        item = article()
        meta = Metadata(publisher.article_html(item))
        self.assertEqual(meta.values.get('og:url'),
                         'https://news.eximutc.com/articles/gemology-news-0.html')
        self.assertEqual(meta.values.get('twitter:card'), 'summary_large_image')
        index = Metadata(publisher.build_index([item]))
        self.assertEqual(index.values.get('og:url'), 'https://news.eximutc.com/')

    def test_homepage_embed_uses_three_latest_articles_and_absolute_links(self):
        history = [article(i) for i in range(5)]
        page = publisher.build_embed(history)
        links = Metadata(page).links
        article_links = [x for x in links if '/articles/' in x]
        self.assertEqual(len(article_links), 3)
        self.assertIn('https://news.eximutc.com/articles/gemology-news-4.html', article_links)
        self.assertIn('https://news.eximutc.com/articles/gemology-news-2.html', article_links)
        self.assertNotIn('https://news.eximutc.com/articles/gemology-news-1.html', article_links)
        self.assertIn('https://news.eximutc.com/', links)

    def test_homepage_embed_shows_only_the_latest_reviewed_photo(self):
        history = [article(i) for i in range(2)]
        history[0]['image'] = reviewed_photo('older.jpg')
        history[1]['image'] = reviewed_photo('newest.jpg')
        page = publisher.build_embed(history)
        self.assertEqual(Metadata(page).images, [history[1]['image']['url']])
        self.assertIn('Editorial test photograph', page)

    def test_production_accepts_verified_photo_and_detects_changed_bytes(self):
        item = article()
        item['published_at'] = datetime.now(timezone.utc).isoformat()
        item['image'] = reviewed_photo('latest.jpg')
        pages = {
            verify_production.BASE: publisher.build_index([item]),
            verify_production.BASE + 'articles/' + item['slug'] + '.html': publisher.article_html(item),
        }
        with patch.object(verify_production, 'read', side_effect=pages.__getitem__):
            with patch.object(verify_production, 'read_bytes',
                              return_value=(b'approved test photo', 'image/jpeg')):
                verify_production.verify(item)
            with patch.object(verify_production, 'read_bytes',
                              return_value=(b'unexpected bytes', 'image/jpeg')):
                with self.assertRaisesRegex(ValueError, 'does not match the reviewed image'):
                    verify_production.verify(item)

    def test_approved_export_never_falls_back_to_older_queue_rows(self):
        older, approved = article(1), article(2)
        approved_fingerprint = publisher.fingerprint(approved)
        queue = {
            'status': 'APPROVED_FOR_PUBLISHING',
            'exported_latest_fingerprint': approved_fingerprint,
            'items': [older, approved],
        }
        self.assertEqual(publisher.pick_item(queue, [], approved_export_only=True), approved)
        self.assertIsNone(publisher.pick_item(
            queue, [{'fingerprint': approved_fingerprint}], approved_export_only=True))
        queue['exported_latest_fingerprint'] = 'a' * 64
        self.assertIsNone(publisher.pick_item(queue, [], approved_export_only=True))

    def test_delayed_exact_export_preserves_newer_story_at_top(self):
        delayed, latest = article(1), article(2)
        delayed['published_at'] = '2026-11-24T01:30:00-05:00'
        latest['published_at'] = '2026-11-24T12:30:00+00:00'
        latest['fingerprint'] = publisher.fingerprint(latest)
        queue = {
            'status': 'APPROVED_FOR_PUBLISHING',
            'exported_latest_fingerprint': publisher.fingerprint(delayed),
            'items': [delayed],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output, state, queue_path = root / 'docs', root / 'history.json', root / 'queue.json'
            state.write_text(json.dumps([latest]))
            queue_path.write_text(json.dumps(queue))
            with patch.multiple(publisher, OUT=output, STATE=state, QUEUE=queue_path):
                publisher.main(approved_export_only=True)
            history = json.loads(state.read_text())
            self.assertEqual([x['title'] for x in history], [delayed['title'], latest['title']])
            self.assertEqual(history[0]['published_at'], delayed['published_at'])
            self.assertTrue((output / 'articles' / (history[0]['slug'] + '.html')).exists())
            for page in ('index.html', 'embed.html'):
                links = Metadata((output / page).read_text()).links
                self.assertTrue(next(x for x in links if 'articles/' in x).endswith(latest['slug'] + '.html'))


def reviewed_photo(name):
    return {
        'url': 'https://example.org/' + name,
        'width': 1200,
        'height': 800,
        'mime_type': 'image/jpeg',
        'sha256': hashlib.sha256(b'approved test photo').hexdigest(),
        'credit': 'Editorial test photograph • CC0',
        'license': 'CC0-1.0',
    }


if __name__ == '__main__':
    unittest.main()
