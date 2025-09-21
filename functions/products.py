"""
Products function for ArtisansHub
"""
import json
import os
from datetime import datetime
from shared import Product, Seller

# Simple in-memory storage (in a real app, you'd use a database)
# For demo purposes, we'll use a file-based storage
DATA_FILE = '/tmp/artisanshub_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'sellers': [], 'products': []}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def handler(event, context):
    if event['httpMethod'] == 'GET':
        # Return all products
        data = load_data()
        products = data.get('products', [])
        
        # Convert to proper format
        formatted_products = []
        for product_data in products:
            seller = None
            for s in data.get('sellers', []):
                if s['id'] == product_data['seller_id']:
                    seller = Seller(
                        s['id'], s['name'], s['mobile'], s['location'], 
                        datetime.fromisoformat(s['created_at'])
                    )
                    break
            
            product = Product(
                product_data['id'], product_data['seller_id'], product_data['category'],
                product_data['description'], product_data['price'], product_data['image_filename'],
                product_data['ai_generated'], datetime.fromisoformat(product_data['created_at'])
            )
            formatted_products.append(product.to_dict(seller))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(formatted_products)
        }
    
    elif event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }