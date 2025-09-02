import datetime
import io
import os
import pyshorteners
# import astropy.units as u
import matplotlib.pyplot as plt
# import numpy as np
from stqdm import stqdm
import streamlit as st
# import streamlit_analytics  # TODO: un-comment when streamlit-analytics has been updated with https://github.com/jrieke/streamlit-analytics/pull/44
# import streamlit_analytics2 as streamlit_analytics
# from astropy.coordinates import SkyCoord
# from sunpy.coordinates import frames
from solarmach import SolarMACH, print_body_list, get_sw_speed, calculate_pfss_solution, get_gong_map
from streamlit_scroll_navigation import scroll_navbar


def delete_from_state(vars):
    for var in vars:
        if var in st.session_state:
            del st.session_state[var]


# modify hamburger menu
about_info = '''
The *Solar MAgnetic Connection Haus* (**Solar-MACH**) tool is a multi-spacecraft longitudinal configuration plotter. It was originally developed at the University of Kiel, Germany, and further discussed within the ESA Heliophysics Archives USer (HAUS) group. Development takes now place at the University of Turku, Finland.

'''
get_help_link = "https://github.com/jgieseler/Solar-MACH/discussions"
report_bug_link = "https://github.com/jgieseler/Solar-MACH/discussions/4"
menu_items = {'About': about_info,
              'Get help': get_help_link,
              'Report a bug': report_bug_link}

# set page config - must be the first Streamlit command in the app
st.set_page_config(page_title='Solar-MACH', page_icon=":satellite:",
                   initial_sidebar_state="expanded",
                   menu_items=menu_items)

st.title('Solar-MACH')
st.header('Multi-spacecraft configuration plotter', anchor='classic')

# TODO: This doesn't seem to work anymore with streamlit version 1.28.1
st.markdown(" <style> div[class^='st-emotion-cache-10oheav'] { padding-top: 0.0rem; } </style> ", unsafe_allow_html=True)

# Inject custom CSS to set the width of the sidebar
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 350px !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# st.success("⬇️ **Scroll down for new 3d view and PFSS extension (both BETA)!** ⬇️")

# st.error("**2025-01-10: Due to a wildfire near JPL, Solar-MACH outages may occur.**", icon="⚠️")

scroll_navbar(
        ['classic', '3d', 'PFSS'],
        key="navbar",
        anchor_labels=["Classic view", "3d view (BETA)", "PFSS extension (BETA)"],
        orientation="horizontal",
        override_styles={
                        "navbarButtonBase": {"backgroundColor": "#ff4b4b",  # Set a custom button background color
                                            "color": "#ffffff",  # Set custom text color
                                            "border-radius": "5px",
                                            "padding-top": "8px",
                                            },
                        "navbarButtonHover": {"backgroundColor": "#ae3434",  # Set a custom hover color for the buttons
                                            },
                        "navbarButtonActive": {"backgroundColor": "#ff4b4b",  # 922c2b. Set a custom color for the active buttons
                                            },
                        "navigationBarBase": {"backgroundColor": "#f8f9fa",  # Change the navigation bar background color
                                            "height": "60px",
                                            },                      
                        },
        auto_update_anchor=True,
        )

# st.info("""
#        📢 **Update November 2022** 📢
#        * [Solar-MACH paper available](https://doi.org/10.3389/fspas.2022.1058810). Please cite this if you use Solar-MACH!
#        * Added option to change between Carrington and Stonyhurst coordinates for the whole tool (deprecates overplotting of Earth-centered coordinate system)
#        * Added option to change Earth position in the plot
#        * Take into account solar differential rotation wrt. latitude (see [#21](https://github.com/jgieseler/solarmach/issues/21))
#        * Instead of spherical radius, plot its projection to the heliographic equatorial plane (see [#3](https://github.com/jgieseler/solarmach/issues/3))
#        """)


# Save parameters to URL for sharing and bookmarking
# def make_url(set_query_params):
#     st.query_params(**set_query_params)


def clear_url():
    """
    Clear parameters from URL bc. otherwise input becomes buggy as of Streamlit
    version 1.0. Will hopefully be fixed in the future. Then hopefully all
    occurences of "clear_url" can be removed.
    """
    st.query_params.clear()
    st.query_params["embedded"] = 'true'


