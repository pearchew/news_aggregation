import feedparser
import logging

logger = logging.getLogger(__name__)


bis_innovation_hub_feed = feedparser.parse('https://www.bis.org/doclist/bisih_publications.rss')
finextra_headline_feed = feedparser.parse('https://www.finextra.com/rss/headlines.aspx')
finextra_blog_feed = feedparser.parse('https://www.finextra.com/rss/blogs.aspx')
finextra_ai_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=ai')
finextra_payments_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=payments')
finextra_regulation_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=regulation')
finextra_crime_feed = feedparser.parse('https://www.finextra.com/rss/channel.aspx?channel=crime')