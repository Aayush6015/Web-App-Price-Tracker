from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import threading
from scheduler import *

app = Flask(__name__)

client = MongoClient("mongodb+srv://bithional:CSZuAvvAc3WEzl2I@cluster.oou5h.mongodb.net/")
db = client["price_tracker"]
products_collection = db["products"]

# Flask route to display price variation graph for a specific product
@app.route('/product/<product_id>/graph')
def view_graph(product_id):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    
    # Extract price history and timestamps
    prices = product.get('price_history', [])
    timestamps = product.get('timestamps', [])

    if not prices or not timestamps:
        return "No price data available for this product", 404

    # Create a plot for price variation over time
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, prices, marker='o', linestyle='-', color='b')
    plt.xlabel('Date')
    plt.ylabel('Price (in currency)')
    plt.title(f"Price Variation for {product['name']}")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save plot to a buffer and encode as base64 to embed in HTML
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    graph_url = base64.b64encode(img.getvalue()).decode('utf-8')
    plt.close()

    return render_template('graph.html', graph_url=graph_url)
    
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form['name']
        product_url = request.form['url']
        products_collection.insert_one({
            'name': product_name,
            'url': product_url,
            'price': None,  
            'last_updated': None,  
        })
        scrape_price(product_url)
        update_prices()
        return redirect(url_for('index'))
    products = products_collection.find()
    return render_template('index.html', products=products)
@app.route('/product/<product_id>')
def view_product(product_id):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    return render_template('product.html', product=product)

@app.route('/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    result = products_collection.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count > 0:
        print(f"Successfully deleted product with ID {product_id}")
    else:
        print(f"Failed to delete product with ID {product_id}")
    
    return redirect(url_for('index'))

def start_scheduler():
    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True  # Ensure it exits when the main program exits
    thread.start()

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)