# @st.cache_data
def obtain_vsw(body_list, date, default_vsw):
    vsw_list2 = []
    obtained_vsw = {}  #[]
    for i, body in stqdm(enumerate(body_list), desc="Obtaining solar wind speeds for selected bodies..."):
        vsw = get_sw_speed(body, date, default_vsw=default_vsw[i])
        vsw_list2.append(vsw)
        if vsw==default_vsw[i]:
            # obtained_vsw.append(-1)
            obtained_vsw[body] = -1
        else:
            # obtained_vsw.append(1)
            obtained_vsw[body] = 1
    st.session_state["obtained_vsw"] = obtained_vsw
    st.session_state["speeds"] = vsw_list2


@st.fragment
def download_table_button():
    st.download_button(
        label="Download table as .csv file",
        data=c.coord_table.to_csv(index=False),
        file_name=filename+'.csv',
        on_click='ignore',
        mime='text/csv')

def reset_vsw(body_list):
    delete_from_state(["obtained_vsw"])
    st.session_state["speeds"] = [400] * len(body_list)


@st.cache_data
def get_gong_map_cached(time, filepath=None):
    return get_gong_map(time, filepath=filepath)


@st.fragment
def show_classic_plots():
    """
    Generates and displays classic 2D and 3D plots using the provided
    configuration from Streamlit session state and provides options to download
    them in a way that won't cause the app to re-run.
    """
    c.plot(
        plot_spirals=st.session_state.def_plot_spirals,                            # plot Parker spirals for each body
        plot_sun_body_line=st.session_state.def_plot_sun_body_line,                # plot straight line between Sun and body
        reference_vsw=st.session_state.def_reference_vsw,                          # define solar wind speed at reference
        transparent=st.session_state.def_transparent,
        # numbered_markers=st.session_state.def_numbered,
        markers=markers,
        long_offset=st.session_state.def_long_offset,
        # outfile=filename+'.png'                               # output file (optional)
    )

    # download plot
    plot2 = io.BytesIO()
    plt.savefig(plot2, format='png', bbox_inches="tight")
    st.download_button(
        label="Download figure as .png file",
        data=plot2.getvalue(),
        file_name=filename+'.png',
        on_click='ignore',
        mime="image/png")

    # download plot, alternative. produces actual png image on server.
    # needs # outfile=filename+'.png' uncommented above
    # with open(filename+'.png', 'rb') as f:
    #     st.download_button('Download figure as .png file', f, file_name=filename+'.png', mime="image/png")

    # load 3d plot
    st.subheader("**:red[3d view (BETA)]**", anchor='3d')
    st.error('''
             Be aware that the 3d view is still in beta stage! Please give us feedback through [GitHub issues](https://github.com/jgieseler/solarmach/issues) or by sending an [e-mail](mailto:jan.gieseler@utu.fi?subject=Solar-MACH).
    
             Note that at the moment saving the figure will always provide the *default* view of it (see [#35](https://github.com/jgieseler/Solar-MACH/issues/35) for details). If you want to save a custom view, you need to make a screenshot.
             ''')
    c.plot_3d(plot_spirals=st.session_state.def_plot_spirals,
              plot_sun_body_line=st.session_state.def_plot_sun_body_line,
              markers=markers,
              reference_vsw=st.session_state.def_reference_vsw,
              plot_equatorial_plane=st.session_state.def_plot_equatorial_plane,
              plot_3d_grid=st.session_state.def_plot_3d_grid,
              plot_vertical_line=st.session_state.def_plot_vertical_line,
              )
    st.caption('Sun not to scale. Hover over plot and click on 📷 in the top right to save the plot.')
    #
    return


@st.fragment
def show_pfss_plots():
    """
    Generates and displays PFSS plots and provides options to download them in
    a way that won't cause the app to re-run.
    """
    c.plot_pfss(rss=rss,
                pfss_solution=pfss_solution,
                vary=vary,
                n_varies=n_varies,
                long_offset=st.session_state.def_long_offset,
                reference_vsw=st.session_state.def_reference_vsw,
                markers=markers,
                plot_spirals=True,  # st.session_state.def_plot_spirals - crashes for False
                figsize=(12, 8),
                dpi=200,
                # outfile=pfss_filename+'.png'
                )
    # download plot
    plot2 = io.BytesIO()
    plt.savefig(plot2, format='png', bbox_inches="tight")
    st.download_button(
        label="Download figure as .png file",
        data=plot2.getvalue(),
        file_name=filename+'_PFSS'+'.png',
        on_click='ignore',
        mime="image/png")

    st.write("The following two plots show the same content, just at different default zoom levels:")

    # load 3d plot
    c.pfss_3d(color_code="object", rss=rss,
                plot_spirals=st.session_state.def_plot_spirals,
                plot_sun_body_line=st.session_state.def_plot_sun_body_line,
                markers=markers,
                reference_vsw=st.session_state.def_reference_vsw,
                plot_equatorial_plane=st.session_state.def_plot_equatorial_plane,
                plot_3d_grid=st.session_state.def_plot_3d_grid,
                plot_vertical_line=st.session_state.def_plot_vertical_line,
                zoom_out=False)
    c.pfss_3d(color_code="object", rss=rss,
                plot_spirals=st.session_state.def_plot_spirals,
                plot_sun_body_line=st.session_state.def_plot_sun_body_line,
                markers=markers,
                reference_vsw=st.session_state.def_reference_vsw,
                plot_equatorial_plane=st.session_state.def_plot_equatorial_plane,
                plot_3d_grid=st.session_state.def_plot_3d_grid,
                plot_vertical_line=st.session_state.def_plot_vertical_line,
                zoom_out=True)
    st.caption('Hover over plot and click on 📷 in the top right to save the plot.')
    #
    return


