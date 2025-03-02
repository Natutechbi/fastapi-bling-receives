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

from access_api import *

# Configure logging to output to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Load environment variables
if load_dotenv():
    logging.info("Environment variables loaded successfully from .env file")
else:
    logging.error("Warning: Could not load environment variables from .env file")

# MongoDB connection settings
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_COLLECTION_SELLERS = os.getenv("MONGO_COLLECTION_SELLERS")
MONGO_COLLECTION_PAYMENT_METHODS = os.getenv("MONGO_COLLECTION_PAYMENT_METHODS")
MONGO_COLLECTION_MODULOS = os.getenv("MONGO_COLLECTION_MODULOS")
MONGO_COLLECTION_RECEIVABLE = os.getenv("MONGO_COLLECTION_RECEIVABLE")

# Test MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    client.server_info()  # Will raise an exception if connection fails
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {str(e)}")

# some old code

url = os.getenv("URL_PAGAMENTOS")

payload = {}
headers = {
  'Accept': 'application/json',
  'Authorization': f"Bearer {os.getenv('ACCESS_TOKEN')}"
}

def get_bling_modules():
    """
    Retrieves a list of modules from the Bling API.

    Returns:
        dict: The response from the Bling API containing the list of modules.
    """
    response = requests.request("GET", url, headers=get_headers(), data=payload)
    try:
        data = response.json()
        logging.info("Successfully retrieved modules data from Bling API")
        return data
    except:
        logging.error("Failed to retrieve modules data from Bling API")
        logging.error(response.text)
        return None

def get_bling_vendors():
    """
    Retrieves a list of active vendors from the Bling API.

    Returns:
        dict: The response from the Bling API containing the list of vendors.
    """
    url = os.getenv("URL_VENDEDORES")
    payload = {}
    headers = {
        'Accept': 'application/json',
        'Authorization': f"Bearer {os.getenv('ACCESS_TOKEN')}",
        'Cookie': os.getenv('COOKIE')
    }

    response = requests.request("GET", url, headers=get_headers(), data=payload)
    try:
        data = response.json()
        logging.info("Successfully retrieved vendedores from Bling API")
        return data
    except:
        logging.error("Failed to retrieve vendedores from Bling API")
        logging.error(response.text)
        return None

def save_to_mongodb(data):
    """
    Saves the provided data to a MongoDB database.

    Args:
        data (dict): The data to be saved to the database.
    """
    mongo_uri = os.getenv("MONGO_URI")
    mongo_database = os.getenv("MONGO_DATABASE")
    mongo_collection = os.getenv("MONGO_COLLECTION_PAYMENTS")

    client = MongoClient(mongo_uri)
    db = client[mongo_database]
    collection = db[mongo_collection]

    # Remove existing data before saving the new data
    try:
        delete_result = collection.delete_many({})
        logging.info(f"Successfully removed {delete_result.deleted_count} documents from {mongo_collection}")
    except Exception as e:
        logging.error(f"Failed to remove existing data from {mongo_collection}: {str(e)}")
        return

    # Insert new data
    try:
        insert_result = collection.insert_one(data)
        logging.info(f"Successfully inserted new document with ID: {insert_result.inserted_id}")
    except Exception as e:
        logging.error(f"Failed to insert new data into {mongo_collection}: {str(e)}")

def save_vendors_to_mongodb(data):
    """
    Saves the provided data to a MongoDB database.

    Args:
        data (dict): The data to be saved to the database.
    """
    mongo_uri = os.getenv("MONGO_URI")
    mongo_database = os.getenv("MONGO_DATABASE")
    mongo_collection = os.getenv("MONGO_COLLECTION_SELLERS")

    client = MongoClient(mongo_uri)
    db = client[mongo_database]
    collection = db[mongo_collection]

    # Remove existing data before saving the new data
    try:
        delete_result = collection.delete_many({})
        logging.info(f"Successfully removed {delete_result.deleted_count} documents from {mongo_collection}")
    except Exception as e:
        logging.error(f"Failed to remove existing data from {mongo_collection}: {str(e)}")
        return

    # Insert new data
    try:
        insert_result = collection.insert_one(data)
        logging.info(f"Successfully inserted new document with ID: {insert_result.inserted_id}")
    except Exception as e:
        logging.error(f"Failed to insert new data into {mongo_collection}: {str(e)}")

# New data getters, as Power Bi

# Vendedor / sellers data
def get_bling_sellers_data():
    response = get(f"{API_BASE_URL}/vendedores?situacaoContato=A", headers=get_headers())

    if response.status_code == 200:
        logging.info(f"Successfully fetched sellers data from API")
        data = response.json()
        vendedores = data.get("data", [])

        df = pd.DataFrame(vendedores)

        if 'loja' in df.columns:
            loja_df = pd.json_normalize(df['loja'])
            df = pd.concat([df, loja_df.add_prefix('loja.')], axis=1).drop(columns=['loja'])

        if 'contato' in df.columns:
            contato_df = pd.json_normalize(df['contato'])
            df = pd.concat([df, contato_df.add_prefix('contato.')], axis=1).drop(columns=['contato'])

        df.rename(columns={'contato.nome': 'CRVendedor'}, inplace=True)

        df = df.astype({
            'id': str,
            'descontoLimite': float,
            'lojaid': str,
            'contatoid': str,
            'CRVendedor': str
        })

        return df.to_dict("records")
    else:
        logging.error(f"Failed to fetch data: {response.status_code}")


