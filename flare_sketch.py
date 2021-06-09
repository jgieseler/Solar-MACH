import streamlit as st
from backmapping import *
import datetime

st.title('Multi-spacecraft longitudinal configuration plotter')

st.header('Provide date and time')
# date = '2020-05-01 13:00:00'
d = st.date_input("Select date", datetime.date.today())
# st.write('Selected date:', d)
t = st.time_input('Select time', datetime.time(16, 45))
# st.write('Selected time:', t)
date = datetime.datetime.combine(d, t).strftime("%Y-%m-%d %H:%M:%S")
st.write('Selected datetime:', date)

st.markdown("""---""")

st.header('Chose bodies/spacecraft and measured solar wind speeds')
st.subheader('vst_list: leave empty for nominal speed of vsw=400 km/s')
st.write(print_body_list())

body_list = ['STEREO-A', 'STEREO-B', 'Earth', 'MPO', 'PSP', 'Solar Orbiter',
             'Mars']
vsw_list = [300, 400, 500, 600, 700, 800, 900, 200]

# body_list = st.multiselect('SC', ['STEREO-A', 'STEREO-B', 'Earth', 'MPO', 'PSP', 'Solar Orbiter', 'Mars'])
# vsw_list = st.multiselect('v', [300, 400, 500, 600, 700, 800, 900, 200])
st.write(body_list, vsw_list)

st.markdown("""---""")

st.header('Provide a reference longitude in Carrington coordinates (e.g. flare longitude)')
reference_long = 20
reference_lat = -20
reference_long = st.slider('Reference longitude:', 0, 360, 20)
reference_lat = st.slider('Reference latitude:', -180, 180, -20)
st.write('Selected reference longitude and latituide:', reference_long, reference_lat)

st.markdown("""---""")

# Initialize the Bodies
c = HeliosphericConstellation(date, body_list, vsw_list, reference_long,
                              reference_lat)

# Display coordinates
st.write(c.coord_table)

st.markdown("""---""")

# Make the longitudinal constellation plot
c.plot(
    plot_spirals=True,               # plot Parker spirals for each body
    plot_sun_body_line=True,         # plot straight line between Sun and body
    show_earth_centered_coord=True,  # display Earth-centered coordinate system
    outfile='plot.png'               # output file (optional)
)
