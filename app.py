from flask import Flask, request, jsonify, render_template, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from pymongo import MongoClient
from datetime import datetime
from bson.objectid import ObjectId
import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64
import threading
from scheduler import *
import time
import re


# Initialize Flask app
app = Flask(__name__)

# MongoDB connection
client = MongoClient("mongodb+srv://bithional:CSZuAvvAc3WEzl2I@cluster.oou5h.mongodb.net/")
db = client.price_tracker
products_collection = db.products

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

# Modify insert_one logic in index route to add price history and timestamps
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        product_name = request.form['name']
        product_url = request.form['url']
        user_email = request.form['email']  # Capture user email
        
        # Save product info and email to MongoDB
        products_collection.insert_one({
            'name': product_name,
            'url': product_url,
            'price': None,  # Price will be updated by the scheduler
            'last_updated': None,  # To track last price update
            'email': user_email  # Store user email
        })
        scrape_price(product_url)
        update_prices()
        return redirect(url_for('index'))
    
    # Get all products from the database to display on the front page
    products = products_collection.find()
    return render_template('index.html', products=products)
# Flask route to view details of a specific product
@app.route('/product/<product_id>')
def view_product(product_id):
    product = products_collection.find_one({"_id": ObjectId(product_id)})
    return render_template('product.html', product=product)

def start_scheduler():
    thread = threading.Thread(target=run_scheduler)
    thread.daemon = True  # Ensure it exits when the main program exits
    thread.start()

if __name__ == '__main__':
    start_scheduler()
    app.run(debug=True)





# client = MongoClient("mongodb+srv://bithional:CSZuAvvAc3WEzl2I@cluster.oou5h.mongodb.net/")