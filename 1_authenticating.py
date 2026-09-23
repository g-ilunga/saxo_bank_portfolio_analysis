#========================================================================================
# LIBRARIES
#========================================================================================
import json
import urllib.parse
import webbrowser

# Importing local functions that were created for authentication ("functions." is the folder where the modules are located)
from functions.authentication_functions import build_saxo_login_url
from functions.authentication_functions import exchange_code_for_tokens

#========================================================================================
# LOADING THE INFO RELATED TO THE LIVEAPP CREATED ON SAXO DEVELOPER PORTAL
#========================================================================================

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


#==========================================================================================
# STEP 1: RETRIEVING THE AUTHORISATION CODE
#==========================================================================================

# Constructing the url that will be used to log in to your Saxo account
#-----------------------------------------------------------------------
login_url = build_saxo_login_url(app_key, authorization_endpoint, redirect_url, scopes) 

# Opening the url to enter the Saxo account credential
#-----------------------------------------------------
webbrowser.open(login_url)

# Extracting the authorisation code from  the redirect url
#---------------------------------------------------------
auth_url = str(input("Paste the redirect url here: ")) # Prompting the user to paste the redirect url
parsed = urllib.parse.urlparse(auth_url)
params = urllib.parse.parse_qs(parsed.query)
auth_code = params.get("code", [None])[0]

#============================================================================================
# STEP 2: RETRIEVING THE ACCESS TOKEN USING THE AUTHORISATION CODE
#============================================================================================
tokens = exchange_code_for_tokens(token_endpoint, app_key, app_secret, redirect_url, auth_code)
access_token = tokens["access_token"]
refresh_token = tokens.get("refresh_token") # In case Saxo doesn't return a refresh token, the program will not crash
token_expiration = tokens["expires_in"]

# Saving the access token in a  .json file
#------------------------------------------
token_dict = {"access_token": access_token,
              "refresh_token": refresh_token,
              "token_expiration": token_expiration}

with open("./configuration/token_info.json", "w") as f:
    json.dump(token_dict, f)

print ("Access token succesfully retrieved and saved in your pc.")

