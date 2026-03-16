"""
Flask API for Gutteridge Price Tracker
Provides REST endpoints for product tracking and price history
"""

from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
import database as db
import scraper
import threading
import schedule
import time
import csv
import io
import json
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize database on startup
db.init_db()

def update_all_prices():
    """Update prices for all tracked products"""
    print(f"[{datetime.now()}] Starting price update...")
    products = db.get_all_products()
    
    for product in products:
        try:
            print(f"Updating: {product['name']}")
            scraped = scraper.scrape_product_page(product['url'])
            
            if scraped and scraped.get('current_price'):
                db.update_product_price(
                    product['id'],
                    scraped['current_price'],
                    scraped.get('original_price')
                )
                print(f"  Updated price: €{scraped['current_price']}")
            else:
                print(f"  Failed to scrape price")
                
            # Be polite to the server
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error updating {product['name']}: {e}")
    
    print(f"[{datetime.now()}] Price update completed")

def run_scheduler():
    """Run the price update scheduler"""
    # Update prices every 6 hours
    schedule.every(6).hours.do(update_all_prices)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# Start scheduler in background thread
scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

# ============ API Routes ============

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all tracked products"""
    products = db.get_all_products()
    return jsonify({
        'success': True,
        'products': products
    })

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product to track"""
    data = request.get_json()
    
    if not data or not data.get('url'):
        return jsonify({
            'success': False,
            'error': 'URL is required'
        }), 400
    
    url = data['url']
    
    # Check if product already exists
    existing = db.get_product_by_url(url)
    if existing:
        return jsonify({
            'success': True,
            'product': existing,
            'message': 'Product already being tracked'
        })
    
    # Scrape product data
    print(f"Scraping new product: {url}")
    product_data = scraper.scrape_product_page(url)
    
    if not product_data or not product_data.get('name'):
        return jsonify({
            'success': False,
            'error': 'Could not scrape product data. Please check the URL.'
        }), 400
    
    # Add to database
    product_id = db.add_product(
        url=url,
        name=product_data['name'],
        image_url=product_data.get('image_url'),
        category=product_data.get('category'),
        current_price=product_data.get('current_price'),
        original_price=product_data.get('original_price')
    )
    
    product = db.get_product(product_id)
    
    return jsonify({
        'success': True,
        'product': product,
        'message': 'Product added successfully'
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    return jsonify({
        'success': True,
        'product': product
    })

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    db.delete_product(product_id)
    
    return jsonify({
        'success': True,
        'message': 'Product deleted successfully'
    })

@app.route('/api/products/<int:product_id>/history', methods=['GET'])
def get_price_history(product_id):
    """Get price history for a product"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    limit = request.args.get('limit', 100, type=int)
    history = db.get_price_history(product_id, limit)
    stats = db.get_price_stats(product_id)
    
    return jsonify({
        'success': True,
        'product': product,
        'history': history,
        'stats': stats
    })

@app.route('/api/products/<int:product_id>/refresh', methods=['POST'])
def refresh_product(product_id):
    """Manually refresh a product's price"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    # Scrape current price
    scraped = scraper.scrape_product_page(product['url'])
    
    if not scraped:
        return jsonify({
            'success': False,
            'error': 'Could not scrape product data'
        }), 400
    
    # Update price
    if scraped.get('current_price'):
        db.update_product_price(
            product_id,
            scraped['current_price'],
            scraped.get('original_price')
        )
    
    # Update image if we got a new one
    if scraped.get('image_url') and not product.get('image_url'):
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET image_url = ? WHERE id = ?', 
                      (scraped['image_url'], product_id))
        conn.commit()
        conn.close()
    
    updated_product = db.get_product(product_id)
    
    return jsonify({
        'success': True,
        'product': updated_product,
        'message': 'Price refreshed successfully'
    })

@app.route('/api/products/refresh-all', methods=['POST'])
def refresh_all_products():
    """Refresh all products (runs in background)"""
    thread = threading.Thread(target=update_all_prices)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Price refresh started in background'
    })

