#!/usr/bin/env python
# coding: utf-8

# In[2]:


import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
import math
import io
import xlsxwriter
import geopandas as gpd
import folium
import osmnx as ox
import plotly.express as px
import re

from shapely.geometry import Point, LineString, Polygon
import matplotlib.pyplot as plt

# In[3]:

st.title('Crowdsource Automation')

data_amenity = {'amenity': ['all', 'apartment', 'cafe', 'campus', 'cemetery', 'farming', 'gas station', 'hospital', 'hotel', 
                            'industrial area', 'kindergarten', 'mall', 'mining area', 'modern market', 'office', 'palm oil', 
                            'public facilities', 'pumping station', 'residential', 'restaurant', 'school', 'tourist park', 
                            'traditional market', 'transport hub', 'voucher shop', 'warehouse', 'worship place']}
data_building = {'building': ['all', 'apartment', 'cafe', 'campus', 'cemetery', 'farming', 'gas station', 'hospital', 'hotel', 
                            'industrial area', 'kindergarten', 'mall', 'mining area', 'modern market', 'office', 'palm oil', 
                            'public facilities', 'pumping station', 'residential', 'restaurant', 'school', 'tourist park', 
                            'traditional market', 'transport hub', 'voucher shop', 'warehouse', 'worship place']}
        
df_amn = pd.DataFrame(data_amenity)
df_bld = pd.DataFrame(data_building)
        
st.sidebar.header("Please Filter Here:")
amenity = st.sidebar.multiselect("Select the Amenity:", options=df_amn["amenity"].unique(), default="all")
building = st.sidebar.multiselect("Select the Building:", options=df_bld["building"].unique(), default="all")
if "all" in amenity:
    amenity = df_amn["amenity"].unique()
    df_selection1 = df_amn.query("amenity == @amenity")
if "all" in building:
    building = df_bld["building"].unique()
    df_selection2 = df_bld.query("building == @building")
#st.dataframe(df_selection1)
#st.dataframe(df_selection2)
df_selection1 = df_amn.query("amenity == @amenity")
df_selection2 = df_bld.query("building == @building")
excel_file = st.file_uploader("Upload File", type=['xls','xlsx'])

buffer = io.BytesIO()

if excel_file is not None:
    a = pd.read_excel(excel_file)
    st.dataframe(a)
    
    for column in a.columns:
      if a[column].dtype in [float, int] and a[column].between(-180, 180).all() and not a[column].between(-90, 90).all():
        a = a.rename(columns={column: "Long"})
      elif a[column].dtype in [float, int] and a[column].between(-90, 90).all():
        a = a.rename(columns={column: "Lat"})
    #gdf.rename(columns={'Lat':'Lat_TBG','Long':'Long_TBG'}, inplace=True)
    
    #st.dataframe(gdf)
    gdf_append = []
    progress_status = st.empty()
    bar = st.progress(0)
    for i in a.index:
    ## Explore amenity tags (https://wiki.openstreetmap.org/wiki/Key:amenity)
    ## Explore building tags (https://wiki.openstreetmap.org/wiki/Key:building)
    ## Explore tourism tags (https://wiki.openstreetmap.org/wiki/Key:tourism)
        
        tags = {'amenity': df_selection1['amenity'].values.tolist(), 'building': df_selection2['building'].values.tolist()}

    ## Input points (Lat, Long) and distance (radius in meters)
    ## Multiple input points? Modify using for loop...
        gdf = ox.geometries.geometries_from_point((a["Lat"][i], a["Long"][i]), tags, dist=1000).reset_index()
        gdf["Lat"] = a["Lat"][i]
        gdf["Long"] = a["Long"][i]
        if i == len(a)-1:
            bar.progress(100)
            progress_status.write(str(100)+f"% ({len(a)}/{len(a)})")
        else:
            bar.progress(round((i+1)*((100/len(a)))))
            progress_status.write(str(round((i+1)*((100/len(a)))))+f"% ({i+1}/{len(a)})")
        gdf_append.append(gdf)
    
    gdf_append = pd.concat(gdf_append)
    if "amenity" in gdf_append.columns:
        if "name:en" in gdf_append.columns:
            if "building" in gdf_append.columns:
                gdf_append = gdf_append[['geometry', 'Lat', 'Long', 'osmid', 'amenity', 'building', 'name', 'name:en']]
            else:
                gdf_append = gdf_append[['geometry', 'Lat', 'Long', 'osmid', 'amenity','name', 'name:en']]
        elif "building" in gdf_append.columns:
            gdf_append = gdf_append[['geometry', 'Lat', 'Long', 'osmid', 'amenity', 'building','name']]
        else:
            gdf_append = gdf_append[['geometry', 'Lat', 'Long', 'osmid', 'amenity', 'name']]
    elif "building" in gdf_append.columns:
        gdf_append = gdf_append[['geometry', 'Lat', 'Long', 'building']]
    else:
        gdf_append = gdf_append[['geometry', 'Lat', 'Long']]
    gdf_append = pd.merge(a, gdf_append, on=["Lat", "Long"], how='inner')
