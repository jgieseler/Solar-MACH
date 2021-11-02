import base64
import datetime
import io
import json
import os
import pickle
import pyshorteners
import re
import uuid

import astropy.units as u
import pandas as pd
import streamlit as st
from astropy.coordinates import SkyCoord
from sunpy.coordinates import frames

from backmapping import *


# modify hamburger menu
about_info = ''' ## Solar-MACH 
The *Solar MAgnetic Connection Haus* tool is a multi-spacecraft longitudinal configuration plotter, originally developed at the University of Kiel, Germany, and further discussed within the ESA Heliophysics Archives USer (HAUS) group. Forked and modified by J. Gieseler (University of Turku, Finland).

The development of the online tool has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 101004159 (SERPENTINE).'''
get_help_link = "https://github.com/jgieseler/Solar-MACH/discussions"
report_bug_link = "https://github.com/jgieseler/Solar-MACH/discussions/4"
menu_items = {'About': about_info,
              'Get help': get_help_link, 
              'Report a bug': report_bug_link}

# set page config
st.set_page_config(page_title='Solar-MACH', page_icon=":satellite:", 
                   initial_sidebar_state="expanded",
                   menu_items=menu_items)

st.write(st.session_state)

st.info('Update (Oct 26, 2021): You can now save or share the status of a given configuration! Scroll down and get the full URL from the blue box at the bottom of the page.')

st.title('Solar-MACH')
st.markdown('## Multi-spacecraft longitudinal configuration plotter')


# Save parameters to URL for sharing and bookmarking
def make_url(set_query_params):
    st.experimental_set_query_params(**set_query_params)

# Clear parameters from URL bc. otherwise input becomes buggy as of Streamlit 
# version 1.0. Will hopefully be fixed in the future. Then hopefully all 
# occurences of "clear_url" can be removed.
def clear_url():
    st.experimental_set_query_params()

# Define Download button, from https://discuss.streamlit.io/t/a-download-button-with-custom-css/4220
def download_button(object_to_download, download_filename, button_text, pickle_it=False):
    """
    Generates a link to download the given object_to_download.

    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.

    Returns:
    -------
    (str): the anchor tag to download object_to_download

    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')

    """
    if pickle_it:
        try:
            object_to_download = pickle.dumps(object_to_download)
        except pickle.PicklingError as e:
            st.write(e)
            return None

    else:
        if isinstance(object_to_download, bytes):
            pass

        elif isinstance(object_to_download, pd.DataFrame):
            object_to_download = object_to_download.to_csv(index=False)

        # Try JSON encode for everything else
        else:
            object_to_download = json.dumps(object_to_download)

    try:
        # some strings <-> bytes conversions necessary here
        b64 = base64.b64encode(object_to_download.encode()).decode()

    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}             
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link

# obtain query paramamters from URL
query_params = st.experimental_get_query_params()

# define empty dict for new params to put into URL (only in box at the bottom)
set_query_params = {}

# saved obtained quety params from URL into session_state
for i in query_params:
    st.session_state[i] = query_params[i]

# removed as of now
# st.sidebar.button('Get shareable URL', help='Save parameters to URL, so that it can be saved or shared with others.', on_click=make_url, args=[set_query_params])

# provide date and time
with st.sidebar.container():
    # set starting parameters from URL if available, otherwise use defaults 
    # def_d = datetime.datetime.strptime(query_params["date"][0], "%Y%m%d") if "date" in query_params \
    #         else datetime.date.today()-datetime.timedelta(days = 2)
    # def_t = datetime.datetime.strptime(query_params["time"][0], "%H%M") if "time" in query_params \
    #         else datetime.time(0, 0)
    def_d = datetime.datetime.strptime(st.session_state["date"][0], "%Y%m%d") if "date" in st.session_state \
            else datetime.date.today()-datetime.timedelta(days = 2)
    def_t = datetime.datetime.strptime(st.session_state["time"][0], "%H%M") if "time" in st.session_state \
            else datetime.time(0, 0)
    d = st.sidebar.date_input("Select date", def_d) #, on_change=clear_url)
    t = st.sidebar.time_input('Select time', def_t) #, on_change=clear_url)
    date = datetime.datetime.combine(d, t).strftime("%Y-%m-%d %H:%M:%S")

    # save query parameters to URL
    sdate = d.strftime("%Y%m%d")
    stime = t.strftime("%H%M")
    set_query_params["date"] = [sdate]
    set_query_params["time"] = [stime]
    st.session_state["date"] = [sdate]
    st.session_state["time"] = [stime]


