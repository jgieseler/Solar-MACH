import base64
import datetime
import io

import astropy.units as u
import streamlit as st
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

from backmapping import *

# set page config
st.set_page_config(page_title='Solar-MACH', page_icon=":satellite:", 
                   initial_sidebar_state="expanded")

st.title('Solar-MACH')
st.markdown('## Multi-spacecraft longitudinal configuration plotter')

# provide date and time
with st.sidebar.beta_container():
    d = st.sidebar.date_input("Select date", datetime.date.today()-datetime.timedelta(days = 2))
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
        if reference_sys == 'Carrington':
            reference_long = st.slider('Longitude:', 0, 360, 20)
            reference_lat = st.slider('Latitude:', -180, 180, 0)
        if reference_sys == 'Stonyhurst':
            reference_long = st.slider('Longitude:', -180, 180, 20)
            reference_lat = st.slider('Latitude:', -180, 180, 0)
            # convert Stonyhurst coordinates to Carrington for further use:
            coord = SkyCoord(reference_long*u.deg, reference_lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=date)
            coord = coord.transform_to(frames.HeliographicCarrington(observer='Sun'))
            reference_long = coord.lon.value
            reference_lat = coord.lat.value
    if plot_reference is False:
        reference_long = None
        reference_lat = None

st.sidebar.subheader('Choose bodies/spacecraft and measured solar wind speeds')
with st.sidebar.beta_container():
    full_body_list = \
        st.sidebar.text_area('Bodies/spacecraft (scroll down for example list)',
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
    # ugly workaround to not show the index in the table: replace them with empty strings
    all_bodies.index = [""] * len(all_bodies)
    st.sidebar.table(all_bodies)

    st.sidebar.markdown('[Complete list of available bodies](https://ssd.jpl.nasa.gov/horizons.cgi?s_target=1#top)')

# initialize the bodies
c = HeliosphericConstellation(date, body_list, vsw_list, reference_long,
                              reference_lat)

# make the longitudinal constellation plot
plot_file = 'plot_'+datetime.datetime.combine(d, t).strftime("%Y-%m-%d_%H-%M-%S")+'.png'

c.plot(
    plot_spirals=plot_spirals,                            # plot Parker spirals for each body
    plot_sun_body_line=plot_sun_body_line,                # plot straight line between Sun and body
    show_earth_centered_coord=show_earth_centered_coord,  # display Earth-aligned coordinate system
    # outfile=plot_file                                     # output file (optional)
)

# download plot
plot2 = io.BytesIO()
plt.savefig(plot2, format='png', bbox_inches="tight")
plot2 = base64.b64encode(plot2.getvalue()).decode("utf-8").replace("\n", "")
st.markdown(f'<a href="data:file/png;base64,{plot2}" download="{plot_file}" target="_blank">Download figure as .png file</a>', unsafe_allow_html=True)

# display coordinates
st.dataframe(c.coord_table)

# download coordinates
csv = c.coord_table.to_csv().encode()
b64 = base64.b64encode(csv).decode()
filename = 'table_'+datetime.datetime.combine(d, t).strftime("%Y-%m-%d_%H-%M-%S")
st.markdown(f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" target="_blank">Download table as .csv file</a>', unsafe_allow_html=True)

# footer
st.markdown("""---""")
st.markdown('The *Solar MAgnetic Connection Haus* (Solar-MACH) tool is a \
            multi-spacecraft longitudinal configuration plotter. It was \
            originally developed at the University of Kiel, Germany, and further \
            discussed within the [ESA Heliophysics Archives USer (HAUS)]\
            (https://www.cosmos.esa.int/web/esdc/archives-user-groups/heliophysics) \
            group. It is now opened to everyone ([original code]\
            (https://github.com/esdc-esac-esa-int/Solar-MACH)).')

st.markdown('[Forked and modified](https://github.com/jgieseler/Solar-MACH) by \
            [J. Gieseler](https://jgieseler.github.io) \
            (University of Turku, Finland). [Get in contact](mailto:jan.gieseler@utu.fi?subject=Solar-MACH).')

st.markdown("""---""")
st.markdown('Powered by: \
            [<img src="https://matplotlib.org/stable/_static/logo2_compressed.svg" height="25">](https://matplotlib.org) \
            [<img src="https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg" height="30">](https://streamlit.io) \
            [<img src="https://raw.githubusercontent.com/sunpy/sunpy-logo/master/generated/sunpy_logo_landscape.svg" height="30">](https://sunpy.org)', \
            unsafe_allow_html=True)
