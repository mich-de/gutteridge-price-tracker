"""
Web scraper for Gutteridge.com
Extracts product information including name, price, and images
Uses requests with proper headers to bypass anti-bot protection
"""

import requests
import gzip
import brotli
import io
from bs4 import BeautifulSoup
import re
import json
import time
import warnings
import urllib3
from urllib.parse import urljoin, urlparse

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

BASE_URL = 'https://www.gutteridge.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# Global session
_session = None

def get_session():
    """Get or create requests Session"""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session

def get_page(url, retries=3):
    """Fetch a page with retries - tries requests first, then Selenium"""
    # First try with requests
    session = get_session()
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            # Use response.text which handles decompression automatically
            html = response.text
            
            # Check if page has meaningful content
            if len(html) > 10000:
                return html
        except Exception as e:
            print(f"Requests attempt {attempt + 1} failed for {url}: {e}")
            # Reset session on failure
            global _session
            _session = None
    
    return None

def parse_price(price_text):
    """Parse price from text like '€ 199,00' or '199,00 €' or '259.00'"""
    if not price_text:
        return None
    
    # Convert to string if needed
    price_text = str(price_text)
    
    # Remove currency symbols and whitespace
    price_text = price_text.replace('€', '').replace('EUR', '').strip()
    
    # Handle different decimal formats
    # If format is like "259.00" (dot as decimal separator)
    if '.' in price_text and ',' not in price_text:
        try:
            return float(price_text)
        except ValueError:
            pass
    
    # If format is like "259,00" (comma as decimal separator)
    if ',' in price_text:
        # Replace comma with dot
        price_text = price_text.replace('.', '').replace(',', '.')
    
    try:
        return float(price_text)
    except ValueError:
        # Try to extract number with regex
        match = re.search(r'(\d+[.,]?\d*)', price_text)
        if match:
            return float(match.group(1).replace(',', '.'))
    return None

def scrape_product_page(url):
    """
    Scrape a single product page
    Returns dict with product info
    """
    print(f"Scraping product: {url}")
    html = get_page(url)
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    product_data = {
        'url': url,
        'name': None,
        'image_url': None,
        'current_price': None,
        'original_price': None,
        'category': None,
        'description': None,
        'sku': None,
        'sizes': [],
        'colors': []
    }
    
    # Try to extract from JSON-LD structured data
    json_ld = soup.find('script', type='application/ld+json')
    if json_ld:
        try:
            data = json.loads(json_ld.string)
            if isinstance(data, list):
                data = data[0]
            
            product_data['name'] = data.get('name')
            product_data['description'] = data.get('description')
            product_data['sku'] = data.get('sku')
            
            # Get image
            image = data.get('image')
            if image:
                if isinstance(image, list):
                    product_data['image_url'] = image[0]
                else:
                    product_data['image_url'] = image
            
            # Get price from offers
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0]
            
            product_data['current_price'] = offers.get('price')
            if not product_data['current_price']:
                product_data['current_price'] = offers.get('lowPrice')
                
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing JSON-LD: {e}")
    
    # Fallback: Extract from HTML elements
    if not product_data['name']:
        # Try common selectors for product name
        name_selectors = [
            'h1.product-name',
            'h1.product-title',
            '.product-info h1',
            '[data-testid="product-name"]',
            'h1'
        ]
        for selector in name_selectors:
            elem = soup.select_one(selector)
            if elem:
                product_data['name'] = elem.get_text(strip=True)
                break
    
    if not product_data['image_url']:
        # Try to find main product image
        img_selectors = [
            '.product-image img',
            '.product-gallery img',
            '[data-testid="product-image"] img',
            '.pdp-image img',
            'img.product-img'
        ]
        for selector in img_selectors:
            elem = soup.select_one(selector)
            if elem:
                src = elem.get('src') or elem.get('data-src') or elem.get('data-lazy-src')
                if src:
                    product_data['image_url'] = urljoin(url, src)
                    break
        
        # Try og:image as fallback
        if not product_data['image_url']:
            og_image = soup.find('meta', property='og:image')
            if og_image:
                product_data['image_url'] = og_image.get('content')
    
    if not product_data['current_price']:
        # Try to find price in HTML - Gutteridge specific selectors
        price_selectors = [
            'span.sales.outlet-price span.value',
            'span.sales span.value',
            '.price span.value',
            '.product-price .current-price',
            '.product-price .price',
            '.price-current',
            '[data-testid="product-price"]',
            '.pdp-price .price',
            '.product-info .price'
        ]
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                # Try content attribute first, then text
                price_val = elem.get('content') or elem.get_text()
                product_data['current_price'] = parse_price(price_val)
                if product_data['current_price']:
                    break
    
    # Try to find original price (before discount)
    original_price_selectors = [
        'span.strike-through.list span.value',
        'del span.value',
        '.product-price .original-price',
        '.product-price .old-price',
        '.price-original',
        '.price-old',
        '.was-price',
        's.price',
        'del.price'
    ]
    for selector in original_price_selectors:
        elem = soup.select_one(selector)
        if elem:
            # Try content attribute first, then text
            price_val = elem.get('content') or elem.get_text()
            product_data['original_price'] = parse_price(price_val)
            if product_data['original_price']:
                break
    
    # Extract category from breadcrumb
    breadcrumb = soup.select('.breadcrumb a, .breadcrumbs a, nav[aria-label="breadcrumb"] a')
    if breadcrumb:
        categories = [a.get_text(strip=True) for a in breadcrumb if a.get_text(strip=True)]
        if categories:
            product_data['category'] = ' > '.join(categories)
    
    # Extract sizes
    size_selectors = [
        '.size-selector button',
        '.size-options button',
        '[data-testid="size-option"]',
        '.product-sizes button'
    ]
    for selector in size_selectors:
        sizes = soup.select(selector)
        if sizes:
            product_data['sizes'] = [s.get_text(strip=True) for s in sizes]
            break
    
    # Extract colors
    color_selectors = [
        '.color-selector button',
        '.color-options button',
        '[data-testid="color-option"]',
        '.product-colors button'
    ]
    for selector in color_selectors:
        colors = soup.select(selector)
        if colors:
            product_data['colors'] = [c.get('title') or c.get('aria-label') or c.get_text(strip=True) for c in colors]
            break
    
    return product_data