# obtain query paramamters from URL; convert query dictionary to old format
query_params = {}
for key in st.query_params.keys():
    query_params[key] = st.query_params.get_all(key)


# define empty dict for new params to put into URL (only in box at the bottom)
set_query_params = {}

# catch old URL parameters and replace with current ones
if ("plot_reference" in query_params) and int(query_params["plot_reference"][0]) == 1:
    if "carr_long" in query_params and "carr_lat" in query_params and "reference_sys" in query_params and "coord_sys" not in query_params and int(query_params["reference_sys"][0]) == 0:
        query_params["reference_long"] = query_params.pop("carr_long")
        query_params["reference_lat"] = query_params.pop("carr_lat")
        query_params["coord_sys"] = query_params.pop("reference_sys")
        # query_params["coord_sys"] = ["0"]  # select Carrington coordinates
    elif "ston_long" in query_params and "ston_lat" in query_params and "reference_sys" in query_params and "coord_sys" not in query_params and int(query_params["reference_sys"][0]) == 1:
        query_params["reference_long"] = query_params.pop("ston_long")
        query_params["reference_lat"] = query_params.pop("ston_lat")
        query_params["coord_sys"] = query_params.pop("reference_sys")
        # query_params["coord_sys"] = ["1"]  # select Stonyhurst coordinates
    else:
        if "carr_long" in query_params or "carr_lat" in query_params or "ston_long" in query_params or "ston_lat" in query_params or "reference_sys" in query_params:
            st.error('⚠️ **WARNING:** Deprecated parameters have been prodived by the URL. To avoid unexpected behaviour, plotting of the reference has been deactivated!')
            query_params["plot_reference"][0] = 0

# saved obtained query params from URL into session_state
for i in query_params:
    st.session_state[i] = query_params[i]

# removed as of now
# st.sidebar.button('Get shareable URL', help='Save parameters to URL, so that it can be saved or shared with others.', on_click=make_url, args=[set_query_params])

# provide date and time
# set starting parameters from URL if available, otherwise use defaults
if "date" in query_params:
    st.session_state.date_input = datetime.datetime.strptime(query_params["date"][0], "%Y%m%d")
st.sidebar.date_input("Select date", value=datetime.date.today()-datetime.timedelta(days=2), min_value=datetime.date(1970, 1, 1), key="date_input")

if "time" in query_params:
    st.session_state.time_input = datetime.datetime.strptime(query_params["time"][0], "%H%M").time()
st.sidebar.time_input('Select time', value=datetime.time(0, 0), key="time_input")

date = datetime.datetime.combine(st.session_state.date_input, st.session_state.time_input).strftime("%Y-%m-%d %H:%M:%S")

# save query parameters to URL
sdate = st.session_state.date_input.strftime("%Y%m%d")
stime = st.session_state.time_input.strftime("%H%M")

# if changing datetime, remove obtained_vsw from session_state (bc. new vsw need to be obtained for changed datetime)
if "date" in st.session_state.keys():
    if st.session_state["date"] != [sdate]: 
        delete_from_state(["obtained_vsw"])
if "time" in st.session_state.keys():
    if st.session_state["time"] != [stime]: 
        delete_from_state(["obtained_vsw"])

st.session_state["date"] = [sdate]
st.session_state["time"] = [stime]


