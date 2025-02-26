import os
import requests
from requests import get
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys
import logging
from time import sleep
import pandas as pd

from bling_sources import *

def get_recent_receivables():
    """
    Retrieves receivables from MongoDB where dataEmissao_x is within the last 5 days.
    
    Returns:
        list: List of receivable documents that match the criteria
    """
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DATABASE")]
        collection = db[os.getenv("MONGO_COLLECTION_RECEIVABLE")]
        
        # Calculate the date 5 days ago
        five_days_ago = datetime.now() - timedelta(days=5)
        
        # Query for documents where dataEmissao_x is within the last 5 days
        query = {
            "dataEmissao_x": {
                "$gte": five_days_ago.strftime("%Y-%m-%d")
            }
        }
        
        # Execute the query
        results = list(collection.find(query))
        
        logging.info(f"Successfully retrieved {len(results)} receivables from the last 5 days")
        return results
        
    except Exception as e:
        logging.error(f"Error retrieving recent receivables: {str(e)}")
        return []
    finally:
        if 'client' in locals():
            client.close()