def scrape_category_page(url, max_products=50):
    """
    Scrape a category page to get product links
    Returns list of product URLs
    """
    print(f"Scraping category: {url}")
    html = get_page(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    product_urls = []
    
    # Try to find product links
    link_selectors = [
        '.product-tile a',
        '.product-card a',
        '.product-item a',
        '[data-testid="product-tile"] a',
        '.products-grid a.product-link'
    ]
    
    for selector in link_selectors:
        links = soup.select(selector)
        if links:
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(url, href)
                    if full_url not in product_urls and '/it_IT/' in full_url:
                        product_urls.append(full_url)
                        if len(product_urls) >= max_products:
                            break
            if product_urls:
                break
    
    return product_urls

def search_products(query, max_results=20):
    """
    Search for products on Gutteridge
    Returns list of product data
    """
    search_url = f"{BASE_URL}/it_IT/search?q={query}"
    print(f"Searching: {search_url}")
    
    html = get_page(search_url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    products = []
    
    # Try to find product tiles
    tile_selectors = [
        '.product-tile',
        '.product-card',
        '.product-item',
        '[data-testid="product-tile"]'
    ]
    
    for selector in tile_selectors:
        tiles = soup.select(selector)
        if tiles:
            for tile in tiles[:max_results]:
                product = {}
                
                # Get link
                link = tile.select_one('a')
                if link:
                    href = link.get('href')
                    if href:
                        product['url'] = urljoin(BASE_URL, href)
                
                # Get name
                name_elem = tile.select_one('.product-name, .product-title, h3, h2')
                if name_elem:
                    product['name'] = name_elem.get_text(strip=True)
                
                # Get image
                img = tile.select_one('img')
                if img:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        product['image_url'] = urljoin(BASE_URL, src)
                
                # Get price
                price_elem = tile.select_one('.price, .product-price')
                if price_elem:
                    product['current_price'] = parse_price(price_elem.get_text())
                
                if product.get('url'):
                    products.append(product)
            
            break
    
    return products

def get_all_images_from_product(url):
    """
    Get all images from a product page
    Returns list of image URLs
    """
    print(f"Getting all images from: {url}")
    html = get_page(url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    images = []
    
    # Try to find product gallery images
    gallery_selectors = [
        '.product-gallery img',
        '.product-images img',
        '.pdp-gallery img',
        '[data-testid="product-gallery"] img',
        '.swiper-slide img'
    ]
    
    for selector in gallery_selectors:
        imgs = soup.select(selector)
        if imgs:
            for img in imgs:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src and src not in images:
                    full_url = urljoin(url, src)
                    # Filter out small icons and placeholders
                    if not any(x in src.lower() for x in ['icon', 'logo', 'placeholder', 'blank']):
                        images.append(full_url)
            if images:
                break
    
    # Also check for JSON data with images
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'productImages' in script.string:
            try:
                # Try to extract image URLs from JavaScript
                matches = re.findall(r'https?://[^\s"\'\]]+\.(?:jpg|jpeg|png|webp)', script.string)
                for match in matches:
                    if match not in images and not any(x in match.lower() for x in ['icon', 'logo']):
                        images.append(match)
            except:
                pass
    
    return images

if __name__ == '__main__':
    # Test with a sample product URL
    test_url = 'https://www.gutteridge.com/it_IT/giacca-in-lana-con-revers-a-lancia-C2GUCAS220219999.html'
    result = scrape_product_page(test_url)
    print(json.dumps(result, indent=2, ensure_ascii=False))