# plotting settings
with st.sidebar.container():
    coord_sys_list = ['Carrington', 'Stonyhurst']
    # set starting parameters from URL if available, otherwise use defaults
    # def_reference_sys = int(query_params["reference_sys"][0]) if "reference_sys" in query_params else 0
    def_coord_sys = int(st.session_state["coord_sys"][0]) if "coord_sys" in st.session_state else 0
    coord_sys = st.sidebar.radio('Coordinate system:', coord_sys_list, index=def_coord_sys, horizontal=True)
    st.session_state["coord_sys"] = [str(coord_sys_list.index(coord_sys))]

    st.sidebar.subheader('Plot options:')

    if ("plot_spirals" in query_params) and int(query_params["plot_spirals"][0]) == 0:
        st.session_state.def_plot_spirals = False
    st.sidebar.checkbox('Parker spiral for each body', value=True, key='def_plot_spirals')  # , on_change=clear_url)
    st.session_state["plot_spirals"] = [1] if st.session_state.def_plot_spirals else [0]

    if ("plot_sun_body_line" in query_params) and int(query_params["plot_sun_body_line"][0]) == 0:
        st.session_state.def_plot_sun_body_line = False
    st.sidebar.checkbox('Straight line from Sun to body', value=True, key='def_plot_sun_body_line')  # , on_change=clear_url)
    st.session_state["plot_sun_body_line"] = [1] if st.session_state.def_plot_sun_body_line else [0]

    # # if ("plot_ecc" in query_params) and int(query_params["plot_ecc"][0]) == 1:
    # if ("plot_ecc" in st.session_state) and int(st.session_state["plot_ecc"][0]) == 1:
    #     def_show_earth_centered_coord = True
    # else:
    #     def_show_earth_centered_coord = False
    # show_earth_centered_coord = st.sidebar.checkbox('Add Stonyhurst coord. system', value=def_show_earth_centered_coord)  # , on_change=clear_url)
    # if show_earth_centered_coord:
    #     set_query_params["plot_ecc"] = [1]
    #     st.session_state["plot_ecc"] = [1]

    if ("plot_trans" in query_params) and int(query_params["plot_trans"][0]) == 1:
        st.session_state.def_transparent = True
    st.sidebar.checkbox('Transparent background', value=False, key='def_transparent')  # , on_change=clear_url)
    st.session_state["plot_trans"] = [1] if st.session_state.def_transparent else [0]

    # catch old URL query parameter plot_nr for numberd_markers:
    if ("plot_nr" in query_params) and int(query_params["plot_nr"][0]) == 1:
        st.session_state.def_markers = "Numbers"
    if ("plot_nr" in query_params) and int(query_params["plot_nr"][0]) == 0:
        st.session_state.def_markers = "Squares"
    #
    if ("plot_markers" in query_params):
        st.session_state.def_markers = st.session_state.plot_markers[0].capitalize()
    # st.sidebar.checkbox('Numbered symbols', value=False, key='def_numbered')
    st.sidebar.radio("Plot symbol style", ["Letters", "Numbers", "Squares"], index=1, key='def_markers', horizontal=True)
    # st.session_state["plot_nr"] = [1] if st.session_state.def_numbered else [0]
    st.session_state["plot_markers"] = [st.session_state.def_markers]

    if ("plot_eq" in query_params) and int(query_params["plot_eq"][0]) == 1:
        st.session_state.def_plot_equatorial_plane = True
    st.sidebar.checkbox(':red[Equatorial plane (only 3d plot)]', value=True, key='def_plot_equatorial_plane')  # , on_change=clear_url)
    st.session_state["plot_eq"] = [1] if st.session_state.def_plot_equatorial_plane else [0]

    if ("plot_3d_axis" in query_params) and int(query_params["plot_3d_axis"][0]) == 1:
        st.session_state.def_plot_3d_grid = True
    st.sidebar.checkbox(':red[x, y, z axis & grid (only 3d plot)]', value=True, key='def_plot_3d_grid')  # , on_change=clear_url)
    st.session_state["plot_3d_axis"] = [1] if st.session_state.def_plot_3d_grid else [0]

    if ("plot_vertical_line" in query_params) and int(query_params["plot_vertical_line"][0]) == 1:
        st.session_state.def_plot_vertical_line = True
    st.sidebar.checkbox(':red[Vertical line from eq. plane to body (only 3d plot)]', value=False, key='def_plot_vertical_line')  # , on_change=clear_url)
    st.session_state["plot_vertical_line"] = [1] if st.session_state.def_plot_vertical_line else [0]

    if ("long_offset" in query_params):
        st.session_state.def_long_offset = int(st.session_state["long_offset"][0])
    st.sidebar.number_input('Plot Earth at longitude (axis system, 0=3 o`clock):',
                            min_value=0, max_value=360, value=270, step=90, key='def_long_offset')
    st.session_state["long_offset"] = [str(int(st.session_state.def_long_offset))]

    if ("plot_reference" in query_params) and int(query_params["plot_reference"][0]) == 1:
        st.session_state.plot_reference_check = True
    st.sidebar.checkbox('Plot reference (e.g. flare)', value=False, key='plot_reference_check')  # , on_change=clear_url)

    with st.sidebar.expander("Reference coordinates (e.g. flare)", expanded=st.session_state.plot_reference_check):
        wrong_ref_coord = False
        # reference_sys_list = ['Carrington', 'Stonyhurst']
        # # set starting parameters from URL if available, otherwise use defaults
        # # def_reference_sys = int(query_params["reference_sys"][0]) if "reference_sys" in query_params else 0
        # def_reference_sys = int(st.session_state["reference_sys"][0]) if "reference_sys" in st.session_state else 0
        # reference_sys = st.radio('Coordinate system:', reference_sys_list, index=def_reference_sys)

        def_reference_long = int(st.session_state["reference_long"][0]) if "reference_long" in st.session_state else 90
        def_reference_lat = int(st.session_state["reference_lat"][0]) if "reference_lat" in st.session_state else 0

        # read in coordinates from user
        if coord_sys == 'Carrington':
            reference_long = st.number_input('Longitude (0 to 360):', min_value=0, max_value=360, value=def_reference_long)  # , on_change=clear_url)
            reference_lat = st.number_input('Latitude (-90 to 90):', min_value=-90, max_value=90, value=def_reference_lat)  # , on_change=clear_url)
        elif coord_sys == 'Stonyhurst':
            reference_long = st.number_input('Longitude (-180 to 180, integer):', min_value=-180, max_value=180, value=def_reference_long)  # , on_change=clear_url)
            reference_lat = st.number_input('Latitude (-90 to 90, integer):', min_value=-90, max_value=90, value=def_reference_lat)  # , on_change=clear_url)

        if ("reference_vsw" in query_params):
            st.session_state.def_reference_vsw = int(query_params["reference_vsw"][0])
        st.number_input('Solar wind speed for reference (km/s)', min_value=0, value=400, step=50, key='def_reference_vsw')  # , on_change=clear_url)

        if st.session_state.plot_reference_check:
            st.session_state["reference_long"] = [str(int(reference_long))]
            st.session_state["reference_lat"] = [str(int(reference_lat))]
            st.session_state["reference_vsw"] = [str(int(st.session_state.def_reference_vsw))]
            st.session_state["plot_reference"] = [1]
        else:
            delete_from_state(["reference_long", "reference_lat", "reference_vsw", "plot_reference"])
            reference_long = None
            reference_lat = None