# Modulos and Situacoes data
def get_bling_modulos_data():
    response = get(f"{API_BASE_URL}/situacoes/modulos", headers=get_headers())
    bling_endpoint = os.getenv("LOJA")  # will be passed as function argument in future

    if response.status_code == 200:
        logging.info("Successfully fetched modulos data from API")
        data = response.json()
        modulos = data.get("data", [])
        df = pd.DataFrame(modulos)
        if not df.empty:
            df = df.astype({
                "id": str,
                "nome": str,
                "descricao": str
            })

            situacoes_list = []
            for _, row in df.iterrows():
                module_id = row["id"]
                situacoes_response = get(f"{API_BASE_URL}/situacoes/modulos/{module_id}", headers=get_headers())

                if situacoes_response.status_code == 200:
                    logging.info(f"Successfully fetched situacoes for module {module_id}")
                    situacoes_data = situacoes_response.json().get("data", [])
                    for situacao in situacoes_data:
                        situacao["module_id"] = module_id
                        situacao["bling_endpoint"] = bling_endpoint
                    situacoes_list.extend(situacoes_data)
                else:
                    logging.error(f"Failed to fetch situacoes for module {module_id}: {situacoes_response.status_code}")

            situacoes_df = pd.DataFrame(situacoes_list)

            # Merging 
            if not situacoes_df.empty:
                situacoes_df = situacoes_df.astype({
                    "id": str,
                    "nome": str,
                    "idHerdado": str,
                    "cor": str
                })
                merged_df = df.merge(situacoes_df, left_on="id", right_on="module_id", suffixes=("", ".Situacoes"))
                return merged_df.to_dict("records")
            else:
                logging.info("No situacoes data found")
        else:
            logging.info("No modulos data found")
    else:
        logging.error(f"Failed to fetch modulos data: {response.status_code}, {response.text}")


# Payment method data
def get_bling_payment_methods_data() -> list[dict]:
    """Return payment method data"""
    response = get(f"{API_BASE_URL}/formas-pagamentos", headers=get_headers())

    if response.status_code == 200:
        logging.info("Successfully fetched payment methods data from API")
        data = response.json()
        forma_pagamentos = data.get("data", [])
        df = pd.DataFrame(forma_pagamentos)

        if not df.empty:
            df = df.astype({
                "id": str,
                "descricao": str,
                "tipoPagamento": str,
                "situacao": str,
                "padrao": str,
                "finalidade": str
            })

            return df.to_dict("records")
        else:
            logging.info("No forma_pagamentos data found.")
    else:
        logging.error(f"Failed to fetch forma_pagamentos data: {response.status_code}, {response.text}")


