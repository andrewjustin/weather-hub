from datetime import datetime
import requests
import streamlit as st

st.set_page_config(layout="wide")

st.title("Nadocast Viewer")

st.markdown('### Forecast Options')

historical_data = st.checkbox('Historical Data')

today_date = datetime.utcnow().date()
if historical_data:
    date_input = st.date_input("Select Date", value=today_date, min_value=datetime(2022, 4, 20), max_value=today_date)
else:
    date_input = st.date_input("Select Date", value=today_date, max_value=today_date, disabled=True, label_visibility='collapsed')

if datetime.fromisoformat(date_input.isoformat()) < datetime.fromisoformat(datetime(2023, 1, 31).isoformat()):
    init_time = st.radio('Initialization Time', options=['0z', '10z', '12z', '14z', '18z'], key='1_radio_init_time', horizontal=True, label_visibility='collapsed')
else:
    init_time = st.radio('Initialization Time', options=['0z', '12z', '14z', '18z'], key='1_radio_init_time', horizontal=True, label_visibility='collapsed')


if init_time == '0z':
    forecast_hours = st.radio('Forecast Hour Range', ['12 - 35'], index=0, disabled=True)
elif init_time == '10z':
    forecast_hours = st.radio('Forecast Hour Range', ['02 - 25'], index=0, disabled=True)
elif init_time == '12z':
    forecast_hours = st.radio('Forecast Hour Range', ['02 - 23', '24 - 47'], index=0)
elif init_time == '14z':
    forecast_hours = st.radio('Forecast Hour Range', ['02 - 21'], index=0, disabled=True)
else:  # 18z
    forecast_hours = st.radio('Forecast Hour Range', ['02 - 17'], index=0, disabled=True)

disable_options = True if init_time in ['10z', '14z'] else False

sig_haz = st.checkbox('Significant Hazards', disabled=disable_options)
abs_cal = st.checkbox('Absolutely Calibrated', disabled=disable_options)
adjusted = st.checkbox('Adjusted (Wind only)', disabled=disable_options)

get_forecast = st.button('Retrieve Forecast')

if get_forecast:
    
    year, month, day = date_input.year, date_input.month, date_input.day
    
    # start by making the link to the wind forecast first because it is the only hazard with the 'adjusted' option
    wind_link = "http://data.nadocast.com/%d%02d/%d%02d%02d/t%s/nadocast_2022_models_conus_" % (year, month, year, month, day, init_time)
    if sig_haz:
        wind_link += 'sig_'
    wind_link += 'wind_'
    if adjusted:
        wind_link += 'adj_'
    if abs_cal:
        wind_link += 'abs_calib_'
    wind_link += '%d%02d%02d_t%s_f%s.png' % (year, month, day, init_time.zfill(3), forecast_hours.replace(' ', ''))
    
    # filename format changed on November 29, 2022
    if datetime.fromisoformat(date_input.isoformat()) < datetime.fromisoformat(datetime(2022, 11, 28).isoformat()):
        wind_link = wind_link.replace('_2022_', '_')
    
    # 14z forecast uses older nadocast model
    if init_time in ['10z', '14z']:
        wind_link = wind_link.replace('_2022_', '_2020_')
    
    hail_link = wind_link.replace('adj_', '').replace('wind', 'hail')
    tor_link = hail_link.replace('hail', 'tornado')
    
    try:
        forecast_exists = requests.get(tor_link).ok
    except ConnectionAbortedError:
        st.write(":red[Connection error. Please try again later.]")
    else:
        
        if forecast_exists:
            
            if init_time != '14z' and init_time != '10z':
                
                col1, col2, col3 = st.columns(3)
                
                # titles that will be displayed above the retrieved images
                tor_img_title = "Tornado"
                hail_img_title = "Hail"
                wind_img_title = "Wind"
                
                if sig_haz and abs_cal:
                    tor_img_title += " (SIG, calibrated)"
                    hail_img_title += " (SIG, calibrated)"
                    if adjusted:
                        wind_img_title += " (SIG, calibrated, adjusted)"
                    else:
                        wind_img_title += " (SIG, calibrated)"
                elif sig_haz:
                    tor_img_title += " (SIG)"
                    hail_img_title += " (SIG)"
                    if adjusted:
                        wind_img_title += " (SIG, adjusted)"
                    else:
                        wind_img_title += " (SIG)"
                elif abs_cal:
                    tor_img_title += " (calibrated)"
                    hail_img_title += " (calibrated)"
                    if adjusted:
                        wind_img_title += " (calibrated, adjusted)"
                    else:
                        wind_img_title += " (calibrated)"
                
                with col1:
                    st.html("<h1 style='text-align: center; color: red; font-size: 16pt;'>%s</h1>\n"
                            "<img align='center' style='width: inherit', src=%s>\n"
                            "<div style='text-align: center'>\n"
                            "<a href=%s>Download GRIB2</a>\n"
                            "</div>" % (tor_img_title, tor_link, tor_link.replace('.png', '.grib2')))
                with col2:
                    st.html("<h1 style='text-align: center; color: limegreen; font-size: 16pt;'>%s</h1>\n"
                            "<img align='center' style='width: inherit', src=%s>\n"
                            "<div style='text-align: center'>\n"
                            "<a href=%s>Download GRIB2</a>\n"
                            "</div>" % (hail_img_title, hail_link, hail_link.replace('.png', '.grib2')))
                with col3:
                    st.html("<h1 style='text-align: center; color: #0095ff; font-size: 16pt;'>%s</h1>\n"
                            "<img align='center' style='width: inherit', src=%s>\n"
                            "<div style='text-align: center'>\n"
                            "<a href=%s>Download GRIB2</a>\n"
                            "</div>" % (wind_img_title, wind_link, wind_link.replace('.png', '.grib2')))
            
            else:
                st.markdown("<h1 style='text-align: center; color: red; font-size: 16pt;'>Tornado</h1>", unsafe_allow_html=True)
                st.html("<img align='center' style='width: inherit', src=%s>\n"
                        "<div style='text-align: center'>\n"
                        "<a href=%s>Download GRIB2</a>\n"
                        "</div>" % (tor_link, tor_link.replace('.png', '.grib2')))

        else:
            
            st.write(":red[The requested forecast was not found. Try a different date/time or try again later.]")