# plotting settings
with st.sidebar.container():
    st.sidebar.subheader('Plot options:')

    # if ("plot_spirals" in query_params) and int(query_params["plot_spirals"][0]) == 0:
    if ("plot_spirals" in st.session_state) and int(st.session_state["plot_spirals"][0]) == 0:
        def_plot_spirals = False    
    else:
        def_plot_spirals = True
    plot_spirals = st.sidebar.checkbox('Parker spiral for each body', value=def_plot_spirals) #, on_change=clear_url)
    if not plot_spirals:
        set_query_params["plot_spirals"] = [0]
        st.session_state["plot_spirals"] = [0]

    # if ("plot_sun_body_line" in query_params) and int(query_params["plot_sun_body_line"][0]) == 0:
    if ("plot_sun_body_line" in st.session_state) and int(st.session_state["plot_sun_body_line"][0]) == 0:
        def_plot_sun_body_line = False    
    else:
        def_plot_sun_body_line = True
    plot_sun_body_line = st.sidebar.checkbox('Straight line from Sun to body', value=def_plot_sun_body_line) #, on_change=clear_url)
    if not plot_sun_body_line:
        set_query_params["plot_sun_body_line"] = [0]
        st.session_state["plot_sun_body_line"] = [0]

    # if ("plot_ecc" in query_params) and int(query_params["plot_ecc"][0]) == 1:
    if ("plot_ecc" in st.session_state) and int(st.session_state["plot_ecc"][0]) == 1:
        def_show_earth_centered_coord = True    
    else:
        def_show_earth_centered_coord = False
    show_earth_centered_coord = st.sidebar.checkbox('Add Earth-aligned coord. system', value=def_show_earth_centered_coord) #, on_change=clear_url)
    if show_earth_centered_coord:
        set_query_params["plot_ecc"] = [1]
        st.session_state["plot_ecc"] = [1]

    # if ("plot_trans" in query_params) and int(query_params["plot_trans"][0]) == 1:
    if ("plot_trans" in st.session_state) and int(st.session_state["plot_trans"][0]) == 1:
        def_transparent = True    
    else:
        def_transparent = False
    transparent = st.sidebar.checkbox('Transparent background', value=def_transparent) #, on_change=clear_url)
    if transparent:
        set_query_params["plot_trans"] = [1]
        st.session_state["plot_trans"] = [1]

    if ("plot_nr" in st.session_state) and int(st.session_state["plot_nr"][0]) == 1:
        def_numbered = True    
    else:
        def_numbered = False
    numbered_markers = st.sidebar.checkbox('Numbered symbols', value=def_numbered) #, on_change=clear_url)
    if numbered_markers:
        set_query_params["plot_nr"] = [1]
        st.session_state["plot_nr"] = [1]

    # if ("plot_reference" in query_params) and int(query_params["plot_reference"][0]) == 1:
    if ("plot_reference" in st.session_state) and int(st.session_state["plot_reference"][0]) == 1:
        def_plot_reference = True
    else:
        def_plot_reference = False
  
    plot_reference = st.sidebar.checkbox('Plot reference (e.g. flare)', value=def_plot_reference) #, on_change=clear_url)

    with st.sidebar.expander("Reference coordinates (e.g. flare)", expanded=plot_reference):
        wrong_ref_coord = False
        reference_sys_list = ['Carrington', 'Stonyhurst']
        # set starting parameters from URL if available, otherwise use defaults
        # def_reference_sys = int(query_params["reference_sys"][0]) if "reference_sys" in query_params else 0
        def_reference_sys = int(st.session_state["reference_sys"][0]) if "reference_sys" in st.session_state else 0

        reference_sys = st.radio('Coordinate system:', reference_sys_list, index=def_reference_sys)

        if reference_sys == 'Carrington':
            # def_reference_long = int(query_params["carr_long"][0]) if "carr_long" in query_params else 20
            # def_reference_lat = int(query_params["carr_lat"][0]) if "carr_lat" in query_params else 0
            def_reference_long = int(st.session_state["carr_long"][0]) if "carr_long" in st.session_state else 20
            def_reference_lat = int(st.session_state["carr_lat"][0]) if "carr_lat" in st.session_state else 0
            reference_long = st.number_input('Longitude (0 to 360):', min_value=0, max_value=360, value=def_reference_long) #, on_change=clear_url)
            reference_lat  = st.number_input('Latitude (-90 to 90):', min_value=-90, max_value=90, value=def_reference_lat) #, on_change=clear_url)
            # outdated check for wrong coordinates (caught by using st.number_input)
            # if (reference_long < 0) or (reference_long > 360) or (reference_lat < -90) or (reference_lat > 90):
            #     wrong_ref_coord = True
            if plot_reference is True:
                set_query_params["carr_long"] = [str(int(reference_long))]
                set_query_params["carr_lat"] = [str(int(reference_lat))]
                st.session_state["carr_long"] = [str(int(reference_long))]
                st.session_state["carr_lat"] = [str(int(reference_lat))]

        if reference_sys == 'Stonyhurst':
            # def_reference_long = int(query_params["ston_long"][0]) if "ston_long" in query_params else 90
            # def_reference_lat = int(query_params["ston_lat"][0]) if "ston_lat" in query_params else 0
            def_reference_long = int(st.session_state["ston_long"][0]) if "ston_long" in st.session_state else 90
            def_reference_lat = int(st.session_state["ston_lat"][0]) if "ston_lat" in st.session_state else 0
            # convert query coordinates (always Carrington) to Stonyhurst for input widget:
            # coord = SkyCoord(def_reference_long*u.deg, def_reference_lat*u.deg, frame=frames.HeliographicCarrington(observer='Sun', obstime=date))
            # coord = coord.transform_to(frames.HeliographicStonyhurst)
            # def_reference_long = coord.lon.value
            # def_reference_lat = coord.lat.value
            
            # read in coordinates from user
            reference_long = st.number_input('Longitude (-180 to 180, integer):', min_value=-180, max_value=180, value=def_reference_long) #, on_change=clear_url)
            reference_lat  = st.number_input('Latitude (-90 to 90, integer):', min_value=-90, max_value=90, value=def_reference_lat) #, on_change=clear_url)
            # outdated check for wrong coordinates (caught by using st.number_input)
            # if (reference_long < -180) or (reference_long > 180) or (reference_lat < -90) or (reference_lat > 90):
            #     wrong_ref_coord = True
            if plot_reference is True:
                set_query_params["ston_long"] = [str(int(reference_long))]
                set_query_params["ston_lat"] = [str(int(reference_lat))]
                st.session_state["ston_long"] = [str(int(reference_long))]
                st.session_state["ston_lat"] = [str(int(reference_lat))]
        
        # outdated check for wrong coordinates (caught by using st.number_input)
        # if wrong_ref_coord:
        #         st.error('ERROR: There is something wrong in the prodived reference coordinates!')
        #         st.stop()

        if reference_sys == 'Stonyhurst':
            # convert Stonyhurst coordinates to Carrington for further use:
            coord = SkyCoord(reference_long*u.deg, reference_lat*u.deg, frame=frames.HeliographicStonyhurst, obstime=date)
            coord = coord.transform_to(frames.HeliographicCarrington(observer='Sun'))
            reference_long = coord.lon.value
            reference_lat = coord.lat.value

        import math
        # def_reference_vsw = int(query_params["reference_vsw"][0]) if "reference_vsw" in query_params else 400
        def_reference_vsw = int(st.session_state["reference_vsw"][0]) if "reference_vsw" in st.session_state else 400
        reference_vsw = st.number_input('Solar wind speed for reference (km/s)', min_value=0, value=def_reference_vsw, step=50) #, on_change=clear_url)

    if plot_reference is False:
        reference_long = None
        reference_lat = None

    # save query parameters to URL
    if plot_reference is True:
        set_query_params["reference_sys"] = [str(reference_sys_list.index(reference_sys))]
        set_query_params["reference_vsw"] = [str(int(reference_vsw))]
        set_query_params["plot_reference"] = [1]
        st.session_state["reference_sys"] = [str(reference_sys_list.index(reference_sys))]
        st.session_state["reference_vsw"] = [str(int(reference_vsw))]
        st.session_state["plot_reference"] = [1]


