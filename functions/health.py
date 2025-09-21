"""
Health check function for ArtisansHub
"""
import json
from datetime import datetime

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'https://p-sav06.github.io',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps({
            'status': 'healthy',
            'message': 'ArtisansHub Backend API is running on Netlify Functions',
            'timestamp': datetime.now().isoformat()
        })
    }