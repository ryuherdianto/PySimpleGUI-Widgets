"""
  COVID-19 Distance Tracking Widget
  Display distances from your zipcode to the known cases of COVID-19 in your area
  BE SAFE EVERYONE!
  Don't panic but do protect yourself
  The data acquisition and processing portion of this code (i.e. the hard stuff) was provided
  by Isael Dryer that can be executed online - https://repl.it/@IsraelDryer/Covid-19-Distance
  Oh, also grabbed some of his Weather Widget code to create the window.
  https://github.com/israel-dryer/Weather-App

  Copyright 2020 PySimpleGUI.com
  Learn more about PySimpleGUI http://www.PySimpleGUI.org GitHub http://www.PySimpleGUI.com

  Requires geopy and PySimpleGUI... both are pip installable

  The data source is:
  2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE
  https://github.com/CSSEGISandData/COVID-19

  EDUCATE YOURSELF - Read sources that are up to date and known to be solid, ubiased outlets
  https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6
"""

import pandas as pd
import geopy
from geopy.distance import distance
from geopy.geocoders import Nominatim
import PySimpleGUI as sg
import json
from os import path
from os import remove
import datetime
import webbrowser

sg.theme('Dark Red')
# sg.theme('Light Green 6')     # If you want a slightly more upbeat color theme
TXT_COLOR = sg.theme_text_color()
BG_COLOR = sg.theme_background_color()
ALPHA = 1.0

NUM_CITIES = 5

SETTINGS_FILE = path.join(path.dirname(__file__), r'C19-widget.cfg')

def load_settings():
    settings = {'zipcode': 'New York, NY', 'country': 'United States'}

    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
    except:
        sg.popup_quick_message('No settings file found... will create one for you', keep_on_top=True)
        settings = change_settings(settings)
        zipcode = settings['zipcode']
        if not zipcode:
            sg.popup_error('Aborting', auto_close=True, auto_close_duration=2)
            exit(69)
        save_settings(settings)

    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def change_settings(settings):
    layout = [[sg.T('Zipcode OR City, State for your location')],
              [sg.I(settings.get('zipcode', ''), size=(15,1), key='-ZIP-')],
              [sg.T('Country')],
              [sg.I(settings.get('country', 'United States'), size=(15,1), key='-COUNTRY-')],
              [sg.B('Ok', bind_return_key=True), sg.B('Cancel')],
              ]
    event, values = sg.Window('Settings', layout, keep_on_top=True).read(close=True)
    if event == 'Ok':
        settings['zipcode'] = values['-ZIP-']
        settings['country'] = values['-COUNTRY-']

    return settings


def distance_list(settings, window):
    # Setup the geolocator
    geopy.geocoders.options.default_user_agent = 'my_app/1'
    geopy.geocoders.options.default_timeout = 7
    geolocator = Nominatim()

    # Find location based on my zip code
    try:
        # location = geolocator.geocode({'postalcode' : '42420', 'country':settings['country']})      # type: geopy.location.Location
        location = geolocator.geocode(f'{settings["zipcode"]} {settings["country"]}')      # type: geopy.location.Location
        myloc = (location.latitude, location.longitude)
        window['-LOCATION-'].update(location.address)
        window['-LATLON-'].update(myloc)
    except Exception as e:
        sg.popup_error(f'Exception computing distance. Exception {e}', 'Deleting your settings file', keep_on_top=True)
        remove(SETTINGS_FILE)
        return None

    # Download Covid-19 data
    file_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv"
    df = pd.read_csv(file_url)

    def distance_in_miles(row):
      """ Calculate the distance between my location and the other locations in the dataset """
      rowloc = (row.Lat, row.Long)
      miles = distance(myloc, rowloc).miles
      return miles

    df['DistanceInMiles'] = df.apply(distance_in_miles, axis=1)

    # Print the top 10 nearest locations
    return df.sort_values('DistanceInMiles').head(NUM_CITIES)


def create_output(distances):
    out = []
    values = distances.values[0:5]
    for data in values:
        out.append(f'{data[0]:30} {data[1]:4} {data[-1]:8.2f}')
    return out


def nearest(distances):
    return distances.values[0][-1]


def update_display(window, zipcode, distances):
    if distances is not None:
        text = create_output(distances)
        for i, line in enumerate(text):
            window[i].update(line)
        window['-ZIP-'].update(zipcode)
        window['-NEAREST-'].update(f'{nearest(distances):.2f} Miles')
    window['-UPDATED-'].update('Updated: ' + datetime.datetime.now().strftime("%B %d %I:%M:%S %p"))

def create_window():
    """ Create the application window """
    PAD = (0,0)
    main_data_col = [*[[sg.T(size=(56,1), font='Courier 12', key=i, background_color=sg.theme_text_color(), text_color=sg.theme_background_color(), pad=(0,0))] for i in range(NUM_CITIES)]]

    layout = [[sg.T('COVID-19 Distance', font='Arial 40 bold', pad=PAD),
               sg.Text('×', font=('Arial Black', 16), pad=((50,10), 0), justification='right', background_color=BG_COLOR, text_color=TXT_COLOR, enable_events=True, key='-QUIT-')],
              [sg.T(size=(15,1), font='Arial 40 bold', key='-ZIP-', pad=PAD)],
              [sg.T(size=(12,1), font='Arial 30 bold', key='-NEAREST-', pad=PAD)],
              [sg.T(size=(40,2), key='-LOCATION-')],
              [sg.T(size=(40,1), key='-LATLON-')],
              [sg.Col(main_data_col, pad=(0,0))],
              [sg.T(size=(40,1), font='Arial 8', key='-UPDATED-')],
              [sg.T('Settings', key='-SETTINGS-', enable_events=True),
               sg.T('        Latest Statistics', key='-MOREINFO-',enable_events=True),
               sg.T('        Refresh', key='-REFRESH-',enable_events=True)],
              ]

    window = sg.Window(layout=layout, title='COVID Distance Widget', margins=(0, 0), finalize=True, keep_on_top=True, no_titlebar=True, grab_anywhere=True, alpha_channel=ALPHA)

    window['-SETTINGS-'].set_cursor('hand2')
    window['-MOREINFO-'].set_cursor('hand2')
    window['-REFRESH-'].set_cursor('hand2')
    window['-QUIT-'].set_cursor('hand2')

    return window


def main(refresh_rate, settings):

    zipcode = settings['zipcode']
    """ The main program routine """
    timeout_minutes = refresh_rate * 60 * 1000

    # Create main window
    window = create_window()

    distances = distance_list(settings, window)
    update_display(window, zipcode, distances)

    while True:
        event, values = window.read(timeout=timeout_minutes)
        if event in (None, 'Exit', '-QUIT-'):
            break
        elif event == '-SETTINGS-':
            settings = change_settings(settings)
            # Insert a proper settings window here
            zipcode = settings['zipcode']
        elif event == '-MOREINFO-':
            webbrowser.open(r'https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6')
        elif event == '-REFRESH-':
            pass        # will automatically refresh so nothing to do

        if zipcode:
            distances = distance_list(settings, window)
            settings['zipcode'] = zipcode
            save_settings(settings)
            update_display(window, zipcode, distances)
    window.close()

if __name__ == '__main__':
    settings = load_settings()
    main(5, settings)