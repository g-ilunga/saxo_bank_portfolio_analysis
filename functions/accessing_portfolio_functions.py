#========================================================================================
# LIBRARIES
#========================================================================================
import json
import requests
import pandas as pd

configuration_folder = "./configuration" # This is where configuration files are saved

#=================================================================================================
# LOADING NECESSARY INPUT FILES
#=================================================================================================

# Info related to the liveApp created on the Saxo Developer Portal
#------------------------------------------------------------------

with open('./configuration/app_details.json', 'r') as f: # This is the json file where the liveApp info were stored
    configuration = json.load(f)

app_key = configuration["app_key"] 
authorization_endpoint = configuration["authorization_endpoint"]
token_endpoint = configuration["token_endpoint"]
app_secret = configuration["app_secrets1"] # Saxo provides 2 App Secrets. You can use either one.
redirect_url = configuration["redirect_url"]
scopes = configuration["scopes"]

"""
Notes:
===========================
The "scopes" parameter is not part of the liveapp info on Saxo Developer Portal. 
I included it in my configuration file to specify that I want my app to have the permission "read" and "offline_access"
"""


# Acces token info
#--------------------------------------------------------
with open('./configuration/token_info.json', 'r') as f:
    token_info = json.load(f)

access_token = token_info["access_token"]
refresh_token = token_info["refresh_token"]


#===========================================================================
# RETRIEVING CLIENT KEY AND ACCOUNTS KEYS
#===========================================================================

def retrieving_keys(access_token, app_key):
    
    # API calls
    #--------------------------------------------------------------------------------
    accounts_endpoint = "https://gateway.saxobank.com/openapi/port/v1/accounts/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-OpenAPI-AppKey": app_key
    }
    response = requests.get(accounts_endpoint, headers=headers)

    # Retrieving client key
    #--------------------------------------------------
    client_key = response.json()["Data"][0]["ClientKey"] # no matter the number of accounts you have, client key is the same. No need to put it in a loop
    client_key_dict = {"client_key": client_key} 
    with open(f"{configuration_folder}/client_key.json", "w") as f: # Saving the account keys and client key into a .json file.
        json.dump(client_key_dict, f)

    # Retrieving account display name and keys
    #-----------------------------------------------------
    account_display_name_list = [] # Names of accounts as they appear on the saxoinvestor or trader platform
    account_key_list = []
    number_of_accounts = len(response.json()["Data"])

    for x in list(range(number_of_accounts)):
        account_display_name = response.json()["Data"][x]["DisplayName"]
        account_key = response.json()["Data"][x]["AccountKey"]

        account_display_name_list.append(account_display_name)
        account_key_list.append(account_key)

    accounts_details = dict(zip(account_display_name_list, account_key_list))
    with open(f"{configuration_folder}/account_key.json", "w") as f: # Saving the account keys and client key into a .json file.
        json.dump(accounts_details, f)
    
    print("Client keys and account key successfully retrieved.")


#====================================================
# GETTING OPEN POSITIONS IN A GIVEN ACCOUNT
#====================================================

def getting_open_positions(account_key, client_key, access_token, app_key):

    # Retrieving positions UIC, invested amount and asset type
    #-----------------------------------------------------------
    position_endpoint = f"https://gateway.saxobank.com/openapi/port/v1/netpositions?AccountKey={account_key}&ClientKey={client_key}" # position in a given account. But it doesn't give names of products
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-OpenAPI-AppKey": app_key
    }
    response = requests.get(position_endpoint, headers=headers)

    number_of_positions = response.json()['__count']
    uic_list = [] # UIC are unique identifiers that Saxo assigns to each instruments available
    asset_type_list = []
    invested_amount_list = []

    for x in list(range(number_of_positions)):
        uic = response.json()["Data"][x]["NetPositionBase"]["Uic"]
        asset_type = response.json()["Data"][x]["NetPositionBase"]["AssetType"]
        market_value = response.json()["Data"][x]["NetPositionView"]["MarketValueOpenInBaseCurrency"]
        profit_loss = response.json()["Data"][x]["NetPositionView"]["ProfitLossOnTradeInBaseCurrency"]
        invested_amount = (market_value - profit_loss) * (-1)

        uic_list.append(uic)
        asset_type_list.append(asset_type)
        invested_amount_list.append(invested_amount)

    # Retrieving symbols of open positions to match with our ISIN database
    #-----------------------------------------------------------------------
    symbol_list = []
    asset_name_list = []

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-OpenAPI-AppKey": app_key
    }

    for uic,  asset_type in zip(uic_list, asset_type_list):
        instruments_endpoint = f"https://gateway.saxobank.com/openapi/ref/v1/instruments?AccountKey={account_key}&ClientKey={client_key}&Uics={uic}&AssetType={asset_type}" # to retrieve names of products from UIC (universal instruments code)

        response = requests.get(instruments_endpoint, headers=headers)
        symbol = response.json()["Data"][0]["Symbol"]
        symbol_list.append(symbol)

        asset_name = response.json()["Data"][0]["Description"]
        asset_name_list.append(asset_name)

    # Creating a dataframe of our open positions
    df_positions = pd.DataFrame({
        "Name": asset_name_list,
        "UIC": uic_list,
        "Type": asset_type_list,
        "Symbol": symbol_list,
        "Invested_amount": invested_amount_list
    })

    return df_positions