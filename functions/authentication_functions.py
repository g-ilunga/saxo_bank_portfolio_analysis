"""
This script contains functions developed for the authentication part of the tool
"""

#===========================================
# Importing libraries
#===========================================

import urllib.parse
import requests

#==================================================================================
# Constructing the login url to be used by the user to enter its Saxo credentials
#==================================================================================

def build_saxo_login_url(app_key, authorization_endpoint, redirect_url, scopes):
    
    params = {
        "response_type": "code",
        "client_id": app_key,
        "redirect_uri": redirect_url,
        "scope": "".join(scopes)
    }

    query_string = urllib.parse.urlencode(params) # It converts a Python dictionary into a properly encoded URL query string.
    login_url = f"{authorization_endpoint}?{query_string}"
    return login_url

"""
Note:
This function will generate a url. When accessing the url, the user will be prompted to enter its Saxo Investor credentials.
Once successfully authenticated, Saxo will provide an authentication code that will be used to obtain an access token to be used to query the investment accounts.
"""

#=============================================================================================
# Building a function that will use access code provided by Saxo after logging to get tokens
#=============================================================================================

def exchange_code_for_tokens(token_endpoint, app_key, app_secret, redirect_url, auth_code):
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_url,
        "client_id": app_key,
        "client_secret": app_secret
    }

    response = requests.post(token_endpoint, data=data)
    response.raise_for_status()
    return response.json()

"""
Note:
The function will return:
- The access token: to be used to query the investment accounts
- The refresh token: since the access token expires after few minutes, Saxo provides this refresh token to avoid redoing the entire authentication process
- The validity of the access token. Usually in seconds
"""

#==============================================
# Activating the Refresh token
#==============================================

def refresh_access_token(token_endpoint, app_key, app_secret, refresh_token):
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
        "client_secret": app_secret
    }

    response = requests.post(token_endpoint, data=data)
    response.raise_for_status()
    return response.json()