# Receivable data
def get_bling_receivable_data() -> list[dict]:
    """Return last 30 days receivable data, only if not already retrieved"""

    today = datetime.now()
    _30_day_ago = datetime.now() - timedelta(days=30)

    # Check if data already exists in MongoDB for today
    try:
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        collection = db[MONGO_COLLECTION_RECEIVABLE]

        # Check for documents from today
        today_start = datetime.combine(today.date(), datetime.min.time())
        existing_data = collection.find_one({
            "CREmissao": {"$gte": today_start.isoformat()}
        })

        if existing_data:
            logging.info("Receivable data already retrieved today, skipping fetch")
            return list(collection.find())

    except Exception as e:
        logging.error(f"Error checking MongoDB for existing data: {str(e)}")
        return []

    def fetch_receivable_data():
        params = {
            "situacoes[]": "1", 
            "tipoFiltroData": "E",
            "dataInicial": _30_day_ago.strftime("%Y-%m-%d"),
            "dataFinal": today.strftime("%Y-%m-%d"),
            "idFormaPagamento": "4951136"
        }
        # Add delay between API calls
        sleep(4)
        response = get(f"{API_BASE_URL}/contas/receber", headers=get_headers(), params=params)
        if response.status_code == 200:
            logging.info("Successfully fetched receivable data from API")
            data = response.json()
            return data.get("data", [])
        else:
            logging.error(f"Failed to fetch contas/receber: {response.status_code}, {response.text}")
            return []

    def fetch_receivable_detail(receivable_id):
        # Add delay between API calls
        sleep(4)
        response = get(f"{API_BASE_URL}/contas/receber/{receivable_id}", headers=get_headers())
        if response.status_code == 200:
            logging.info(f"Successfully fetched receivable details for ID {receivable_id} from API")
            return response.json().get("data", {})
        else:
            logging.error(f"Failed to fetch details for ID {receivable_id}: {response.status_code}, {response.text}")
            return {}

    receivable_data = fetch_receivable_data()
    if not receivable_data:
        logging.info("No receivable data found.")
        return []

    df = pd.DataFrame(receivable_data)
    df = df.rename(columns={"id": "CRParcelaID"}) # ok

    detailed_data = []
    for _, row in df.iterrows():
        receivable_id = row["CRParcelaID"]
        detail = fetch_receivable_detail(receivable_id)
        if detail:
            detail.update({"CRParcelaID": receivable_id})  # Retain ID for joining
            detailed_data.append(detail)

    detail_df = pd.DataFrame(detailed_data)

    # Merging
    merged_df = pd.merge(df, detail_df, on="CRParcelaID", how="left")

    # Renaming
    rename_map = {
        "situacao": "CRSituacao", #ok
        "vencimento": "CRVenc",# ok
        "valor": "CRValorParcela", #ok
        "dataEmissao": "CREmissao", #ok
        "saldo": "CRSaldoVenda", #ok
        "vendedorid": "CRVendedorID", #ok
        "formaPagamentoid": "CRFormaPagamento", #ok
        "contatoid": "CRContatoID" #ok
    }

    # Rename columns if they exist
    merged_df = merged_df.rename(columns={k: v for k, v in rename_map.items() if k in merged_df.columns})

    # Format columns if they exist
    if "CRVenc" in merged_df.columns:
        merged_df["CRVenc"] = pd.to_datetime(merged_df["CRVenc"], errors="coerce")
    if "CREmissao" in merged_df.columns:
        merged_df["CREmissao"] = pd.to_datetime(merged_df["CREmissao"], errors="coerce")
    if "CRValorParcela" in merged_df.columns:
        merged_df["CRValorParcela"] = pd.to_numeric(merged_df["CRValorParcela"], errors="coerce")
    if "CRSaldoVenda" in merged_df.columns:
        merged_df["CRSaldoVenda"] = pd.to_numeric(merged_df["CRSaldoVenda"], errors="coerce")

    # Save new data to MongoDB
    try:
        collection.delete_many({})  # Clear old data
        records = merged_df.to_dict("records")
        collection.insert_many(records)
        logging.info(f"Successfully saved {len(records)} new receivable records to MongoDB")
        return records
    except Exception as e:
        logging.error(f"Error saving receivable data to MongoDB: {str(e)}")
        return merged_df.to_dict("records")

def run_schedule():
    """
    Runs the data retrieval and saving to MongoDB on a 24-hours schedule.
    """      
    logging.info("Starting data collection process...")
    
    while True:
        logging.info(f"Running data collection at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        sellers_collection = db[MONGO_COLLECTION_SELLERS]
        modulos_collection = db[MONGO_COLLECTION_MODULOS]
        payment_methods_collection = db[MONGO_COLLECTION_PAYMENT_METHODS]
        receivable_collection = db[MONGO_COLLECTION_RECEIVABLE]

        # sellers data
        try:
            logging.info("Fetching sellers data...")
            sellers_data = get_bling_sellers_data()
            sellers_collection.delete_many({})
            sellers_collection.insert_many(sellers_data)
            logging.info(f"Successfully saved {len(sellers_data)} seller records")
        except Exception as e:
            logging.error(f"ERROR fetching sellers data: {e}")

        # modulos data
        try:
            logging.info("Fetching modules data...")
            modulos_data = get_bling_modulos_data()
            modulos_collection.delete_many({})
            modulos_collection.insert_many(modulos_data)
            logging.info(f"Successfully saved {len(modulos_data)} module records")
        except Exception as e:
            logging.error(f"ERROR fetching modules data: {e}")

        # payment methods data
        try:
            logging.info("Fetching payment methods data...")
            payment_methods_data = get_bling_payment_methods_data()
            payment_methods_collection.delete_many({})
            payment_methods_collection.insert_many(payment_methods_data)
            logging.info(f"Successfully saved {len(payment_methods_data)} payment method records")
        except Exception as e:
            logging.error(f"ERROR fetching payment methods data: {e}")

        # CT receivables data
        try:
            logging.info("Fetching receivable data...")
            receivable_data = get_bling_receivable_data()
            receivable_collection.delete_many({})
            receivable_collection.insert_many(receivable_data)
            logging.info(f"Successfully saved {len(receivable_data)} receivable records")
        except Exception as e:
            logging.error(f"ERROR fetching receivable data: {e}")

        next_run = datetime.now() + timedelta(hours=24)
        logging.info(f"Data collection completed. Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        sleep(86400)  # 24 hours in seconds (fixed from 86000)

if __name__ == "__main__":
    try:
        logging.info("About to start run_schedule...")
        run_schedule()
    except Exception as e:
        logging.error(f"Fatal error in main execution: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
