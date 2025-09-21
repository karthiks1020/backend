"""
Create listing function for ArtisansHub
"""
import json
import os
import random
from datetime import datetime
from shared import Seller, Product

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
    if event['httpMethod'] == 'POST':
        try:
            # Parse the JSON body
            data = json.loads(event['body'])
            
            required_fields = ['seller_name', 'seller_mobile', 'seller_location', 'category', 'description', 'price', 'image_filename']
            if not all(field in data for field in required_fields):
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps({'success': False, 'message': 'Missing required fields'})
                }

            # Load existing data
            db_data = load_data()
            
            # Check if seller already exists
            seller = None
            for s in db_data['sellers']:
                if s['mobile'] == data['seller_mobile']:
                    seller = Seller(
                        s['id'], s['name'], s['mobile'], s['location'], 
                        datetime.fromisoformat(s['created_at'])
                    )
                    break
            
            # Create new seller if not exists
            if not seller:
                seller_id = max([s['id'] for s in db_data['sellers']], default=0) + 1
                seller = Seller(
                    seller_id, data['seller_name'], data['seller_mobile'], data['seller_location']
                )
                db_data['sellers'].append({
                    'id': seller.id,
                    'name': seller.name,
                    'mobile': seller.mobile,
                    'location': seller.location,
                    'created_at': seller.created_at.isoformat()
                })
            
            # Create new product
            product_id = max([p['id'] for p in db_data['products']], default=0) + 1
            new_product = Product(
                product_id,
                seller.id,
                data['category'],
                data['description'],
                float(data['price']),
                data['image_filename'],
                data.get('ai_generated', True)
            )
            
            db_data['products'].append({
                'id': new_product.id,
                'seller_id': new_product.seller_id,
                'category': new_product.category,
                'description': new_product.description,
                'price': new_product.price,
                'image_filename': new_product.image_filename,
                'ai_generated': new_product.ai_generated,
                'created_at': new_product.created_at.isoformat()
            })
            
            # Save updated data
            save_data(db_data)

            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({
                    'success': True, 
                    'message': 'Listing created successfully', 
                    'product_id': new_product.id
                })
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'success': False, 'message': f'Database error: {str(e)}'})
            }
    
    elif event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        }
    
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({'error': 'Method not allowed'})
        }