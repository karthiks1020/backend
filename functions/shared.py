"""
Shared utilities for ArtisansHub Netlify functions
"""
import os
import uuid
import base64
import random
from datetime import datetime

# Create uploads directory
UPLOAD_FOLDER = '/tmp/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database models (simplified for serverless)
class Seller:
    def __init__(self, id, name, mobile, location, created_at=None):
        self.id = id
        self.name = name
        self.mobile = mobile
        self.location = location
        self.created_at = created_at or datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile': self.mobile,
            'location': self.location,
            'created_at': self.created_at.isoformat()
        }

class Product:
    def __init__(self, id, seller_id, category, description, price, image_filename, ai_generated=True, created_at=None):
        self.id = id
        self.seller_id = seller_id
        self.category = category
        self.description = description
        self.price = price
        self.image_filename = image_filename
        self.ai_generated = ai_generated
        self.created_at = created_at or datetime.now()
    
    def to_dict(self, seller=None):
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
            'seller': seller.to_dict() if seller else None
        }

# Helper functions
def process_uploaded_image(base64_string):
    try:
        header, encoded = base64_string.split(",", 1)
        image_data = base64.b64decode(encoded)
        filename = f"{uuid.uuid4().hex}.jpeg"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        
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