st.sidebar.subheader('Choose bodies/spacecraft and measured solar wind speeds')
with st.sidebar.container():
    all_bodies = print_body_list()

    # rename Lx point and order body list alphabetically
    for l in ['1', '2', '4', '5']:
        all_bodies = all_bodies.replace(f'SEMB-L{l}', f'L{l}')
    all_bodies = all_bodies.sort_index()

    # set starting parameters from URL if available, otherwise use defaults
    # def_full_body_list = query_params["bodies"] if "bodies" in query_params else ['STEREO A', 'Earth', 'BepiColombo', 'Parker Solar Probe', 'Solar Orbiter']
    # def_vsw_list = [int(i) for i in query_params["speeds"]] if "speeds" in query_params else [400, 400, 400, 400, 400]

    def_full_body_list = st.session_state["bodies"] if "bodies" in st.session_state else ['STEREO A', 'Earth', 'BepiColombo', 'Parker Solar Probe', 'Solar Orbiter']
    def_vsw_list = [int(i) for i in st.session_state["speeds"]] if "speeds" in st.session_state else [400, 400, 400, 400, 400]

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
        key='bodies')  # , on_change=clear_url)

    with st.sidebar.expander("Solar wind speed (km/s) per S/C", expanded=True):
        vsw_dict = {}
        st.button("Try to obtain measurements* :mag:", on_click=obtain_vsw, args=[body_list, date, def_vsw_list], type='primary')
        st.caption(r'\* Some data is preliminary browse data!')
        for i, body in enumerate(body_list):
            if "obtained_vsw" in st.session_state:
                if st.session_state["obtained_vsw"][body]==-1:
                    obtained_vsw_status = '  ❌'
                if st.session_state["obtained_vsw"][body]==1:
                    obtained_vsw_status = '  ✅'
            else:
                obtained_vsw_status = ''    
            vsw_dict[body] = int(st.number_input(body+obtained_vsw_status, min_value=0,
                                 value=def_vsw_dict.get(body, 400),
                                 step=50))  # , on_change=clear_url))
        if "obtained_vsw" in st.session_state:
            legend = '''✅ - measurement found
❌ - no measurement found'''
            st.code(legend, language=None)
        st.button("Reset all speeds to 400 km/s", on_click=reset_vsw, args=[body_list], type='primary')
        vsw_list = [vsw_dict[body] for body in body_list]

    # st.session_state["bodies"] = body_list
    st.session_state["speeds"] = vsw_list

