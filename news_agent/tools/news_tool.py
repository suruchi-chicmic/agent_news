import requests
import xml.etree.ElementTree as ET
from typing import Union

def fetch_news(query: str, page_size: int = 10, country: Union[str, None] = None, category: Union[str, None] = None):
    # Use category in the query if provided
    search_query = f"{query} topic:{category}" if category else query
    
    if country:
        url = f"https://news.google.com/rss/search?q={search_query}&hl=en-{country.upper()}&gl={country.upper()}&ceid={country.upper()}:en"
    else:
        url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
    print("-----------url i am hitting is---------------",url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        results = []
        for i, item in enumerate(items):
            if i >= page_size: break
            results.append({
                "title": item.find('title').text if item.find('title') is not None else "No Title",
                "source": item.find('source').text if item.find('source') is not None else "Google News",
                "description": item.find('description').text if item.find('description') is not None else "",
                "url": item.find('link').text if item.find('link') is not None else "",
                "publishedAt": item.find('pubDate').text if item.find('pubDate') is not None else ""
            })
        return results if results else "No news found."
    except Exception as e:
        return f"Error: {str(e)}"