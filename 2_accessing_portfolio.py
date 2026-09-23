#========================================================================================
# LIBRARIES
#========================================================================================
import json
import requests
import pandas as pd

# Importing local functions that were created for authentication ("functions." is the folder where the modules are located)
from functions.accessing_portfolio_functions import retrieving_keys
from functions.accessing_portfolio_functions import getting_open_positions

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

# Spreadsheet with ISIN information
#-------------------------------------
isin_database = pd.read_excel("./configuration/isin_database.xlsx")

# Acces token info
#--------------------------------------------------------
with open('./configuration/token_info.json', 'r') as f:
    token_info = json.load(f)

access_token = token_info["access_token"]
refresh_token = token_info["refresh_token"]


#===========================================================================
# RETRIEVING CLIENT KEY AND ACCOUNTS KEYS
#===========================================================================

retrieving_keys(access_token, app_key)

#================================================================================================================================
# PROMPTING THE USER TO SELECT THE ACCOUNT THEY WANT TO WORK WITH
#================================================================================================================================
# I hardcoded two options since my Saxo portfolio has 2 accounts

with open('./configuration/client_key.json', 'r') as f: 
    client_key = json.load(f)
client_key = client_key["client_key"]

with open('./configuration/account_key.json', 'r') as f:
    account_key = json.load(f)

option1 = list(account_key.keys())[0] # Returns the name of the fist account
option2 = list(account_key.keys())[1] # Returns the name of the second account

while True:
    account_selection = int(input(f"Enter 1 for {option1} or 2 for {option2}: "))
    
    if account_selection == 1:
        print (f"You selected {option1}")
        account_key = account_key[option1]
        break

    elif account_selection == 2:
        print(f"You selected {option2}")
        account_key = account_key[option2]
        break

    else:
        print("Invalid choice. Please enter 1 or 2.")

#=====================================================================================================
# GETTING OPEN POSITIONS IN A GIVEN ACCOUNT
#=====================================================================================================

positions_df = getting_open_positions(account_key, client_key, access_token, app_key)

#=============================================
# FINAL DATAFRAME WITH ASSOCIATED ISIN
#=============================================

positions_df["ISIN"] = positions_df["Symbol"].map(isin_database.set_index("Symbol")["ISIN"]) # Retrieving ISIN from our database
positions_df.to_excel("positions.xlsx", index=False)
print(positions_df)