url = 'https://solar-mach-pfss.streamlit.app/?embedded=true&'

# Get all the parameters from st.session_state and store them in set_query_params so you can build the url
for p in ["date", "time", "coord_sys", "plot_spirals", "plot_sun_body_line", "plot_trans", "plot_markers",
          "long_offset", "reference_long", "reference_lat", "reference_vsw", "plot_reference", "bodies", "speeds"]:
    if p in st.session_state:
        set_query_params[p] = st.session_state[p]

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
    c = SolarMACH(date, body_list, vsw_list, reference_long, reference_lat, coord_sys)

    # make the longitudinal constellation plot
    filename = 'Solar-MACH_'+datetime.datetime.combine(st.session_state.date_input, st.session_state.time_input).strftime("%Y-%m-%d_%H-%M")

    if st.session_state.def_markers.lower()=='squares':
        markers=False
        # markers_pfss_3d=False
    else:
        markers=st.session_state.def_markers.lower()
        # markers_pfss_3d=st.session_state.def_markers.lower()

    # call the classic Solar-MACH plots and download button here with a fragment function so that the app won't re-run while interacting
    show_classic_plots()

    st.success('''
           📄 **Citation:** Please cite the following paper if you use Solar-MACH in your publication.

           Gieseler, J., Dresing, N., Palmroos, C., von Forstner, J.L.F., Price, D.J., Vainio, R. et al. (2022).
           Solar-MACH: An open-source tool to analyze solar magnetic connection configurations. *Front. Astronomy Space Sci.* 9.
           [doi:10.3389/fspas.2022.1058810](https://doi.org/10.3389/fspas.2022.1058810)
           ''')

    # display coordinates table
    df = c.coord_table
    df.index = df['Spacecraft/Body']
    df = df.drop(columns=['Spacecraft/Body'])
    df = df.rename(columns={"Spacecraft/Body": "Spacecraft / body",
                            f"{coord_sys} longitude (°)": f"{coord_sys} longitude [°]",
                            f"{coord_sys} latitude (°)": f"{coord_sys} latitude [°]",
                            "Heliocentric distance (AU)": "Heliocent. distance [AU]",
                            "Longitudinal separation to Earth's longitude": "Longitud. separation to Earth longitude [°]",
                            "Latitudinal separation to Earth's latitude": "Latitud. separation to Earth latitude [°]",
                            "Vsw": "Solar wind speed [km/s]",
                            f"Magnetic footpoint longitude ({coord_sys})": f"Magnetic footpoint {coord_sys} longitude [°]",
                            "Longitudinal separation between body and reference_long": "Longitud. separation bw. body & reference [°]",
                            "Longitudinal separation between body's magnetic footpoint and reference_long": "Longitud. separation bw. body's magnetic footpoint & reference [°]",
                            "Latitudinal separation between body and reference_lat": "Latitudinal separation bw. body & reference [°]"})

    df2 = df.copy()
    decimals = 1
    df = df.round({f"{coord_sys} longitude [°]": decimals,
                   f"{coord_sys} latitude [°]": decimals,
                   "Longitud. separation to Earth longitude [°]": decimals,
                   "Latitud. separation to Earth latitude [°]": decimals,
                   "Solar wind speed [km/s]": decimals,
                   f"Magnetic footpoint {coord_sys} longitude [°]": decimals,
                   "Longitud. separation bw. body & reference [°]": decimals,
                   "Longitud. separation bw. body's magnetic footpoint & reference [°]": decimals,
                   "Latitudinal separation bw. body & reference [°]": decimals
                   }).astype(str)
    #               }).astype(np.int64).astype(str)  # yes, convert to int64 first and then to str to get rid of ".0" if using decimals=0
    df["Heliocent. distance [AU]"] = df2["Heliocent. distance [AU]"].round(2).astype(str)

    st.table(df.T)

    # download coordinates
    download_table_button()
else:
    st.error(f"ERROR: Number of elements in the bodies/spacecraft list \
               ({len(body_list)}) and solar wind speed list ({len(vsw_list)}) \
               don't match! Please verify that for each body there is a solar \
               wind speed provided!")


