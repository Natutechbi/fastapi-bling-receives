import requests
import json
import schedule
import time
import os
from dotenv import load_dotenv, set_key

# Path to the .env file
ENV_PATH = '.env'

def get_access_token():
    """
    Fetch access token from the specified URL and save to .env file.
    """
    url = "http://85.209.93.197:8080/code_bling/lojaodositio"
    
    payload = {}
    headers = {
        'Authorization': 'Bearer 0123456789',
        'Content-Type': 'application/json'
    }
    
    try:
        # Send GET request
        response = requests.request("GET", url, headers=headers, data=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            # Parse the response
            response_data = response.json()
            
            # Ensure the .env file exists
            if not os.path.exists(ENV_PATH):
                open(ENV_PATH, 'a').close()
            
            # Save the access token to .env file
            set_key(ENV_PATH, 'ACCESS_TOKEN', json.dumps(response_data))
            
            print(f"Access token updated successfully at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Response:", json.dumps(response_data, indent=2))
        else:
            print(f"Failed to fetch access token. Status code: {response.status_code}")
            print("Response:", response.text)
    
    except requests.RequestException as e:
        print(f"Error occurred while fetching access token: {e}")
    except json.JSONDecodeError:
        print("Error parsing JSON response")

def main():
    # Load existing .env variables
    load_dotenv(ENV_PATH)
    
    # Schedule the job to run every 240 minutes
    schedule.every(240).minutes.do(get_access_token)
    
    # Initial token fetch
    get_access_token()
    
    # Keep the script running and execute scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
