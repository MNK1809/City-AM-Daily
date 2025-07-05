#!/usr/bin/env python3
"""
City A.M. Blog Content Extractor for GitHub Actions
Automatically extracts daily summaries from City A.M. RSS feeds
Optimized for automated GitHub Actions workflow
"""

import feedparser
import requests
from datetime import datetime, timedelta
import re
import html
import os
import sys

class CityAMExtractor:
    def __init__(self):
        self.rss_feeds = {
            'news': 'https://www.cityam.com/news/rss',
            'business': 'https://www.cityam.com/news/feed'
        }
        self.base_url = 'https://www.cityam.com'
        
        # GitHub Actions specific settings
        self.output_dir = 'summaries'
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def clean_html(self, text):
        """Remove HTML tags and clean up text"""
        if not text:
            return ""
        
        # Remove HTML tags
        clean = re.compile('<.*?>')
        text = re.sub(clean, '', text)
        # Decode HTML entities
        text = html.unescape(text)
        # Clean up whitespace
        text = ' '.join(text.split())
        return text
    
    def extract_articles(self, feed_name='news', max_articles=5):
        """Extract articles from specified RSS feed"""
        feed_url = self.rss_feeds.get(feed_name)
        if not feed_url:
            raise ValueError(f"Unknown feed: {feed_name}")
        
        try:
            print(f"Fetching content from: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            if feed.bozo:
                print(f"Warning: Feed parsing issues - {feed.bozo_exception}")
            
            if not feed.entries:
                print("No articles found in feed")
                return None
            
            articles = []
            for entry in feed.entries[:max_articles]:
                # Clean and extract content
                title = self.clean_html(entry.get('title', 'No title'))
                summary = self.clean_html(entry.get('summary', entry.get('description', '')))
                
                # Limit summary length for blog use
                if len(summary) > 300:
                    summary = summary[:297] + '...'
                
                article = {
                    'title': title,
                    'link': entry.get('link', ''),
                    'summary': summary,
                    'published': entry.get('published', ''),
                    'author': entry.get('author', 'City A.M.'),
                    'categories': [tag.term for tag in entry.get('tags', [])]
                }
                articles.append(article)
            
            print(f"Successfully extracted {len(articles)} articles")
            
            return {
                'feed_title': feed.feed.get('title', 'City A.M. News'),
                'feed_description': feed.feed.get('description', ''),
                'last_updated': feed.feed.get('updated', ''),
                'articles': articles
            }
        
        except Exception as e:
            print(f"Error extracting from feed {feed_url}: {e}")
            return None
    
    def generate_blog_post(self, feed_data, blog_name="Business News Blog", author_name="Automated Summary"):
        """Generate a blog post from feed data with proper attribution"""
        if not feed_data or not feed_data['articles']:
            return "No articles available for summary."
        
        today = datetime.now().strftime('%B %d, %Y')
        
        # Blog post header
        post = f"""# Daily Business News Summary - {today}
*Curated from City A.M. Business News*

---

Good morning! Here's your daily roundup of the top business stories from City A.M., London's leading business newspaper.

"""
        
        # Add articles
        for i, article in enumerate(feed_data['articles'], 1):
            categories_text = ', '.join(article['categories']) if article['categories'] else 'Business News'
            
            post += f"""## {i}. {article['title']}

**Summary**: {article['summary']}

**Categories**: {categories_text}

**[Read the full article at City A.M.]({article['link']})**

---

"""
        
        # Footer with attribution
        post += f"""
## About This Summary

This daily summary is automatically curated from [City A.M.]({self.base_url}), London's premier business newspaper. All original reporting and content rights belong to City A.M. 

*Summary compiled by {author_name} for {blog_name} | Original content © City A.M.*

**Want to stay updated?** 
- Visit [City A.M.]({self.base_url}) for complete coverage
- Download their [free mobile app](https://www.cityam.com/apps/)
- Subscribe to their newsletters

---
*Disclaimer: This is a curated summary for informational purposes. Please visit the original articles for complete reporting and context.*

*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*
"""
        
        return post
    
    def save_blog_post(self, content, filename=None):
        """Save blog post to file in summaries directory"""
        if not filename:
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"cityam_summary_{date_str}.md"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Blog post saved to: {filepath}")
        return filepath
    
    def update_index(self, new_filename):
        """Update index.md with latest summary"""
        index_path = "README.md"
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Create or update README with latest summary link
        readme_content = f"""# Daily City A.M. Business News Summaries

This repository automatically generates daily business news summaries from City A.M.'s RSS feed.

## Latest Summary
📰 **[{date_str} Summary](summaries/{os.path.basename(new_filename)})**

## About
- **Source**: [City A.M.](https://www.cityam.com) - London's leading business newspaper
- **Update Frequency**: Daily at 8:00 AM UTC
- **Content**: Top 5 business stories with summaries and links to full articles
- **Legal**: All content properly attributed with links to original sources

## Archive
All daily summaries are stored in the [`summaries/`](summaries/) directory.

## How It Works
This repository uses GitHub Actions to automatically:
1. Fetch the latest articles from City A.M.'s RSS feed
2. Generate formatted summaries with proper attribution
3. Commit and push the new content daily

---
*Automated by GitHub Actions | Content © City A.M.*
"""
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"Updated {index_path}")
    
    def run_daily_extraction(self):
        """Main method for daily extraction - optimized for GitHub Actions"""
        print("=" * 50)
        print("City A.M. Daily Content Extraction")
        print("=" * 50)
        
        try:
            # Extract content
            feed_data = self.extract_articles('news', max_articles=5)
            
            if not feed_data:
                print("❌ Failed to extract content from RSS feed")
                sys.exit(1)
            
            # Generate blog post
            blog_content = self.generate_blog_post(feed_data)
            
            # Save blog post
            filename = self.save_blog_post(blog_content)
            
            # Update index
            self.update_index(filename)
            
            print("✅ Daily extraction completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            sys.exit(1)

def main():
    """Main execution for GitHub Actions"""
    extractor = CityAMExtractor()
    extractor.run_daily_extraction()

if __name__ == "__main__":
    main()