# st.markdown("""---""")
# experimental PFSS extension
# with st.expander(":red[**PFSS extension (experimental)**]", expanded=True):
with st.container():
    st.header("**:red[PFSS extension (BETA)]**", divider='grey', anchor='PFSS')
    st.error('''
             Be aware that the PFSS extension is still in beta stage! Please give us feedback through [GitHub issues](https://github.com/jgieseler/solarmach/issues) or by sending an [e-mail](mailto:jan.gieseler@utu.fi?subject=Solar-MACH).
    
             Note that at the moment saving a 3d figure will always provide the *default* view of it (see [#35](https://github.com/jgieseler/Solar-MACH/issues/35) for details). If you want to save a custom view, you need to make a screenshot.
             ''')


    form = st.form("PFSS_form")
    # form.write("If you change any parameter (here or on the left), you have to re-run the PFSS analysis (though it should be faster after the initial run)!")
    form.caption('If you change any parameter (here or on the left), you have to re-run the PFSS analysis (though it should be faster after the initial run)! Note that for the semi-logarithmic PFSS plot _Parker spirals_ will always be plotted and _straight lines from Sun to body_ never.')
    # Set the height of the source surface as a boundary condition for pfss extrapolation
    col1, col2 = form.columns((3, 1))
    col1.write('Set source surface height (in solar radii):')
    rss = col2.number_input('Set source surface height (in solar radii)', value=2.5, min_value=0.99, step=0.1, label_visibility='collapsed')
    col1, col2 = form.columns((3, 1))
    col1.write('Track down a flux tube instead of a single field line:')
    vary = col2.checkbox('vary', value=False, label_visibility="collapsed")
    col1, col2 = form.columns((3, 1))
    col1.write('Thickness of flux tube (n * 0.03 rad * height_of_ss):')
    n_varies = col2.number_input('n_varies', value=1, step=1, label_visibility='collapsed')

    run_pfss = form.form_submit_button('Start PFSS', type='primary')

    if run_pfss:
        with st.spinner('Running PFSS analysis, please wait...', show_time=True):
            try:
                # gong_map = get_gong_map(time=date, filepath=None)
                gong_map = get_gong_map_cached(time=date, filepath=None)
                st.toast('GONG map obtained.')

                # Calculate the potential field source surface solution
                pfss_solution = calculate_pfss_solution(gong_map=gong_map, rss=rss, coord_sys=coord_sys)
                st.toast('PFSS solution calculated.')

                # call the PFSS plots and download button here with a fragment function so that the app won't re-run while interacting
                show_pfss_plots()

            except IndexError:
                st.warning("Couldn't obtain input GONG map. Probably too recent (or old) date selected.", icon="⚠️")
            # import plotly.graph_objects as go
            # st.plotly_chart(go.Figure(data=[c.pfss_3d(color_code="object")]))


st.markdown("""---""")

st.markdown('###### Save or share this setup by bookmarking or distributing the following URL:')

st.info(url)

with st.expander("⚠️ **The URL format has changed in July 2022 and again in June 2023. Click here for more info.**", expanded=False):
    st.markdown('''
           * Because of changes to Streamlit, the URL format has changed in July 2022 and in June 2023.
           * If you still have old URLs, you can update them by replacing one of the following 
             ```
             https://share.streamlit.io/jgieseler/solar-mach?

             https://solar-mach.streamlitapp.com/?embedded=true&
             ```
             with 
             ```
             https://solar-mach.streamlit.app/?embedded=true&
             ```
           * In order to update a short URL that has been generated in the past, first get the full URL by adding `/coshorten` to it, e.g., `https://da.gd/B95XM` ⇒ `https://da.gd/coshorten/B95XM`. After that, you can update the URL like above.
           ''')

@st.fragment
def short_url_button(url):
    def get_short_url(url):
        """
        generate short da.gd URL
        """
        s = pyshorteners.Shortener()
        surl = s.dagd.short(url)
        # cont1.write(surl)
        cont1.success(surl)
    cont1 = st.container()
    cont1.button('Generate short URL', on_click=get_short_url, args=[url])


short_url_button(url=url)

# streamlit_analytics.start_tracking()  # TODO: un-comment when streamlit-analytics has been updated with https://github.com/jrieke/streamlit-analytics/pull/44


# footer
st.markdown("""---""")

st.markdown('The *Solar MAgnetic Connection Haus* (Solar-MACH) tool is a multi-spacecraft longitudinal configuration \
            plotter. It was originally developed at the University of Kiel, Germany, and further discussed within the \
            [ESA Heliophysics Archives USer (HAUS)](https://www.cosmos.esa.int/web/esdc/archives-user-groups/heliophysics) \
            group. Development takes now place at the University of Turku, Finland.')

