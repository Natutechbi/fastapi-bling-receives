import os
import requests
from requests import get
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv

import pandas as pd

from access_api import *

load_dotenv()


# Mongo DB

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DATABASE = os.getenv("MONGO_DATABASE")
MONGO_COLLECTION_SELLERS = os.getenv("MONGO_COLLECTION_SELLERS")
MONGO_COLLECTION_PAYMENT_METHODS = os.getenv("MONGO_COLLECTION_PAYMENT_METHODS")
MONGO_COLLECTION_MODULOS = os.getenv("MONGO_COLLECTION_MODULOS")
MONGO_COLLECTION_RECEIVABLE = os.getenv("MONGO_COLLECTION_RECEIVABLE")

# some old code

url = "https://bling.com.br/Api/v3/formas-pagamentos"

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
        return response.json()
    except:
        print(response.text)

def get_bling_vendors():
    """
    Retrieves a list of active vendors from the Bling API.

    Returns:
        dict: The response from the Bling API containing the list of vendors.
    """
    url = "https://bling.com.br/Api/v3/vendedores?situacaoContato=A"
    payload = {}
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer 2a60ec481fd639ac52933c11812bfdf080bf4c92',
        'Cookie': 'PHPSESSID=v7f9qq0ee44iqviq7e95fm6r7e'
    }

    response = requests.request("GET", url, headers=get_headers(), data=payload)
    return response.json()

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
    collection.delete_many({})
    collection.insert_one(data)
    print(f"Data saved to MongoDB collection: {mongo_collection}")

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
    collection.delete_many({})
    collection.insert_one(data)
    print(f"Data saved to MongoDB collection: {mongo_collection}")

# New data getters, as Power Bi

# Vendedor / sellers data
def get_bling_sellers_data():
    response = get(f"{API_BASE_URL}/vendedores?situacaoContato=A", headers=get_headers())

    if response.status_code == 200:
        data = response.json()
        vendedores = data.get("data", [])

        df = pd.DataFrame(vendedores)

        if 'loja' in df.columns:
            loja_df = pd.json_normalize(df['loja'])
            df = pd.concat([df, loja_df.add_prefix('loja.')], axis=1).drop(columns=['loja'])

        if 'contato' in df.columns:
            contato_df = pd.json_normalize(df['contato'])
            df = pd.concat([df, contato_df.add_prefix('contato.')], axis=1).drop(columns=['contato'])

        df.rename(columns={'contato.nome': 'CR.Vendedor'}, inplace=True)

        df = df.astype({
            'id': str,
            'descontoLimite': float,
            'loja.id': str,
            'contato.id': str,
            'CR.Vendedor': str
        })

        return df.to_dict("records")
    else:
        print(f"Failed to fetch data: {response.status_code}")


# Modlos and Sitacoes data
def get_bling_modulos_data():
    response = get(f"{API_BASE_URL}/situacoes/modulos", headers=get_headers())
    bling_endpoint = "lojaodositio" # will be passed as function argument in future

    if response.status_code == 200:
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
                    situacoes_data = situacoes_response.json().get("data", [])
                    for situacao in situacoes_data:
                        situacao["module_id"] = module_id
                        situacao["bling_endpoint"] = bling_endpoint
                    situacoes_list.extend(situacoes_data)

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
                print("No situacoes data found")
        else:
            print("No modulos data found")
    else:
        print(f"Failed to fetch modulos data: {response.status_code}, {response.text}")


# Payment method data
def get_bling_payment_methods_data() -> list[dict]:
    """Return payment method data"""
    response = get(f"{API_BASE_URL}/formas-pagamentos", headers=get_headers())

    if response.status_code == 200:
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
            print("No forma_pagamentos data found.")
    else:
        print(f"Failed to fetch forma_pagamentos data: {response.status_code}, {response.text}")


