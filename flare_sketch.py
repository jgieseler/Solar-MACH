import streamlit as st
from backmapping import *
import datetime

st.title('Multi-spacecraft longitudinal configuration plotter')

# st.sidebar.subheader('Provide date and time')
d = st.sidebar.date_input("Select date", datetime.date.today())
t = st.sidebar.time_input('Select time', datetime.time(16, 45))
date = datetime.datetime.combine(d, t).strftime("%Y-%m-%d %H:%M:%S")


st.sidebar.subheader('Provide a reference longitude in Carrington coordinates (e.g. flare longitude)')
reference_long = st.sidebar.slider('Reference longitude:', 0, 360, 20)
reference_lat = st.sidebar.slider('Reference latitude:', -180, 180, -20)
# st.write('Selected reference longitude and latituide:',
#          reference_long, reference_lat)


st.sidebar.subheader('Chose bodies/spacecraft and measured solar wind speeds')
# st.sidebar.subheader('vst_list: leave empty for nominal speed of \
#                       vsw=400 km/s')
full_body_list = \
    st.sidebar.text_area('bodies/spacecraft (scroll down for full list)',
                         'STEREO-A, STEREO-B, Earth, MPO, PSP, Solar Orbiter, Mars',
                         height=50)
vsw_list = \
    st.sidebar.text_area('vst_list', '400, 400, 400, 400, 400, 400, 400, 400',
                         height=50)
body_list = full_body_list.split(',')
vsw_list = vsw_list.split(',')
body_list = [np.int(body_list[i].lstrip()) for i in range(len(body_list))]
vsw_list = [np.int(vsw_list[i].lstrip()) for i in range(len(vsw_list))]

all_bodies = print_body_list()
st.sidebar.table(all_bodies)


# Initialize the Bodies
c = HeliosphericConstellation(date, body_list, vsw_list, reference_long,
                              reference_lat)

# Make the longitudinal constellation plot
c.plot(
    plot_spirals=True,               # plot Parker spirals for each body
    plot_sun_body_line=True,         # plot straight line between Sun and body
    show_earth_centered_coord=True,  # display Earth-centered coordinate system
    outfile='plot.png'               # output file (optional)
)

# Display coordinates
st.dataframe(c.coord_table)
