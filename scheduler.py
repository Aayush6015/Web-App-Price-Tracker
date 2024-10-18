# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from bs4 import BeautifulSoup
# from pymongo import MongoClient
# from datetime import datetime
# import schedule
# import time
# import re

# # MongoDB connection
# client = MongoClient("mongodb+srv://bithional:CSZuAvvAc3WEzl2I@cluster.mongodb.net/myDatabase?retryWrites=true&w=majority")
# db = client.price_tracker
# products_collection = db.products

# # Selenium setup (headless mode)
# chrome_options = Options()
# chrome_options.add_argument("--headless=old")  # Run in headless mode
# chrome_options.add_argument("--disable-gpu")  # Disable GPU usage (optional)
# chrome_options.add_argument("--no-sandbox")  # Required if running as root (Linux environments)
# chrome_options.add_argument("--disable-dev-shm-usage") 
# chrome_options.add_argument("--window-size=1920x1080")
# chrome_options.add_argument("--blink-settings=imagesEnabled=false")

# driver = webdriver.Chrome(service=Service('<path-to-your-chromedriver>'), options=chrome_options)

# # Function to scrape price using Selenium and BeautifulSoup
# def scrape_price(url):
#     driver.get(url)
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
    
#     # Logic to extract the price from the page (customize for your page)
#     price = None
#     if "amazon" in url:  # Example for Amazon
#         price = soup.find("span", {"id": "priceblock_ourprice"}).get_text(strip=True)
#     elif "ebay" in url:  # Example for eBay
#         price = soup.find("span", {"id": "prcIsum"}).get_text(strip=True)

#     if price:
#         price = re.sub(r'[^\d.]', '', price)  # Extract numeric value from price string
    
#     return price

# # Function to update prices for all products
# def update_prices():
#     products = products_collection.find()
#     for product in products:
#         new_price = scrape_price(product['url'])
#         if new_price:
#             products_collection.update_one(
#                 {'_id': product['_id']},
#                 {"$set": {'price': new_price, 'last_updated': datetime.now()}}
#             )
#             print(f"Updated price for {product['name']} to {new_price}")

# # Scheduler function to run daily at a specific time (e.g., midnight)
# def run_scheduler():
#     schedule.every().day.at("00:00").do(update_prices)
    
#     while True:
#         schedule.run_pending()
#         time.sleep(60)  # Sleep for 60 seconds between checks

# if __name__ == '__main__':
#     run_scheduler()

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# MongoDB connection
client = MongoClient("mongodb+srv://bithional:CSZuAvvAc3WEzl2I@cluster.oou5h.mongodb.net/")
db = client["price_tracker"]
products_collection = db["products"]

# Selenium setup (headless mode)
chrome_options = Options()
chrome_options.add_argument("--headless=old")  # Run in headless mode
chrome_options.add_argument("--disable-gpu")  # Disable GPU usage (optional)
chrome_options.add_argument("--no-sandbox")  # Required if running as root (Linux environments)
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--blink-settings=imagesEnabled=false")

driver = webdriver.Chrome(service=Service(), options=chrome_options)

# Function to scrape price using Selenium and BeautifulSoup
def scrape_price(url):
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    # Logic to extract the price from the page (customize for your page)
    price = None
    if "amazon." in url: 
        price = soup.find(class_ = "a-price-whole").get_text(strip=True)
    elif "flipkart." in url:  
        price = (soup.find(class_ = "Nx9bqj CxhGGd").get_text(strip=True))[1:]
    elif "myntra." in url:
        price = (soup.find(class_="pdp-price").get_text(strip=True))[1:]
    elif "thesouledstore." in url:
        price = ((soup.find(class_="leftPrice pull-right").get_text(strip=True))[1:]).strip()
    elif "ajio." in url:
        price = (soup.find(class_="prod-sp").get_text(strip=True))
    elif "nykaa." in url:
        price = (soup.find(class_="css-1jczs19").get_text())
    if price:
        price = re.sub(r'[^\d.]', '', price)  # Extract numeric value from price string
    
    print(price)
    return price

# Function to update prices for all products
# def update_prices():
#     products = products_collection.find()
#     for product in products:
#         print(f"Scraping price for {product['name']} from {product['url']}")
#         new_price = scrape_price(product['url'])
#         if new_price:
#             print(f"New price for {product['name']}: {new_price}")
#             update_result = products_collection.update_one(
#                 {'_id': product['_id']},
#                 {"$set": {'price': new_price, 'last_updated': datetime.now()}}
#             )
#             if update_result.modified_count > 0:
#                 print(f"Successfully updated price for {product['name']} in the database")
#             else:
#                 print(f"Failed to update price for {product['name']} in the database")
#         else:
#             print(f"Failed to scrape price for {product['name']}")
def update_prices():
    products = products_collection.find()
    for product in products:
        print(f"Scraping price for {product['name']} from {product['url']}")
        new_price = scrape_price(product['url'])
        
        if new_price:
            current_price = float(new_price)
            stored_price = float(product.get('price', '0')) if product['price'] else None
            
            if stored_price and current_price < stored_price:
                # Send email if price has dropped
                send_price_drop_email(product['email'], product['name'], new_price, product['url'])

            # Update the price in the database
            update_result = products_collection.update_one(
                {'_id': product['_id']},
                {"$set": {'price': new_price, 'last_updated': datetime.now()}}
            )
            if update_result.modified_count > 0:
                print(f"Successfully updated price for {product['name']} in the database")
            else:
                print(f"Failed to update price for {product['name']} in the database")
        else:
            print(f"Failed to scrape price for {product['name']}")

# Function to send email notification
def send_price_drop_email(to_email, product_name, new_price, product_url):
    sender_email = "aayusingh121@gmail.com"
    sender_password = "kleptomania"  # Use app password or store securely in environment variables
    subject = f"Price Drop Alert for {product_name}"
    body = f"The price for {product_name} has dropped to {new_price}. Check it out here: {product_url}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")


# Scheduler function to run daily at a specific time (e.g., midnight)
def run_scheduler():
    schedule.every(1).hour.do(update_prices)
    while True:
        schedule.run_pending()
        time.sleep(3)  # Sleep for 60 seconds between checks

if __name__ == '__main__':
    run_scheduler()

# scrape_price("https://www.amazon.in/One94Store-Fairy-300-Adjustable-Brightness/dp/B0B97N5V97/ref=sr_1_30?crid=3KEX0Z1HNSP19&dib=eyJ2IjoiMSJ9.zlU5YszL6Cx10zHqBpiYlp8v0WD3y1jj_qR43PN7xc_BXQ-bmr_yH4rxGc6WhqjsDhqWNsgmmSnz2Jy7zqj-Oaw-cTJb0BDOq4Vuwn4R7GBTqO2Lp9lU9YpAfAlzE_FEKH8mHdDr8FrPnsfxoV066GVyz63RNsut9RFEE2lSHtUpZ1RD0sr5McSDyUSyNJu2LuWDR6ggfUweEO0X6kdopZVqTMWag_oFwX-_KSdURx5Vyakvys36gZ5YdoDhzp0ZtwPNaSq3yU8uQ5aWh-BoDdolFHUAWCxlxEk7A2k2AQU.i8bKen1eAS6m5lqWyYQS2CmxKjWOViWOi_mefDl95io&dib_tag=se&keywords=lights&qid=1728906561&sprefix=ligh%2Caps%2C297&sr=8-30")