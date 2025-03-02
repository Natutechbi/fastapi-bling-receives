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
        
        # Calculate the date 4 days ago
        four_days_ago = datetime.now() - timedelta(days=4)
        
        # Query for documents where dataEmissao_x is within the last 5 days
        query = {
            "dataEmissao_x": {
                "$gte": four_days_ago.strftime("%Y-%m-%d")
            }
        }
        
        # Execute the query
        results = list(collection.find(query))
        
        # Process the numeroDocumento field for each document
        split_numeroDocumento(results, collection)
        
        return results
        
    except Exception as e:
        logging.error(f"Error retrieving recent receivables: {str(e)}")
        return []
    finally:
        if 'client' in locals():
            client.close()

def split_numeroDocumento(documents, collection):
    """
    Splits the numeroDocumento field into CRPedidoNº field
    and updates the documents in MongoDB if they haven't been processed already.
    
    Args:
        documents (list): List of documents to process
        collection: MongoDB collection to update
    """
    total_docs = len(documents)
    split_success = 0
    already_processed = 0
    split_failed = 0
    
    for doc in documents:
        # Check if fields already exist and have values
        if ('CRPedidoNº' in doc and doc['CRPedidoNº']):
            already_processed += 1
            continue
            
        if 'numeroDocumento' in doc and doc['numeroDocumento']:
            try:
                parts = doc['numeroDocumento'].split('/')
                doc['CRPedidoNº'] = parts[0] if len(parts) > 0 else ''
                
                # Update only if the document hasn't been processed
                collection.update_one(
                    {
                        '_id': doc['_id'],
                        '$or': [
                            {'CRPedidoNº': {'$exists': False}},
                            {'CRPedidoNº': ''}
                        ]
                    },
                    {'$set': {
                        'CRPedidoNº': doc['CRPedidoNº']
                    }}
                )
                split_success += 1
            except Exception as e:
                logging.error(f"Error splitting numeroDocumento for document {doc.get('_id')}: {str(e)}")
                split_failed += 1
        else:
            split_failed += 1
    
    logging.info(
        f"Processed {total_docs} receivables: "
        f"{split_success} numeroDocumento successfully split, "
        f"{already_processed} already processed, "
        f"{split_failed} failed or missing numeroDocumento"
    )

def get_CRDataControle_(CREmissao, CRValorParcela, CRPedidoNº):
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("MONGO_DATABASE")]
        collection = db[os.getenv("MONGO_COLLECTION_RECEIVABLE")]
        
        # Query for documents where CREmissao matches and check if already processed
        query = {
            "CREmissao": CREmissao,
            "$or": [
                {"DataControle": {"$exists": False}},
                {"DataControle": None}
            ]
        }
        
        # Execute the query
        result = collection.find_one(query)
        
        if result:
            # Document exists but hasn't been processed yet
            try:
                # Copy the CREmissao value and convert to Int64
                emissao_value = result["CREmissao"]
                # Convert to Int64 using pandas
                data_controle_int = pd.to_numeric(emissao_value, downcast='integer')
                result["DataControle"] = int(data_controle_int)
                
                # Update the document in the database
                collection.update_one(
                    {"_id": result["_id"]},
                    {"$set": {
                        "DataControle": result["DataControle"]
                    }}
                )
                
                logging.info(f"Successfully converted DataControle to Int64 for document {result['_id']}")
                return result
            except ValueError as ve:
                logging.error(f"Error converting DataControle to Int64: {str(ve)}")
                return None
        else:
            # Check if document was already processed
            already_processed = collection.find_one({
                "CREmissao": CREmissao,
                "DataControle": {"$exists": True, "$ne": None}
            })
            
            if already_processed:
                logging.info(f"Document with CREmissao {CREmissao} was already processed")
                return already_processed
            else:
                logging.info(f"No document found with CREmissao: {CREmissao}")
                return None
                
    except Exception as e:
        logging.error(f"Error retrieving CRDataControle: {str(e)}")
        return None
    finally:
        if 'client' in locals():
            client.close()
            logging.info("MongoDB connection closed successfully")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Test the get_recent_receivables function
    try:
        recent_receivables = get_recent_receivables()
        print(f"Found {len(recent_receivables)} recent receivables")
    except Exception as e:
        print(f"Error testing get_recent_receivables: {e}")

