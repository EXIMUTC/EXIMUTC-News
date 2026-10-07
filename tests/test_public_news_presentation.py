import unittest
from html.parser import HTMLParser
from automation.website_news import publisher


class Metadata(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.values = {}
        self.links = []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.values[attrs.get('name') or attrs.get('property')] = attrs.get('content')
        if tag == 'a':
            self.links.append(attrs.get('href'))


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


if __name__ == '__main__':
    unittest.main()