st.markdown('For the full python package of Solar-MACH, refer to **solarmach**:<br>\
             [<img src="https://img.shields.io/static/v1?label=GitHub&message=solarmach&color=blue&logo=github" height="20">](https://github.com/jgieseler/solarmach/) \
             [<img src="https://img.shields.io/pypi/v/solarmach?style=flat&logo=pypi" height="20">](https://pypi.org/project/solarmach/) \
             [<img src="https://img.shields.io/conda/vn/conda-forge/solarmach?style=flat&logo=anaconda" height="20">](https://anaconda.org/conda-forge/solarmach/)', unsafe_allow_html=True)

st.markdown('For the Streamlit interface to the python package, refer to **Solar-MACH**:<br> \
             [<img src="https://img.shields.io/static/v1?label=GitHub&message=Solar-MACH&color=blue&logo=github" height="20">](https://github.com/jgieseler/Solar-MACH/) \
             [<img src="https://img.shields.io/static/v1?label=Contact&message=jan.gieseler@utu.fi&color=red&logo=gmail" height="20">](mailto:jan.gieseler@utu.fi?subject=Solar-MACH)', unsafe_allow_html=True)

col1, col2 = st.columns((5, 1))
col1.markdown("*The development of the online tool has received funding from the European Union's Horizon 2020 \
              research and innovation programme under grant agreement No 101004159 (SERPENTINE).*")
col2.markdown('[<img src="https://serpentine-h2020.eu/wp-content/uploads/2021/02/SERPENTINE_logo_new.png" \
                height="80">](https://serpentine-h2020.eu)', unsafe_allow_html=True)

st.markdown('Powered by: \
            [<img src="https://matplotlib.org/_static/logo_dark.svg" height="25">](https://matplotlib.org) \
            [<img src="https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.svg" height="30">](https://streamlit.io) \
            [<img src="https://raw.githubusercontent.com/sunpy/sunpy-logo/master/generated/sunpy_logo_landscape.svg" height="30">](https://sunpy.org) \
            [<img src="https://raw.githubusercontent.com/SciQLop/speasy/main/logo/logo_speasy.svg" height="30">](https://pypi.org/project/speasy/) \
            [<img src="app/static/amdaPrint.png" height="30">](http://amda.irap.omp.eu/)',
            unsafe_allow_html=True)

if "verbose" in st.session_state.keys():
    if int(st.session_state["verbose"][0]) == 1:
        st.markdown("""---""")
        st.markdown('## Debug Info')
        st.write(st.session_state)

        os.environ['SPEASY_CORE_DISABLED_PROVIDERS'] = "sscweb,archive,csa"
        import plotly
        import solarmach
        import speasy
        import sunkit_magex
        import sunpy
        import sys
        from io import StringIO
        tmp = sys.stdout
        my_result = StringIO()
        sys.stdout = my_result
        sunpy.util.system_info()
        print('')
        print('Solar-MACH Dependencies')
        print('#######################')
        print(f'plotly: {plotly.__version__}')
        print(f'solarmach: {solarmach.__version__}')
        print(f'speasy: {speasy.__version__}')
        print(f'streamlit: {st.__version__}')
        print(f'sunkit_magex: {sunkit_magex.__version__}')
        sys.stdout = tmp

        st.code(my_result.getvalue())

# remove 'Made with Streamlit' footer
# MainMenu {visibility: hidden;}
hide_streamlit_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# TODO: un-comment the following when streamlit-analytics has been updated with https://github.com/jrieke/streamlit-analytics/pull/44
# if os.path.exists('.streamlit/secrets.toml'):
#     streamlit_analytics.stop_tracking(unsafe_password=st.secrets["streamlit_analytics_password"])
# else:
#     # Use default password if it is not defined in a streamlit secret. Change this if you want to use it!
#     streamlit_analytics.stop_tracking(unsafe_password='opdskf03i45+0ikfg')

# if not in analytics mode, clear params from URL because Streamlit 1.0 still
# get some hickups when one changes the params; it then gets confused with the
# params in the URL and the one from the widgets.
if 'analytics' in query_params.keys():
    if not query_params['analytics'][0] == 'on':
        clear_url()
else:
    clear_url()

# # goatcounter
# import streamlit.components.v1 as components
# html_string = """
# <script data-goatcounter="https://solar-mach.goatcounter.com/count"
#         async src="//gc.zgo.at/count.js"></script>
# """
# components.html(html_string)