## Tambahan : tolong buat kolom baru nama_POI yang isinya value dari kolom name atau name:en. Jika kedua kolom ada isinya prioritasin kolom name yang diambil.
## Rename kolom Lat Long menjadi Lat_TBG dan Long_TBG
## Kolom geometry untuk yang POINT bisa langsung di extract long lat nya > buat kolom baru lagi long_POI dan lat_POI
## Kolom geometry untuk yang POLYGON harus dicari dulu centroidnya. Setelah itu baru di extraxt long lat nya.
    gdf_append.rename(columns={'Lat':'Lat_TBG','Long':'Long_TBG'}, inplace=True)
    if "name" in gdf_append.columns:
        gdf_append['name'] = gdf_append['name'].fillna('none')
        nama_POI=[]
        if "name:en" in gdf_append.columns:
            gdf_append['name:en'] = gdf_append['name:en'].fillna('none')
            for i in gdf_append.index:
                if (gdf_append['name'][i]!="none"):
                    nama_POI.append(gdf_append['name'][i])
                elif (gdf_append['name'][i]=="none"):
                    if (gdf_append['name:en'][i]!="none"):
                        nama_POI.append(gdf_append['name:en'][i])
                    else:
                        nama_POI.append("none")
        else:
            for i in gdf_append.index:
                nama_POI.append(gdf_append['name'][i])
        gdf_append['nama_POI']=nama_POI

    Lat_POI = []
    Long_POI = []
    for i in gdf_append.index:
        if gdf_append['geometry'][i].geom_type == "Polygon":
            Long_POI.append(gdf_append['geometry'][i].centroid.x)
            Lat_POI.append(gdf_append['geometry'][i].centroid.y)
        elif gdf_append['geometry'][i].geom_type == "MultiPolygon":
            Long_POI.append(gdf_append['geometry'][i].centroid.x)
            Lat_POI.append(gdf_append['geometry'][i].centroid.y)
        elif gdf_append['geometry'][i].geom_type == "Point":
            Long_POI.append(gdf_append['geometry'][i].x)
            Lat_POI.append(gdf_append['geometry'][i].y)
    gdf_append["Long_POI"]=Long_POI
    gdf_append["Lat_POI"]=Lat_POI
    
    if "name" in gdf_append.columns:
        if "name:en" in gdf_append.columns:
            gdf_append = gdf_append.drop(['name', 'name:en'], axis=1)
        else:
            gdf_append = gdf_append.drop(['name'], axis=1)
    gdf_append = gdf_append.drop(['geometry'], axis=1)
    gdf_append = gdf_append.drop_duplicates()
                             
    if "nama_POI" in gdf_append.columns:
        gdf_append = gdf_append.drop_duplicates(subset=[gdf_append.columns.values[0], 'amenity', 'nama_POI'], keep='first').reset_index(drop=True)
        if "building" in gdf_append.columns:
            gdf_append = gdf_append.drop_duplicates(subset=[gdf_append.columns.values[0], 'building', 'nama_POI'], keep='first').reset_index(drop=True)
    
    amenities = []
    if "amenity" in gdf_append.columns:
        gdf_append['amenity'] = gdf_append['amenity'].fillna('none')
        for i in gdf_append.index:
            if (gdf_append['amenity'][i]!="none"):
                amenities.append(gdf_append['amenity'][i])
            elif (gdf_append['amenity'][i]=="none"):
                if "building" in gdf_append.columns:
                    gdf_append['building'] = gdf_append['building'].fillna('none')
                    if (gdf_append['building'][i]!="none"):
                        amenities.append(gdf_append['building'][i])
            else:
                amenities.append("none")
    elif "building" in gdf_append.columns:
        gdf_append['building'] = gdf_append['building'].fillna('none')
        for i in gdf_append.index:
            amenities.append(gdf_append['building'][i])
    gdf_append.insert(4, "POI", amenities, True)  
    #gdf_append['amenity'].fillna(gdf_append['building'], inplace=True)
    if "amenity" in gdf_append.columns:
        if "building" in gdf_append.columns:
            gdf_append = gdf_append.drop(['amenity', 'building'], axis=1)
        else:
            gdf_append = gdf_append.drop(['amenity'], axis=1)
    elif "building" in gdf_append.columns:
        gdf_append = gdf_append.drop(['building'], axis=1)
    else:
        st.write("Sorry, it seems the sites don't have any POI")
        exit()
     
    if "nama_POI" in gdf_append.columns:
        for i in gdf_append.index:
            if re.search(str("Hotel|hotel|HOTEL|Homestay|homestay|HOMESTAY|Wisma|wisma|WISMA|Villa|villa|VILLA|Residence|residence|RESIDENCE|Guesthouse|guesthouse|GUESTHOUSE|Penginapan|penginapan|PENGINAPAN|Resort|resort|RESORT"), str(gdf_append['nama_POI'][i])):
                gdf_append['POI'][i] = "Hotel"
                    
    for i in gdf_append.index:
        if gdf_append["POI"][i] == "none":
            gdf_append['POI'] = 'public facilities'
    gdf_append['POI'] = gdf_append['POI'].str.title()
                             
    for i in gdf_append.index:
        if gdf_append['POI'][i]=='School' or gdf_append['POI'][i]=='Campus' or gdf_append['POI'][i]=='Kindergarten' or gdf_append['POI'][i]=='College':
            gdf_append['POI'][i]="School/Campus"
        elif gdf_append['POI'][i]=='Restaurant' or gdf_append['POI'][i]=='Cafe':
            gdf_append['POI'][i]="Restaurant / Cafe"
        elif gdf_append['POI'][i]=='Government' or gdf_append['POI'][i]=='Police' or gdf_append['POI'][i]=='Bank' or gdf_append['POI'][i]=='Townhall':
            gdf_append['POI'][i]="Office"
        elif gdf_append['POI'][i]=='Clinic':
            gdf_append['POI'][i]="Hospital"
        elif gdf_append['POI'][i]=='Place_Of_Worship':
            gdf_append['POI'][i]="worship place"
        elif gdf_append['POI'][i]=='Apartments':
            gdf_append['POI'][i]="Apartment"
              
    amenity = ['Apartment','School/Campus','Gas Station','Restaurant / Cafe', 'Hospital', 'Hotel', 'Cemetery', 'Farming', 'Industrial Area', 'Mall', 'Mining Area', 'Modern Market', 'Office', 'Palm Oil', 'public facilities', 'Pumping Station', 'Residential', 'Tourist Park', 'Traditional Market', 'Transport Hub', 'Voucher Shop', 'Warehouse', 'worship place']
    
    for i in gdf_append['POI'].unique():
        if i not in amenity:
            for j in gdf_append.index:
                if gdf_append['POI'][j]==i:
                    gdf_append['POI'][j]='public facilities'
                           
    #gdf_append = gdf_append.rename(columns={"Lat_POI":"lat","Long_POI":"lon"})
    st.dataframe(gdf_append)
    st.markdown("<h1 style='font-size: 20px;'>POI Distribution by Location</h1>", unsafe_allow_html=True)
    fig = px.scatter_mapbox(gdf_append, lat="Lat_POI", lon="Long_POI", hover_name="POI", zoom=4)
    fig.update_traces(hovertemplate='<b>Location:</b> %{hovertext}<br><b>nama_POI:</b> %{"nama_POI"}<br><b>POI:</b> %{hovertext}')
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig)
    #st.map(gdf_append)
    
    col1, col2 = st.columns(2)
    with col1:
      st.markdown("<h1 style='font-size: 20px;'>Distribution of POI Category</h1>", unsafe_allow_html=True)
      fig = plt.figure(figsize=(10,7))
      values = gdf_append["POI"].value_counts()
      plt.title("POI Category Distribution")
      plt.ylabel("Category")
      plt.xlabel("Number of POI")
      plt.barh(values.index, values)
      st.pyplot(fig)
    
    x = []
    for i in gdf_append[gdf_append.columns.values[0]].unique():
        x.append(gdf_append.loc[gdf_append[gdf_append.columns.values[0]] == i, 'POI'].unique())
    
    z=[]
    for i in range(len(x)):
        y=""
        for j in range(len(x[i])):
            y = y+x[i][j]
            if j < (len(x[i])-1):
                y = y+"+"
        z.append(y)

    gdf_append = gdf_append.drop_duplicates(subset=[gdf_append.columns.values[0]], keep='first').reset_index(drop=True)
    gdf_append["POIs"]=z
    gdf_summary = gdf_append[[gdf_append.columns.values[0], 'POIs']].copy()
    gdf_summary.rename(columns={'POIs':'POI'}, inplace=True)
    #gdf_append['geometry'] = gdf_append['geometry'].astype(str)
    
    #piechart
    with col2:
      st.markdown("<h1 style='font-size: 20px;'>Distribution of Site with and without POI</h1>", unsafe_allow_html=True)
      fig1, ax = plt.subplots()
      fig.set_size_inches(10, 7)
      #fig1 = plt.figure(figsize=(10,7))
      labels = ["Site with POI", "Site without POI"]
      sizes = [gdf_summary[gdf_append.columns.values[0]].nunique(), (len(a)-gdf_summary[gdf_append.columns.values[0]].nunique())]
      #plt.set_ylim(top=1)
      ax.pie(sizes, labels = labels, autopct='%1.1f%%')
      ax.set_ylim(top=1)
      #plt.pie(sizes, labels = labels, autopct='%1.1f%%')
    #fig1,ax1 = plt.subplots()
    #ax1.pie(sizes, labels=labels, , autopct='%1.1f%%')
    #ax1.set_title("tes")
    #ax1.axis('equal')
      st.pyplot(fig1)
    
    #barchart
    #fig = plt.figure(figsize=(10,7))
    #values = gdf_append["amenities"].value_counts()
    #plt.bar(values.index, values, width = 0.4)
    #st.pyplot(fig)
    
    st.dataframe(gdf_summary)
    # download button 2 to download dataframe as xlsx
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        gdf_summary.to_excel(writer, sheet_name='Sheet1', index=False)
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.close()

        download2 = st.download_button(
            label="Download data as Excel",
            data=buffer,
            file_name='large_df.xlsx',
            mime='application/vnd.ms-excel'
        )