st.sidebar.subheader('Choose bodies/spacecraft and measured solar wind speeds')
with st.sidebar.container():
    all_bodies = print_body_list()

    # rename L1 point and order body list alphabetically
    all_bodies = all_bodies.replace('SEMB-L1', 'L1')
    all_bodies = all_bodies.sort_index()

    # set starting parameters from URL if available, otherwise use defaults 
    # def_full_body_list = query_params["bodies"] if "bodies" in query_params \
    #                         else ['STEREO A', 'Earth', 'BepiColombo', 'Parker Solar Probe', 'Solar Orbiter']
    # def_vsw_list = [int(i) for i in query_params["speeds"]] if "speeds" in query_params \
    #                         else [400, 400, 400, 400, 400]

    def_full_body_list = st.session_state["bodies"] if "bodies" in st.session_state \
                            else ['STEREO A', 'Earth', 'BepiColombo', 'Parker Solar Probe', 'Solar Orbiter']


    def_vsw_list = [int(i) for i in st.session_state["speeds"]] if "speeds" in st.session_state \
                            else [400, 400, 400, 400, 400]

    def_vsw_dict = {}
    for i in range(len(def_full_body_list)):
        try:
            def_vsw_dict[def_full_body_list[i]] = def_vsw_list[i]
        except IndexError: 
            def_vsw_dict[def_full_body_list[i]] = 400

    body_list = st.multiselect(
        'Bodies/spacecraft',
        all_bodies,
        def_full_body_list,
        key='bodies') #, on_change=clear_url)
    
    with st.sidebar.expander("Solar wind speed (kms/s) per S/C", expanded=True):
        vsw_dict = {}
        for body in body_list:
            vsw_dict[body] = int(st.number_input(body, min_value=0, 
                                 value=def_vsw_dict.get(body, 400), 
                                 step=50)) #, on_change=clear_url))
        vsw_list = [vsw_dict[body] for body in body_list]
    
    set_query_params["bodies"] = body_list
    set_query_params["speeds"] = vsw_list
    # st.session_state["bodies"] = body_list
    st.session_state["speeds"] = vsw_list

