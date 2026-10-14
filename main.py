#========================================================================================
# LIBRARIES
#========================================================================================
import json
import urllib.parse
import webbrowser
import requests
import pandas as pd
import plotly.express as px

# Importing local modules that were created for authentication ("functions." is the folder where the modules are located)
from functions.authentication_functions import build_saxo_login_url
from functions.authentication_functions import exchange_code_for_tokens
from functions.accessing_portfolio_functions import retrieving_keys
from functions.accessing_portfolio_functions import getting_open_positions

#========================================================================================
# LOADING NECESSARY FILES
#========================================================================================

# Loading the info related to the liveapp created on Saxo developer portal
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
isin_database = pd.read_excel("./etf_data/isin_database.xlsx")

# Importing the spreadsheet containing world countries and their respective continents
df_world_countries = pd.read_excel("./etf_data/countries.xlsx")

# Loading the file containing the geographic distribution of each etf and building a table out of it
with open('./etf_data/geographic_exposure.json', 'r') as f: 
    geography = json.load(f) 

list_geography = []
for etf_isin in geography:
    etf_geography = list(geography[etf_isin][0].keys())
    list_geography.extend(etf_geography)

list_geography_final = list(set(list_geography)) # Removing duplicate
df_geography = pd.DataFrame(list_geography_final, columns=["Countries"])


# Loading the file containing the sector distribution of each etf and building a table out of it
with open('./etf_data/sector_allocation.json', 'r') as f: 
    sector = json.load(f)

list_sector = []
for etf_isin in sector:
    etf_sector = list(sector[etf_isin][0].keys())
    list_sector.extend(etf_sector)

list_sector_final = list(set(list_sector)) # Removing duplicate
df_sector = pd.DataFrame(list_sector_final, columns=["Sectors"])

#==========================================================================================
# 1. AUTHENTICATING
#==========================================================================================

# Retrieving the authorisation code
login_url = build_saxo_login_url(app_key, authorization_endpoint, redirect_url, scopes) # Constructing the url that will be used to log in to your Saxo account
webbrowser.open(login_url) # Opening the url to enter the Saxo account credential

# Extracting the authorisation code from  the redirect url
auth_url = str(input("Paste the redirect url here: ")) # Prompting the user to paste the redirect url
parsed = urllib.parse.urlparse(auth_url)
params = urllib.parse.parse_qs(parsed.query)
auth_code = params.get("code", [None])[0]

# Retrieving the access token using the authorisation code
tokens = exchange_code_for_tokens(token_endpoint, app_key, app_secret, redirect_url, auth_code)
access_token = tokens["access_token"]
refresh_token = tokens.get("refresh_token") # In case Saxo doesn't return a refresh token, the program will not crash
token_expiration = tokens["expires_in"]

print ("Access token succesfully retrieved.")

# Retrieving client key and account key
keys = retrieving_keys(access_token, app_key)
client_key = keys[0]["client_key"]
account_key = keys[1]

#==================================================================================================
# 2. GETTING OPEN POSITIONS IN A GIVEN ACCOUNT
#==================================================================================================

# Selecting the desired account. I hardcoded two options since my Saxo portfolio has 2 accounts
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

# Getting open position
positions = getting_open_positions(account_key, client_key, access_token, app_key)
positions["ISIN"] = positions["Symbol"].map(isin_database.set_index("Symbol")["ISIN"]) # Retrieving ISIN from our database


#==============================================================
# 3. COMPUTING GEOGRAPHY AND SECTOR ALLOCATION
#==============================================================

positions["Proportion in %"] = (positions["Invested_amount"] / positions["Invested_amount"].sum() * 100).round(1) # Proportion of each etf in the portfolio

# Extracting sectoral allocation of each etf
for etf_isin in list(positions["ISIN"]):
    df = pd.DataFrame(list(sector[etf_isin][0].items()), columns=["Sectors", "Allocation in ETF"]) #Turn the dictionnary of etf composition into table
    proportion = positions.loc[positions["ISIN"] == etf_isin, "Proportion in %"].iloc[0] # proportion in % of each etf
    df[etf_isin] = (df["Allocation in ETF"] * proportion/100).round(1) # Find the actual allocation using the proportion the etf occupies in the porfolio
    df = df.drop(columns="Allocation in ETF")
    df_sector = df_sector.merge(df, on="Sectors", how="left")
    df_sector = df_sector.fillna(0)
df_sector["Total"] = df_sector.select_dtypes(include="number").sum(axis=1)
df_sector_final = df_sector[["Sectors", "Total"]]

# Extracting geography allocation of each etf
for etf_isin in list(positions["ISIN"]):
    df = pd.DataFrame(list(geography[etf_isin][0].items()), columns=["Countries", "Allocation in ETF"]) #Turn the dictionnary into table
    proportion = positions.loc[positions["ISIN"] == etf_isin, "Proportion in %"].iloc[0] # proportion in % of each etf
    df[etf_isin] = (df["Allocation in ETF"] * proportion/100).round(1) # Find the actual allocation using the proportion the etf occupies in the porfolio
    df = df.drop(columns="Allocation in ETF")
    df_geography = df_geography.merge(df, on="Countries", how="left")
    df_geography = df_geography.fillna(0)
df_geography["Total"] = df_geography.select_dtypes(include="number").sum(axis=1)
df_geography_final = df_geography[["Countries","Total"]]
df_geography_final = df_geography_final[df_geography_final["Countries"] != "Precious metal"] # Removing precious metal from the list of countries

# Adding the continents on the dataframe for easier analysis
df_geography_final = df_geography_final.merge(df_world_countries[["Countries", "Continent"]],
                                              on="Countries", how="left", validate="many_to_one")

#=====================================================================================================
# 4. PLOTTING THE ALLOCATION
#=====================================================================================================

# Plotting the geographic allocation
#--------------------------------------------

# Aggregate values by continent
pie_data = (df_geography_final.groupby("Continent", as_index=False)["Total"].sum())

# Create the pie chart
fig = px.pie(
    pie_data,
    names="Continent",
    values="Total",
    title="Geographic allocation in percentage",
    hole=0 
)

# Configure labels shown inside/on hover
fig.update_traces(
    textposition="inside",
    textinfo="value+label",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Proportion: %{value:,.0f}%<br>"
        "<extra></extra>"
    )
)

fig.update_layout(template="plotly_white")

fig.show()

# Plotting the sector allocation
#--------------------------------------------

pie_data = df_sector_final

# Create the pie chart
fig = px.pie(
    pie_data,
    names="Sectors",
    values="Total",
    title="Sector allocation in percentage",
    hole=0 
)

# Configure labels shown inside/on hover
fig.update_traces(
    textposition="inside",
    textinfo="value+label",
    hovertemplate=(
        "<b>%{label}</b><br>"
        "Proportion: %{value:,.0f}%<br>"
        "<extra></extra>"
    )
)

fig.update_layout(template="plotly_white")

fig.show()

