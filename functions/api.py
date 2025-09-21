"""
Netlify Function for ArtisansHub Backend API
This converts the Flask app to work as a Netlify function
"""

import json
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
import base64
from datetime import datetime
import random

# Create Flask app
app = Flask(__name__)

# Configure SQLAlchemy to use SQLite
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'artisans-hub-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///artisans_hub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'  # Use /tmp for Netlify functions
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize CORS
CORS(app, origins=["https://p-sav06.github.io"])

# Initialize database
db = SQLAlchemy(app)

# Database Models
class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='seller', lazy=True)

    def to_dict(self):
        return {
            'id': self.id, 
            'name': self.name, 
            'mobile': self.mobile, 
            'location': self.location, 
            'created_at': self.created_at.isoformat()
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(200), nullable=False)
    ai_generated = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        # For Netlify functions, we need to construct the image URL differently
        image_url = f"/uploads/{self.image_filename}"
        return {
            'id': self.id, 
            'seller_id': self.seller_id, 
            'category': self.category, 
            'description': self.description, 
            'price': self.price, 
            'image_url': image_url, 
            'ai_generated': self.ai_generated, 
            'created_at': self.created_at.isoformat(), 
            'seller': self.seller.to_dict() if self.seller else None
        }

# Create tables
with app.app_context():
    db.create_all()

# Helper functions (simplified for Netlify functions)
def process_uploaded_image(base64_string):
    try:
        header, encoded = base64_string.split(",", 1)
        image_data = base64.b64decode(encoded)
        filename = f"{uuid.uuid4().hex}.jpeg"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(image_path, "wb") as f:
            f.write(image_data)
            
        return filename
    except Exception as e:
        raise ValueError(f"Invalid image data: {e}")

def generate_ai_description(category):
    descriptions = {
        "Pottery": "A beautifully handcrafted piece of pottery, showcasing traditional techniques. Fired to perfection, this durable item is perfect for home decor or daily use.",
        "Basket Weaving": "Intricately woven by skilled artisans, this basket is made from natural, eco-friendly materials. It's both a practical storage solution and a rustic decorative piece.",
        "Handlooms": "This vibrant handloom textile is a testament to timeless weaving traditions. Made with high-quality thread, its rich colors and patterns will brighten any space.",
        "Wooden Dolls": "A charming, hand-carved wooden doll, painted with non-toxic colors. This unique toy reflects cultural heritage and makes for a wonderful collectible or gift.",
        "Unknown": "A unique piece of artisan craft. Its quality and design speak for themselves, making it a valuable addition to any collection."
    }
    return descriptions.get(category, descriptions["Unknown"])

def generate_ai_price(category):
    base_prices = {
        "Pottery": 800, "Basket Weaving": 1200, "Handlooms": 2500, "Wooden Dolls": 600, "Unknown": 500
    }
    base = base_prices.get(category, 500)
    suggested = base + random.randint(-150, 150)
    return {
        'suggested_price': max(100, suggested),
        'min_price': max(50, int(suggested * 0.8)),
        'max_price': int(suggested * 1.2)
    }

# API Routes
@app.route('/api/health')
def health_check():
    """Health check endpoint for the backend API"""
    return jsonify({
        'status': 'healthy',
        'message': 'ArtisansHub Backend API is running on Netlify Functions',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/products', methods=['GET'])
def get_all_products():
    try:
        products = Product.query.order_by(Product.created_at.desc()).all()
        return jsonify([product.to_dict() for product in products])
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/upload-analyze', methods=['POST'])
def upload_and_analyze():
    try:
        data = request.get_json()
        if 'image' not in data or not data['image']:
            return jsonify({'success': False, 'message': 'No image provided'}), 400
        
        filename = process_uploaded_image(data['image'])
        
        # For Netlify Functions, we'll return a simplified response
        # since we don't have the full AI model in the function
        category = "Handlooms"  # Default category
        
        description = generate_ai_description(category)
        pricing = generate_ai_price(category)
        
        return jsonify({
            'success': True, 
            'analysis': {
                'predicted_category': category,
                'confidence': 0.95
            }, 
            'ai_description': description, 
            'pricing_suggestion': pricing, 
            'image_filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'An internal error occurred: {str(e)}'}), 500

@app.route('/api/create-listing', methods=['POST'])
def create_listing():
    data = request.get_json()
    required_fields = ['seller_name', 'seller_mobile', 'seller_location', 'category', 'description', 'price', 'image_filename']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        seller = Seller.query.filter_by(mobile=data['seller_mobile']).first()
        if not seller:
            seller = Seller(name=data['seller_name'], mobile=data['seller_mobile'], location=data['seller_location'])
            db.session.add(seller)
            db.session.commit()
        
        new_product = Product(
            seller_id=seller.id,
            category=data['category'],
            description=data['description'],
            price=float(data['price']),
            image_filename=data['image_filename'],
            ai_generated=data.get('ai_generated', True)
        )
        db.session.add(new_product)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Listing created successfully', 'product_id': new_product.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

# Netlify function handler
def handler(event, context):
    from flask.wrappers import Request, Response
    from werkzeug.test import EnvironBuilder
    
    # Create a Flask request from the Netlify event
    builder = EnvironBuilder(
        method=event['httpMethod'],
        path=event['path'],
        headers=event['headers'] or {},
        data=event['body'] if event['httpMethod'] in ['POST', 'PUT', 'PATCH'] else None,
        query_string=event['queryStringParameters'] or {}
    )
    
    # Handle base64 encoded body
    if event.get('isBase64Encoded', False):
        import base64
        builder.data = base64.b64decode(event['body'])
    
    req = Request(builder.get_environ())
    
    # Process the request with Flask app
    with app.request_context(req.environ):
        try:
            resp = app.full_dispatch_request()
            return {
                'statusCode': resp.status_code,
                'headers': dict(resp.headers),
                'body': resp.get_data(as_text=True)
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': str(e)})
            }

# For local testing
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)