# url = 'http://localhost:8501/?'
url = 'https://share.streamlit.io/jgieseler/solar-mach/testing/app.py?'
for p in set_query_params:
    for i in set_query_params[p]:
        # st.write(str(p)+' '+str(i))
        url = url + str(p)+'='+str(i)+'&'
url = url.replace(' ', '+')

# possible alternative to using set_query_params dictionary:
# url2 = 'https://share.streamlit.io/jgieseler/solar-mach/testing/app.py?'
# for p in st.session_state:
#     for i in st.session_state[p]:
#         # st.write(str(p)+' '+str(i))
#         url2 = url2 + str(p)+'='+str(i)+'&'
# url2 = url2.replace(' ', '+')


if len(body_list) == len(vsw_list):
    # initialize the bodies
    c = HeliosphericConstellation(date, body_list, vsw_list, reference_long,
                                reference_lat)

    # make the longitudinal constellation plot
    plot_file = 'Solar-MACH_'+datetime.datetime.combine(d, t).strftime("%Y-%m-%d_%H-%M-%S")+'.png'

    c.plot(
        plot_spirals=plot_spirals,                            # plot Parker spirals for each body
        plot_sun_body_line=plot_sun_body_line,                # plot straight line between Sun and body
        show_earth_centered_coord=show_earth_centered_coord,  # display Earth-aligned coordinate system
        reference_vsw=reference_vsw,                          # define solar wind speed at reference
        transparent = transparent,
        numbered_markers = numbered_markers,
        # outfile=plot_file                                     # output file (optional)
    )

    # download plot
    filename = 'Solar-MACH_'+datetime.datetime.combine(d, t).strftime("%Y-%m-%d_%H-%M-%S")
    plot2 = io.BytesIO()
    plt.savefig(plot2, format='png', bbox_inches="tight")
    # plot3 = base64.b64encode(plot2.getvalue()).decode("utf-8").replace("\n", "")
    # st.markdown(f'<a href="data:file/png;base64,{plot3}" download="{plot_file}" target="_blank">Download figure as .png file</a>', unsafe_allow_html=True)
    download_button_str = download_button(plot2.getvalue(), filename+'.png', f'Download figure as .png file', pickle_it=False)
    st.markdown(download_button_str, unsafe_allow_html=True)

    # using new included download_button function (need to uncomment 
    # "#outfile=plot_file" above!)
    # with open(plot_file, 'rb') as f:
    #     st.download_button('Download file', f, file_name=plot_file)

    # display coordinates table
    df = c.coord_table
    df.index = df['Spacecraft/Body']
    df = df.drop(columns=['Spacecraft/Body'])
    df = df.rename(columns=
        {"Spacecraft/Body": "Spacecraft / body",
        "Carrington Longitude (°)": "Carrington longitude [°]",
        "Latitude (°)": "Carrington latitude [°]",
        "Heliocentric Distance (AU)": "Heliocent. distance [AU]",
        "Longitudinal separation to Earth's longitude": "Longitud. separation to Earth longitude [°]",
        "Latitudinal separation to Earth's latitude": "Latitud. separation to Earth latitude [°]", 
        "Vsw": "Solar wind speed [km/s]",
        "Magnetic footpoint longitude (Carrington)": "Magnetic footpoint Carrington longitude [°]",
        "Longitudinal separation between body and reference_long": "Longitud. separation bw. body & reference [°]",
        "Longitudinal separation between body's mangetic footpoint and reference_long": "Longitud. separation bw. body's magnetic footpoint & reference [°]",
        "Latitudinal separation between body and reference_lat": "Latitudinal separation bw. body & reference [°]"})
    
    df2 = df.copy()
    decimals = 0
    df = df.round({ "Carrington longitude [°]": decimals, 
                    "Carrington latitude [°]": decimals,
                    "Longitud. separation to Earth longitude [°]": decimals,
                    "Latitud. separation to Earth latitude [°]": decimals,
                    "Solar wind speed [km/s]": decimals,
                    "Magnetic footpoint Carrington longitude [°]": decimals,
                    "Longitud. separation bw. body & reference [°]": decimals,
                    "Longitud. separation bw. body's magnetic footpoint & reference [°]": decimals,
                    "Latitudinal separation bw. body & reference [°]": decimals
                    }).astype(np.int64).astype(str) #yes, convert to int64 first and then to str to get rid of ".0"
    df["Heliocent. distance [AU]"] = df2["Heliocent. distance [AU]"].round(2).astype(str)

    st.table(df.T)

    # download coordinates
    # filename = 'Solar-MACH_'+datetime.datetime.combine(d, t).strftime("%Y-%m-%d_%H-%M-%S")
    # csv = c.coord_table.to_csv().encode()
    # b64 = base64.b64encode(csv).decode()
    # st.markdown(f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" target="_blank">Download table as .csv file</a>', unsafe_allow_html=True)
    download_button_str = download_button(c.coord_table, filename+'.csv', f'Download table as .csv file', pickle_it=False)
    st.markdown(download_button_str, unsafe_allow_html=True)