@app.route('/api/search', methods=['GET'])
def search_products():
    """Search for products on Gutteridge"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    results = scraper.search_products(query)
    
    return jsonify({
        'success': True,
        'results': results
    })

@app.route('/api/products/<int:product_id>/images', methods=['GET'])
def get_product_images(product_id):
    """Get all images for a product"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    images = scraper.get_all_images_from_product(product['url'])
    
    return jsonify({
        'success': True,
        'images': images
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    products = db.get_all_products()
    
    total_products = len(products)
    total_price_records = 0
    
    for product in products:
        stats = db.get_price_stats(product['id'])
        total_price_records += stats.get('record_count', 0)
    
    return jsonify({
        'success': True,
        'stats': {
            'total_products': total_products,
            'total_price_records': total_price_records
        }
    })

@app.route('/api/products/<int:product_id>/export/csv', methods=['GET'])
def export_product_csv(product_id):
    """Export price history as CSV"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    history = db.get_price_history(product_id, limit=1000)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Price (EUR)', 'Original Price (EUR)', 'Discount %'])
    
    for record in history:
        discount = ''
        if record['original_price'] and record['original_price'] > record['price']:
            discount = f"{round((1 - record['price'] / record['original_price']) * 100)}%"
        writer.writerow([
            record['recorded_at'],
            record['price'],
            record['original_price'] or '',
            discount
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={product["name"]}_price_history.csv'}
    )

@app.route('/api/products/<int:product_id>/export/json', methods=['GET'])
def export_product_json(product_id):
    """Export price history as JSON"""
    product = db.get_product(product_id)
    
    if not product:
        return jsonify({
            'success': False,
            'error': 'Product not found'
        }), 404
    
    history = db.get_price_history(product_id, limit=1000)
    stats = db.get_price_stats(product_id)
    
    export_data = {
        'product': product,
        'statistics': stats,
        'price_history': history,
        'exported_at': datetime.now().isoformat()
    }
    
    return Response(
        json.dumps(export_data, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={product["name"]}_price_history.json'}
    )

@app.route('/api/products/export/all/csv', methods=['GET'])
def export_all_csv():
    """Export all products and their price history as CSV"""
    products = db.get_all_products()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Product Name', 'URL', 'Current Price', 'Original Price', 'Category', 'Last Updated'])
    
    for product in products:
        writer.writerow([
            product['name'],
            product['url'],
            product['current_price'] or '',
            product['original_price'] or '',
            product['category'] or '',
            product['updated_at']
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=all_products.csv'}
    )

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all price alerts"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT a.*, p.name as product_name, p.current_price, p.image_url
        FROM price_alerts a
        JOIN products p ON a.product_id = p.id
        WHERE a.is_active = 1
    ''')
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'alerts': alerts
    })

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new price alert"""
    data = request.get_json()
    
    if not data or not data.get('product_id') or not data.get('target_price'):
        return jsonify({
            'success': False,
            'error': 'Product ID and target price are required'
        }), 400
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO price_alerts (product_id, target_price, created_at)
        VALUES (?, ?, ?)
    ''', (data['product_id'], data['target_price'], datetime.now()))
    
    conn.commit()
    alert_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'alert_id': alert_id,
        'message': 'Alert created successfully'
    })

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete a price alert"""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM price_alerts WHERE id = ?', (alert_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Alert deleted successfully'
    })

@app.route('/api/alerts/check', methods=['POST'])
def check_alerts():
    """Check all alerts and return triggered ones"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.*, p.name as product_name, p.current_price, p.image_url
        FROM price_alerts a
        JOIN products p ON a.product_id = p.id
        WHERE a.is_active = 1 AND p.current_price <= a.target_price
    ''')
    
    triggered = [dict(row) for row in cursor.fetchall()]
    
    # Deactivate triggered alerts
    for alert in triggered:
        cursor.execute('UPDATE price_alerts SET is_active = 0 WHERE id = ?', (alert['id'],))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'triggered_alerts': triggered,
        'count': len(triggered)
    })

@app.route('/api/products/search', methods=['GET'])
def search_products_db():
    """Search tracked products"""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM products
        WHERE name LIKE ? OR category LIKE ? OR url LIKE ?
        ORDER BY updated_at DESC
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'products': products,
        'count': len(products)
    })

@app.route('/api/products/sort', methods=['GET'])
def get_products_sorted():
    """Get products sorted by various criteria"""
    sort_by = request.args.get('by', 'updated_at')
    order = request.args.get('order', 'desc')
    
    valid_sorts = ['name', 'current_price', 'original_price', 'updated_at', 'created_at']
    if sort_by not in valid_sorts:
        sort_by = 'updated_at'
    
    if order not in ['asc', 'desc']:
        order = 'desc'
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM products ORDER BY {sort_by} {order.upper()}')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'products': products
    })

if __name__ == '__main__':
    print("=" * 50)
    print("Gutteridge Price Tracker")
    print("=" * 50)
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