# Receivable data
def get_bling_receivable_data() -> list[dict]:
    """Return last 30 days reveivable data"""

    today = datetime.now()
    _30_day_ago = datetime.now() - timedelta(days=30)

    def fetch_receivable_data():
        params = {
            "situacoes[]": "1",
            "tipoFiltroData": "E",
            "dataInicial": _30_day_ago.strftime("%Y-%m-%d"),
            "dataFinal": today.strftime("%Y-%m-%d"),
            "idFormaPagamento": "4951136"
        }
        response = get(f"{API_BASE_URL}/contas/receber", headers=get_headers(), params=params)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", [])
        else:
            print(f"Failed to fetch contas/receber: {response.status_code}, {response.text}")
            return []

    def fetch_receivable_detail(receivable_id):
        response = get(f"{API_BASE_URL}/contas/receber/{receivable_id}", headers=get_headers())
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            print(f"Failed to fetch details for ID {receivable_id}: {response.status_code}, {response.text}")
            return {}

    receivable_data = fetch_receivable_data()
    if not receivable_data:
        print("No receivable data found.")
        return []

    df = pd.DataFrame(receivable_data)
    df = df.rename(columns={"id": "CR.Parcela.ID"})

    detailed_data = []
    for _, row in df.iterrows():
        receivable_id = row["CR.Parcela.ID"]
        detail = fetch_receivable_detail(receivable_id)
        if detail:
            detail.update({"CR.Parcela.ID": receivable_id})  # Retain ID for joining
            detailed_data.append(detail)

    detail_df = pd.DataFrame(detailed_data)

    # Mergnig
    merged_df = pd.merge(df, detail_df, on="CR.Parcela.ID", how="left")

    # Renaming
    rename_map = {
        "situacao": "CR.Situacao",
        "vencimento": "CR.Venc",
        "valor": "CR.ValorParcela",
        "dataEmissao": "CR.Emissao",
        "saldo": "CR.SaldoVenda",
        "vendedor.id": "Vendedor.ID",
        "formaPagamento.id": "CR.FormaPagamento",
        "contato.id": "CR.Contato.ID"
    }

    # Rename columns if they exist
    merged_df = merged_df.rename(columns={k: v for k, v in rename_map.items() if k in merged_df.columns})

    # Format columns if they exist
    if "CR.Venc" in merged_df.columns:
        merged_df["CR.Venc"] = pd.to_datetime(merged_df["CR.Venc"], errors="coerce")
    if "CR.Emissao" in merged_df.columns:
        merged_df["CR.Emissao"] = pd.to_datetime(merged_df["CR.Emissao"], errors="coerce")
    if "CR.ValorParcela" in merged_df.columns:
        merged_df["CR.ValorParcela"] = pd.to_numeric(merged_df["CR.ValorParcela"], errors="coerce")
    if "CR.SaldoVenda" in merged_df.columns:
        merged_df["CR.SaldoVenda"] = pd.to_numeric(merged_df["CR.SaldoVenda"], errors="coerce")

    return merged_df.to_dict("records")

def run_schedule():
    """
    Runs the data retrieval and saving to MongoDB on a 24-hours schedule.
    """
    while True:

        client = MongoClient(MONGO_URI)
        db = client[MONGO_DATABASE]
        sellers_collection = db[MONGO_COLLECTION_SELLERS]
        modulos_collection = db[MONGO_COLLECTION_MODULOS]
        payment_methods_collection = db[MONGO_COLLECTION_PAYMENT_METHODS]
        receivable_collection = db[MONGO_COLLECTION_RECEIVABLE]

        # sellers data
        try:
            sellers_data = get_bling_sellers_data()
            sellers_collection.delete_many({})
            sellers_collection.insert_many(sellers_data)
        except Exception as e:
            print("ERROR: ", e)

        # modulos data
        try:
            modulos_data = get_bling_modulos_data()
            modulos_collection.delete_many({})
            modulos_collection.insert_many(modulos_data)
        except Exception as e:
            print("ERROR: ", e)

        # payment methods data
        try:
            payment_methods_data = get_bling_payment_methods_data()
            payment_methods_collection.delete_many({})
            payment_methods_collection.insert_many(payment_methods_data)
        except Exception as e:
            print("ERROR: ", e)

        # CT receivables data
        try:
            receivable_data = get_bling_receivable_data()
            receivable_collection.delete_many({})
            receivable_collection.insert_many(receivable_data)
        except Exception as e:
            print("ERROR: ", e)

        next_run = datetime.now() + timedelta(hours=24)
        print(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        sleep(86000)

if __name__ == "__main__":
    run_schedule()