else:
    st.error(f"ERROR: Number of elements in the bodies/spacecraft list \
               ({len(body_list)}) and solar wind speed list ({len(vsw_list)}) \
               don't match! Please verify that for each body there is a solar \
               wind speed provided!")



st.markdown('###### Save or share this setup by bookmarking or distributing the following URL:')

st.info(url)

cont1 = st.container()

# generate short da.gd URL
def get_short_url(url):
    s = pyshorteners.Shortener()
    surl = s.dagd.short(url)
    # cont1.write(surl)
    cont1.info(surl)

cont1.button('Generate short URL', on_click=get_short_url, args=[url])

# clear params from URL because Streamlit 1.0 still get some hickups when one 
# changes the params; it then gets confused with the params in the URL and the 
# one from the widgets.
clear_url()

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
             [J. Gieseler](https://jgieseler.github.io) (University of Turku, Finland). \
             [**Get in contact**](mailto:jan.gieseler@utu.fi?subject=Solar-MACH).')

col1, col2 = st.columns((5,1))
col1.markdown("The development of the online tool has received funding from the \
             European Union's Horizon 2020 research and innovation programme \
             under grant agreement No 101004159 (SERPENTINE).")
col2.markdown('[<img src="https://serpentine-h2020.eu/wp-content/uploads/2021/02/SERPENTINE_logo_new.png" \
                height="80">](https://serpentine-h2020.eu)', unsafe_allow_html=True)

st.markdown('Powered by: \
            [<img src="https://matplotlib.org/stable/_static/logo2_compressed.svg" height="25">](https://matplotlib.org) \
            [<img src="https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg" height="30">](https://streamlit.io) \
            [<img src="https://raw.githubusercontent.com/sunpy/sunpy-logo/master/generated/sunpy_logo_landscape.svg" height="30">](https://sunpy.org)', \
            unsafe_allow_html=True)


# remove 'Made with Streamlit' footer
#MainMenu {visibility: hidden;}
hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
