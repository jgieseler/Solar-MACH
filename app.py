import datetime

import astropy.units as u
import streamlit as st
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

from backmapping import *

# -- Set page config
st.set_page_config(page_title='Solar-MACH', page_icon=":satellite:", 
                   initial_sidebar_state="expanded")

st.title('Multi-spacecraft longitudinal configuration plotter')

# st.sidebar.subheader('Provide date and time')
with st.sidebar.beta_container():
    d = st.sidebar.date_input("Select date", datetime.date.today())
    t = st.sidebar.time_input('Select time', datetime.time(13, 0))
    date = datetime.datetime.combine(d, t).strftime("%Y-%m-%d %H:%M:%S")

# plotting settings
with st.sidebar.beta_container():
    st.sidebar.subheader('Plot options:')
    plot_spirals = st.sidebar.checkbox('Parker spiral for each body', value=True)
    plot_sun_body_line = st.sidebar.checkbox('Straight line from Sun to body', value=True)
    show_earth_centered_coord = st.sidebar.checkbox('Add Earth-aligned coord. system', value=False)

    plot_reference = st.sidebar.checkbox('Plot reference (e.g. flare)', value=True)

    with st.sidebar.beta_expander("Reference coordinates (e.g. flare)", expanded=plot_reference):
        reference_sys = st.radio('Coordinate system:', ['Carrington', 'Stonyhurst'], index=0)
        # st.sidebar.subheader('Reference longitude in Carrington coordinates (e.g. flare longitude)')
        reference_long = st.slider('Longitude:', 0, 360, 20)
        reference_lat = st.slider('Latitude:', -180, 180, 0)
        # convert Stonyhurst coordinates to Carrington for further use:
        if reference_sys == 'Stonyhurst':
            coord = SkyCoord(reference_long*u.deg, reference_lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=date)
            coord = coord.transform_to(frames.HeliographicCarrington(observer='Sun'))
            reference_long = coord.lon.value
            reference_lat = coord.lat.value
    
    if plot_reference is False:
        reference_long = None
        reference_lat = None


    # st.write('Selected reference longitude and latituide:',
    #          reference_long, reference_lat)


st.sidebar.subheader('Choose bodies/spacecraft and measured solar wind speeds')
with st.sidebar.beta_container():
    # st.sidebar.subheader('vsw_list: leave empty for nominal speed of \
    #                       vsw=400 km/s')
    full_body_list = \
        st.sidebar.text_area('Bodies/spacecraft (scroll down for full list)',
                            'STEREO-A, Earth, BepiColombo, PSP, Solar Orbiter, Mars',
                            height=50)
    vsw_list = \
        st.sidebar.text_area('Solar wind speed per body/SC (mind the order!)', '400, 400, 400, 400, 400, 400',
                            height=50)
    body_list = full_body_list.split(',')
    vsw_list = vsw_list.split(',')
    body_list = [body_list[i].lstrip() for i in range(len(body_list))]
    vsw_list = [int(vsw_list[i].lstrip()) for i in range(len(vsw_list))]

    all_bodies = print_body_list()
    st.sidebar.table(all_bodies)

    st.sidebar.markdown('[Complete list of available bodies](https://ssd.jpl.nasa.gov/horizons.cgi?s_target=1#top)')


# Initialize the Bodies
c = HeliosphericConstellation(date, body_list, vsw_list, reference_long,
                              reference_lat)


# Make the longitudinal constellation plot
c.plot(
    plot_spirals=plot_spirals,               # plot Parker spirals for each body
    plot_sun_body_line=plot_sun_body_line,         # plot straight line between Sun and body
    show_earth_centered_coord=show_earth_centered_coord,  # display Earth-aligned coordinate system
    # outfile='plot.png'               # output file (optional)
)


# Display coordinates
st.dataframe(c.coord_table)

st.markdown("""---""")
st.markdown('*The Solar MAgnetic Connection Haus (Solar-MACH) tool was originally \
            developed at Kiel University, Germany and further discussed within \
            the [ESA Heliophysics Archives USer (HAUS)]\
            (https://www.cosmos.esa.int/web/esdc/archives-user-groups/heliophysics) \
            group. It is now opened to everyone* ([original code]\
            (https://github.com/esdc-esac-esa-int/Solar-MACH)).')

st.markdown('[Forked and modified](https://github.com/jgieseler/Solar-MACH) by \
            [J. Gieseler](https://jgieseler.github.io) \
            (University of Turku, Finland).')

st.markdown('[<img src="https://raw.githubusercontent.com/sunpy/sunpy-logo/master/generated/sunpy_logo_landscape.svg"\
             height="30">](https://sunpy.org)$~~$powered', \
            unsafe_allow_html=True)
