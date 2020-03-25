# backmapping.py

'''
Jan 2020: start playing around with etspice. We want to build a python-based backmapping tool for ESA for the usual spacecraft around

ECLIPJ2000 will be used which is a reference frame for positions in the solar system where the x-y plane corresponds to the  Earth's ecliptic plane.
'''

# if not in Kiel:
# import os as os
# os.environ["SPICE_DATA_DIR"] = "/home/dresing/data/projects/spice"

# from etspice import STEREO_A, STEREO_B
# pos_a = STEREO_A.position(dt.datetime.now())
# pos_b = STEREO_B.position(dt.datetime.now())
# print(pos_a, pos_b)

import math

import matplotlib.pyplot as plt
import numpy as np
import scipy.constants as const
from sunpy.coordinates import frames
from sunpy.coordinates import get_horizons_coord

plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['font.size'] = 15
plt.rcParams['agg.path.chunksize'] = 20000

# disable unnecessary logging
from sunpy import log
log.setLevel('WARNING')

AU = const.au / 1000  # km


# pos_bepi = get_horizons_coord('MPO', dt.datetime.now())  #(lon, lat, radius) in (deg, deg, AU)

def make_the_plot(date, sc_list, vsw_list, flare_long):
    fig, ax = plt.subplots(subplot_kw=dict(projection='polar'), figsize=(8, 8))
    r = np.arange(0.007, 1.3, 0.001)
    if len(vsw_list) == 0:
        vsw_list = np.zeros(len(sc_list)) + 400

    color_dic = {'STEREO-A': 'red', 'STEREO-B': 'blue', 'Earth': 'green', 'MPO': 'orange', 'PSP': 'purple',
                 'Solar Orbiter': 'dodgerblue'}
    for i, sc in enumerate(sc_list):
        sc_color = color_dic[sc]
        sep = get_long_sep(sc, date, flare_long, vsw=vsw_list[i])

        if sc in ['Earth', 'EARTH']:
            pos = get_horizons_coord(399, date, 'id')
        else:
            pos = get_horizons_coord(sc, date)  # (lon, lat, radius) in (deg, deg, AU)
        pos = pos.transform_to(frames.HeliographicCarrington)

        dist_a = pos.radius.value
        sc_long = pos.lon.value

        v_A = vsw_list[i]

        pos_E = get_horizons_coord(399, date, 'id')  # (lon, lat, radius) in (deg, deg, AU)
        pos_E = pos_E.transform_to(frames.HeliographicCarrington)

        E_long = pos_E.lon.value
        dist_e = pos_E.radius.value

        omega = np.radians(360. / (25.38 * 24 * 60 * 60))  # rot-angle in rad/sec, sidereal period

        tt = dist_a * AU / vsw_list[i]
        alpha = np.degrees(omega * tt)

        sc_long_shifted = sc_long - E_long
        if sc_long_shifted < 0.:
            sc_long_shifted = sc_long_shifted + 360.

        delta_flare = flare_long - E_long
        if delta_flare < 0.:
            delta_flare = delta_flare + 360.

        A_west_spiral = np.radians(sc_long_shifted)

        alpha_f = np.deg2rad(delta_flare) + omega / (v_A / AU) * (dist_e / AU - r) - (
                    omega / (v_A / AU) * (dist_e / AU))

        alpha_A = np.deg2rad(sc_long_shifted) + omega / (v_A / AU) * (dist_a - r)
        ax.plot(alpha_A, r, color=sc_color)
        ax.plot(np.deg2rad(sc_long_shifted), dist_a, 's', color=sc_color, label=sc)

    ax.plot(alpha_f, r, '--k')
    arr1 = plt.arrow(alpha_f[0], 0.01, 0, 1.1, head_width=0.12, head_length=0.11, edgecolor='black', facecolor='black',
                     lw=2, zorder=5, overhang=0.2)

    plt.subplots_adjust(left=0.2, bottom=0.1, right=0.8, top=0.8)  # , wspace=None, hspace=None)
    ax.legend(loc=1, bbox_to_anchor=(1.3, 1.3))
    ax.set_rlabel_position(120)
    ax.set_theta_zero_location("S")
    ax.set_rmax(1.3)
    ax.set_rmin(0.01)
    ax.set_title(date + '\n')
    plt.show()


def get_long_sep(sc, date, flare_long, vsw=400):
    '''
    Determines the longitudinal separation angle of a given spacecraft and a given flare longitude
    Parameters
    ----------
    sc : `str`
        The spacecraft for which to calculate positions. 
        'STEREO-A', 'STEREO-B', 'SOHO', 'MPO' (BepiColombo), 'PSP', 'SDO'
    id_type : `str`

    '''
    if sc in ['Earth', 'EARTH']:
        pos = get_horizons_coord(399, date, 'id')
    else:
        pos = get_horizons_coord(sc, date)  # (lon, lat, radius) in (deg, deg, AU)
    pos = pos.transform_to(frames.HeliographicCarrington)

    lon = pos.lon.value
    dist = pos.radius.value

    omega = math.radians(360. / (25.38 * 24 * 60 * 60))  # rot-angle in rad/sec, sidereal period

    tt = dist * AU / vsw
    alpha = math.degrees(omega * tt)

    long_sep = flare_long - (lon + alpha)
    if long_sep > 180.:
        long_sep = long_sep - 360

    if long_sep < -180.:
        long_sep = 360 - abs(long_sep)

    print('spacecraft: {}'.format(sc))
    print('alpha: {:.1f}°'.format(alpha))
    print('lon: {:.1f}°'.format(lon))
    print('v_sw: {:.1f} km/s'.format(vsw))
    print('Longitudinal separation: {:.1f}°'.format(long_sep))
    print()

    return long_sep


def get_pos_diff_between_spacecraft(sc1, sc2, date):
    pos1 = get_horizons_coord(sc1, date)
    pos2 = get_horizons_coord(sc2, date)
    print('lon lat r (sc1):', pos1)
    print('lon lat r (sc2):', pos2)
    londiff = abs(pos1.lon.value - pos2.lon.value)
    if londiff > 180.:
        londiff = londiff - 360
    if londiff < -180.:
        londiff = 360 - abs(londiff)

    latdiff = abs(pos1.lat.value - pos2.lat.value)
    rdiff = pos1.radius.value - pos2.radius.value

    diff = np.array([londiff, latdiff, rdiff])

    return diff
