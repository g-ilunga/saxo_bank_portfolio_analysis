#==========================================================================
# LIBRARY
#==========================================================================
import pandas as pd
import json
import plotly.express as px

#============================================================================
# LOADING RELEVANT INPUT FILES
#============================================================================

# Loading the positions spreadsheet and computing the proportion of each etf in the overall portfolio
#-----------------------------------------------------------------------------------------------------
positions = pd.read_excel("./portfolio/positions.xlsx")
positions["Proportion in %"] = (positions["Invested_amount"] / positions["Invested_amount"].sum() * 100).round(1)

# Importing the spreadsheet containing world countries and their respective continents
#-------------------------------------------------------------------------------------------
df_world_countries = pd.read_excel("./etf_data/countries.xlsx")


# Loading the file containing the geographic distribution of each etf and building a table out of it
#-----------------------------------------------------------------------------------------------------
with open('./etf_data/geographic_exposure.json', 'r') as f: 
    geography = json.load(f) 

list_geography = []
for etf_isin in geography:
    etf_geography = list(geography[etf_isin][0].keys())
    list_geography.extend(etf_geography)

list_geography_final = list(set(list_geography)) # Removing duplicate
df_geography = pd.DataFrame(list_geography_final, columns=["Countries"])


# Loading the file containing the sector distribution of each etf and building a table out of it
#--------------------------------------------------------------------------------------------------
with open('./etf_data/sector_allocation.json', 'r') as f: 
    sector = json.load(f)

list_sector = []
for etf_isin in sector:
    etf_sector = list(sector[etf_isin][0].keys())
    list_sector.extend(etf_sector)

list_sector_final = list(set(list_sector)) # Removing duplicate
df_sector = pd.DataFrame(list_sector_final, columns=["Sectors"])


#============================================================================================
# COMPUTING GEOGRAPHY AND SECTOR ALLOCATION
#============================================================================================

# Extracting sectoral allocation of each etf
#========================================================
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
#==============================================
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
# PLOTTING THE ALLOCATION
#=====================================================================================================

#================================================
# PLOTTING THE ALLOCATION
#================================================

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

