import os
import branca
import datetime as dt
import folium
import geojsoncontour
from matplotlib import cm, colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit_folium as st_folium
import xarray as xr

st.set_page_config(layout='wide')
st.title('ML Frontal Boundaries')

st.markdown('<h3 style="text-align: left; color: cyan; font-size: 14pt;">This is currently a demo product that will eventually feature real-time data.</h3>', unsafe_allow_html=True)

# colormaps of probability contours for front predictions
CONTOUR_CMAPS = {'CF': 'Blues', 'WF': 'Reds', 'SF': 'Greens', 'OF': 'Purples', 'CF-F': 'Blues', 'WF-F': 'Reds', 'SF-F': 'Greens',
                 'OF-F': 'Purples', 'CF-D': 'Blues', 'WF-D': 'Reds', 'SF-D': 'Greens', 'OF-D': 'Purples', 'INST': 'YlOrBr',
                 'TROF': 'YlOrRd', 'TT': 'Oranges', 'DL': 'copper_r', 'MERGED-CF': 'Blues', 'MERGED-WF': 'Reds', 'MERGED-SF': 'Greens',
                 'MERGED-OF': 'Purples', 'MERGED-F': 'Greys', 'MERGED-T': 'YlOrBr', 'F_BIN': 'Greys', 'MERGED-F_BIN': 'Greys'}

# names of front types
FRONT_NAMES = {'CF': 'Cold front', 'WF': 'Warm front', 'SF': 'Stationary front', 'OF': 'Occluded front', 'CF-F': 'Cold front (forming)',
               'WF-F': 'Warm front (forming)', 'SF-F': 'Stationary front (forming)', 'OF-F': 'Occluded front (forming)',
               'CF-D': 'Cold front (dying)', 'WF-D': 'Warm front (dying)', 'SF-D': 'Stationary front (dying)', 'OF-D': 'Occluded front (dying)',
               'INST': 'Outflow boundary', 'TROF': 'Trough', 'TT': 'Tropical trough', 'DL': 'Dryline', 'MERGED-CF': 'Cold front (any)',
               'MERGED-WF': 'Warm front (any)', 'MERGED-SF': 'Stationary front (any)', 'MERGED-OF': 'Occluded front (any)',
               'MERGED-F': 'CF, WF, SF, OF (any)', 'MERGED-T': 'Trough (any)', 'F_BIN': 'Binary front', 'MERGED-F_BIN': 'Binary front (any)'}

# model properties
model_properties = pd.read_pickle('I:/PycharmProjects/weather-hub/fronts/model_1701_properties.pkl')

# time arguments
date_input = st.date_input('Select Date', value=dt.datetime(2019, 5, 1), min_value=dt.datetime(2019, 5, 1), max_value=dt.datetime(2019, 5, 31))
time_input = st.time_input('Select Time (UTC)', value=dt.time(0, 0), step=dt.timedelta(hours=6))
timestep = dt.datetime.combine(date_input, time_input)

contour_levels = np.arange(0.1, 1.01, 0.1)
geomap_start_coords = [40, 250]

view_button = st.button("Show Map")

if view_button:
    
    year, month, day, hour = timestep.year, timestep.month, timestep.day, timestep.hour
    
    cwd = os.getcwd()
    probs_ds = xr.open_dataset('./fronts/model_1701_%d%02d%02d%02d_full.nc' % (year, month, day, hour), engine='netcdf4')
    
    # lat/lon coordinates
    front_labels = list(probs_ds.keys())
    lat = probs_ds['latitude'].values
    lon = probs_ds['longitude'].values
    Lon, Lat = np.meshgrid(lon, lat)
    
    geomap = folium.Map(geomap_start_coords, zoom_start=3, min_zoom=3, max_bounds=True, min_lat=-5, max_lat=85, min_lon=120, max_lon=380, tiles="Cartodb positron")

    for front_label in front_labels:
        
        front_type = FRONT_NAMES[front_label]
        cmap = CONTOUR_CMAPS[front_label]
        
        fg = folium.FeatureGroup(front_type)
        
        cmap_probs, norm_probs = cm.get_cmap(cmap, 11), colors.Normalize(vmin=0, vmax=1.0)
        
        # calibrate model predictions
        ir_model = model_properties['calibration_models']['conus'][front_label]['100 km']
        original_shape = np.shape(probs_ds[front_label].values)
        probs_ds[front_label].values = ir_model.predict(probs_ds[front_label].values.flatten()).reshape(original_shape)
        
        contourf = plt.contourf(Lon, Lat, probs_ds[front_label].values, cmap=cmap_probs, norm=norm_probs, levels=contour_levels, alpha=1)
        geojson_object = geojsoncontour.contourf_to_geojson(contourf=contourf, stroke_width=1)
        
        folium.GeoJson(
            geojson_object,
            style_function=lambda x: {
                'color':     x['properties']['stroke'],
                'weight':    x['properties']['stroke-width'],
                'fillColor': x['properties']['fill'],
                'opacity':   1.0,
            }).add_to(fg)

        fg.add_to(geomap)

        index_list = list(range(cmap_probs.N))
        branca_colors = list(tuple(cmap_probs(i)) for i in index_list)
        branca_cmap = branca.colormap.StepColormap(branca_colors, vmin=0.0, vmax=1.0, caption=front_type + ' probability')
        
        branca_cmap.width = 300
        branca_cmap.add_to(geomap)
    
    folium.LayerControl().add_to(geomap)
    
    st_folium.st_folium(geomap, width='relative', returned_objects=[])