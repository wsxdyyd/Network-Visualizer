# Jonathan Valiente.  All rights reserved. 2022

#The plan is to distribute the source code of Network Visualizer as public infrastructure.
# It is my intention to lead its development with the goals of incentivizing its development, improving its quality, and furthering its utility; I stand on the shoulders of giants and desire to make contributions for the betterment of humanity. :)

# The software is provided "As is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose and noninfringement.
# in no event shall the authors be liable for any claim, damages or
# other liability, whether in an action of contract, tort or otherwise,
# arising from, out of or in connection with the software or the use or
# other dealings in the software.

# Additional Authors:



#Standard Library
import atexit
from importlib import reload 
import json
from math import floor
from multiprocessing import Process
import os
from random import random
import sys
import time
import threading
from typing import Callable



#Additional Libraries
import ipwhois
from ipwhois import IPWhois  # IP description and abuse emails
import netifaces 
import pygeoip
from pyproj import Proj
from skimage.color import rgb2lab, lab2rgb
import zmq 
import zmq.auth #TODO: authorize connections


#Kivy Library
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import sp, dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.checkbox import CheckBox
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.scatter import Scatter
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.utils import get_hex_from_color


###################################################################
# Dynamic Reloading of Network Visualizer Code - reload code without having to restart the program. Saves time not having to restart the program while developing.
# There is an issue with exception handling since upgrading to python3~. I use visual studio to catch exception that are silenced when running directly from terminal.

try:
    import network_sniffer
    reload(network_sniffer)

    from network_sniffer import *

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broken in database_config.py")


try:
    import utilities.database_config

    reload(utilities.database_config)
    from utilities.database_config import *

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broken in utilities/database_config.py")



try:
    import utilities.iconfonts

    reload(utilities.iconfonts)
    from utilities.iconfonts import *

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in utilities/icofonts.py")


try:
    import utilities.utils

    reload(utilities.utils)
    from utilities.utils import *

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in utilities/utils.py")


try:
    import widgets.city_widget

    reload(widgets.city_widget)
    from widgets.city_widget import City_Widget

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in widgets/city_widget.py")


try:
    import widgets.computer_widget

    reload(widgets.computer_widget)
    from widgets.computer_widget import My_Computer

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broken in widgets/computer_widget.py")


try:
    import widgets.country_widget

    reload(widgets.country_widget)
    from widgets.country_widget import Country_Widget

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in widgets/country_widget.py")


try:
    import widgets.ip_widget

    reload(widgets.ip_widget)
    from widgets.ip_widget import IP_Widget

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in widgets/ip_widget.py")


try:
    import widgets.settings_panel

    reload(widgets.settings_panel)
    from widgets.settings_panel import Settings_Panel

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in widgets/settings_panel.py")

########################################################################




class GUI_Manager(ScreenManager):

    """
    GUI_Manager runs the show. This class stores program state, update loops, data structures, and anything else used for the visualizer.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.kivy_application = kwargs["kivy_application"]
        self.resource_path = kwargs["resource_path"]

        # Load saved configuration
        with open(
            os.path.join(self.resource_path, "configuration/config.json"), "r+"
        ) as configuration_file:
            self.config_variables_dict = json.load(configuration_file)

        # Load cached IP whois information
        with open(
            os.path.join(self.resource_path, "assets/database/whois.json"), "r+"
        ) as ip_whois_info_file:
            self.ip_whois_info_dict = json.load(ip_whois_info_file)

        # Views created for ScreenManager - Graph, Mercator, Table, and Malicious
        self.graph_view = Screen(name="graph")
        self.table_view = Screen(name="table")
        self.malicious_view = Screen(name="malicious")

        self.add_widget(self.graph_view)
        self.add_widget(self.table_view)
        self.add_widget(self.malicious_view)

        self.current = "graph"  # self.current is the variable name used by ScreenManager to select the view (see Kivy documentation)

        register(
            "default_font",
            os.path.join(self.resource_path, "assets/fonts/fontawesome-webfont"),
            os.path.join(self.resource_path, "assets/fonts/font-awesome.fontd"),
        )

        register(
            "extra_font",
            os.path.join(self.resource_path, "assets/fonts/fontello"),
            os.path.join(self.resource_path, "assets/fonts/fontello.fontd"),
        )

        self.window_x = Window.size[0]
        self.window_y = Window.size[1]
        self.center_x = self.window_x / 2
        self.center_y = self.window_y / 2
        self.window_ratio = (self.window_y - 75.0) / (self.window_y)

        # BUG: what is this?
        self.mercator_final_country_position = floor(
            (self.window_x - (self.center_x / 2)) / 66
        )

        self.session_name = ""
        self.session_query = ""

        self.x_pixels_per_meter = (
            self.window_x / 40030000.0
        )  # circumfrence of earth in meters (around equator)
        self.y_pixels_per_meter = (
            self.window_y / 18500000.0
        )  # circumfrence/2 of earth in meters (from pole to pole)

        self.ip_total_count = 1
        self.city_total_count = 1
        self.country_total_count = 1
        self.table_count = 0
        self.malicious_table_count = 0

        # these init values probably need to be better seleted..
        self.ip_largest_data_in = 1000
        self.ip_largest_data_out = 1000
        self.city_largest_data_out = 1000
        self.city_largest_data_in = 1000
        self.country_largest_data_out = 1000
        self.country_largest_data_in = 1000

        # Data Structures - See data structure documentation for proper use.
        self.country_dictionary = (
            {}
        )  # Contains all the created GUI widgets (country, city, ip) in heirarchy.
        self.interface_dictionary = {}  # Contains networking interface information
        self.ip_dictionary = {}  # Containes all the ip widgets
        self.sniffer_dictionary = {}  # Data from sniffer


        # Curated list of malcious ip's. https://raw.githubusercontent.com/stamparm/ipsum/master/ipsum.txt
        self.malicious_ips_dictionary =  retrieve_malicious_ips({})
        
        self.malicious_ips_local_database = {}  # Populated from local sql database
        self.found_malicious_ips = {}
        self.built_table = (
            {}
        )  # convience dictionary to quickly lookup if IP is in database
        self.malicious_table_dictionary = {}
        self.live_table_dictionary = (
            {}
        )  # convience dictionary to store live table widgets
        self.todo_ip_whois_array = []  # array container for batch IP whois lookup
        self.resolved_whois_data = {}
        self.misc_update_dictionary = {
            "my_computer": None,
            "country": {},
            "city": {},
            "ip": {},
        }
        self.protocol_color_dict = {
            "TCP": self.config_variables_dict["TCP Protocol Color"],
            "UDP": self.config_variables_dict["UDP Protocol Color"],
            "OTHER": self.config_variables_dict["OTHER Protocol Color"],
            "ICMP": [0, 0, 1, 1],
        }

        self.settings_toggle_boolean = False
        self.connected_to_sniffer = self.config_variables_dict[
            "auto_connect"
        ]  # TODO:edge case which autoconnect, but remote connection not setup?

        # TODO: clean up initalize vs first_time_starting
        self.initalize_layout = False

        if self.config_variables_dict["first_time_starting"] == False:
            self.first_time_starting = False
        else:
            self.first_time_starting = True
            self.config_variables_dict["first_time_starting"] = False

        self.country_labels = self.config_variables_dict["country_labels"]
        self.city_labels = self.config_variables_dict["city_labels"]
        self.ip_labels = self.config_variables_dict["ip_labels"]

        self.graph = True

        # variables to be populated
        self.sniffer_process = None
        self.data_socket = None  # ZMQ publish/subscribe pattern
        self.server_socket = None  # ZMQ client/server pattern
        self.sniffer_ip = None
        self.ip_whois_thread = None


        self.ip_database_lookup = pygeoip.GeoIP(
            os.path.join(self.resource_path, "assets/geolocation/GeoLiteCity.dat")
        )  # ip gelocation

        self.projection = Proj(
            "epsg:32663"
        )  # equirectangular projection (plate) on WGS84 (for mercator view) http://spatialreference.org/ref/epsg/wgs-84-plate-carree/

        
        self.my_mac_address = populate_network_interfaces()
        self.init_database_(self.session_name)
        self.make_settings_panel()
        self.make_GUI_widgets()

        if (
            self.config_variables_dict["auto_connect"] == True
            and not kwargs["switch_sniffer_info"]
        ):
            self.autoconnect_sniffer()

        elif kwargs["switch_sniffer_info"]:
            self.switch_to_new_sniffer(kwargs["switch_sniffer_info"])

        self.initalize_ip_from_sniffer()
        

        # Array of widgets for each Kivy Screenmanager view. When Sreenmanager switches views, the appropriate container of widgets is added/removed.
        # add widgets to these containers to populate them for the appropriate view. (Create a new array of widgets for a new view)

        # graph_view container
        self.graph_widgets = [
            self.widget_container,
            self.my_computer,
            self.main_settings_icon,
            self.table_icon,
            self.malicious_icon,
            self.persistent_widget_container,
        ]

        # table_view container
        self.table_widgets = [
            self.table_scroll,
            self.box_header_container,
            self.livetable_menu,
            self.graph_icon,
            self.main_settings_icon,
            self.malicious_icon,
            self.persistent_widget_container,
        ]

        # malicious_view container
        self.malicious_widgets = [
            self.malicious_ip_scroll,
            self.malicious_ip_container,
            self.malicious_menu,
            self.persistent_widget_container,
            self.graph_icon,
            self.main_settings_icon,
            self.table_icon,
        ]

        self.set_graph_view()  # start graph view on startup #TODO: give option to set default view

        Clock.schedule_interval(
            self.update_gui, 1 / 60
        )  # Main program loop to update GUI widget
        Clock.schedule_interval(
            self.update_from_sniffer, 1
        )  # Update data from sniffer --> self.sniffer_dictionary
        Clock.schedule_interval(self.ip_whois_lookup, 10)  # Batch lookup of IP whois
        Clock.schedule_interval(self.db_insert_ip_whois_info, 10)

    # End of GUI_Manager constructor

 

    def switch_to_new_sniffer(self, switch_sniffer_info: tuple[str, str]) -> None:

        """
        Switch to new network sniffer connection
        """

        sniffer_port = int(switch_sniffer_info[1])
        sniffer_data_port = sniffer_port + 1

        connect_string_sniffer = f"tcp://{switch_sniffer_info[0]}:{sniffer_port}"
        connect_string_subscribe = f"tcp://{switch_sniffer_info[0]}:{sniffer_data_port}"

        self.settings_panel.connection_label.text = f"[color=#00ff00][b]Connected[/b][/color] to [color=#00ff00][b]{switch_sniffer_info[0]}[/color][/b] on port [color=#00ff00][b]{sniffer_port}[/color][/b]"

        if switch_sniffer_info[0] == "localhost" and self.sniffer_process == None:

            try:
                keywords = {"port": sniffer_port}
                self.sniffer_process = Process(
                    name="sniffer", target=Sniffer, kwargs=keywords
                )  # start sniffer as new process for localhost condition
                self.sniffer_process.start()
                atexit.register(
                    self.sniffer_process.terminate
                )  # register sniffer cleanup function
            except:
                pass

        try:

            context = zmq.Context()

            keys = zmq.auth.load_certificate(
                os.path.join(self.resource_path, "configuration/keys/client.key_secret")
            )
            server_key, _ = zmq.auth.load_certificate(
                os.path.join(self.resource_path, "configuration/keys/server.key")
            )

            self.server_socket = context.socket(
                zmq.REQ
            )  # client/server pattern for message passing
            self.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.server_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.server_socket.connect(connect_string_sniffer)

            self.data_socket = context.socket(
                zmq.SUB
            )  # PUB/SUB pattern for sniffer data
            self.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.data_socket.connect(connect_string_subscribe)

            self.config_variables_dict["last_connected_sniffer"][
                0
            ] = switch_sniffer_info[0]
            self.config_variables_dict["last_connected_sniffer"][
                1
            ] = switch_sniffer_info[1]

        except Exception as e:
            print("Issue setting up ZMQ sockets", e)
            self.kivy_application.get_running_app().stop()  # Do we want to shutdown the application if program can't setup ZMQ sockets?


    def autoconnect_sniffer(self):

        """
        Setup ZMQ client/server and pub/sub sockets. If LocalHost, start Sniffer as new process.
        """

        self.settings_panel.auto_connect_checkbox.active = True

        sniffer_ip = self.config_variables_dict["last_connected_sniffer"][0]
        sniffer_port = self.config_variables_dict["last_connected_sniffer"][1]
        sniffer_data_port = sniffer_port + 1

        connect_string_sniffer = f"tcp://{sniffer_ip}:{sniffer_port}"
        connect_string_subscribe = f"tcp://{sniffer_ip}:{sniffer_data_port}"

        if sniffer_ip == "localhost":

            keywords = {"port": sniffer_port}
            self.sniffer_process = Process(
                name="sniffer", target=Sniffer, kwargs=keywords
            )  # start sniffer as new process for localhost condition
            self.sniffer_process.start()
            atexit.register(
                self.sniffer_process.terminate
            )  # register sniffer cleanup function

        try:
            context = zmq.Context()

            keys = zmq.auth.load_certificate(
                os.path.join(self.resource_path, "configuration/keys/client.key_secret")
            )
            server_key, _ = zmq.auth.load_certificate(
                os.path.join(self.resource_path, "configuration/keys/server.key")
            )

            self.server_socket = context.socket(
                zmq.REQ
            )  # client/server pattern for message passing
            self.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.server_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.server_socket.connect(connect_string_sniffer)

            self.data_socket = context.socket(
                zmq.SUB
            )  # PUB/SUB pattern for sniffer data
            self.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.data_socket.connect(connect_string_subscribe)

            print("Made the change! setup_sniffer_communication")
            self.settings_panel.connection_label.text = f"[color=#00ff00][b]Connected[/b][/color] to [color=#00ff00][b]{sniffer_ip}[/color][/b] on port [color=#00ff00][b]{sniffer_port}[/color][/b]"

        except Exception as e:
            print("Issue setting up ZMQ sockets")
            self.kivy_application.get_running_app().stop()  # Do we want to shutdown the application if program can't setup ZMQ sockets?

    def initalize_ip_from_sniffer(self) -> None:

        """
        Query Sniffer to setup outward facing IP
        """

        if self.sniffer_process is not None:

            self.server_socket.send(b"ip_info")
            encoded_ip = self.server_socket.recv()
            self.sniffer_ip = encoded_ip.decode("utf-8")

            my_ip_info = self.ip_database_lookup.record_by_addr(self.sniffer_ip)
            self.interface_dictionary[self.sniffer_ip] = my_ip_info

            if self.config_variables_dict["initalize"] == False:
                screen_x, screen_y = self.mercator_coordinates(
                    my_ip_info["longitude"], my_ip_info["latitude"]
                )
                self.my_computer.mercator_position = (screen_x, screen_y)


            else:
                self.my_computer.mercator_position = self.config_variables_dict[
                    "my_computer"
                ]["mercator_position"]

    def mix_colors(self, protocols: dict) -> tuple[float, float, float, float]:

        """
        Convience function to mix colors. Converts to LAB color space mixes them and converts back to RGB.
        """

        channel_a = 0
        channel_b = 0
        channel_c = 0
        count = 0

        for protocol in protocols.keys():

            key = protocol + " Protocol Color"

            lab_color = rgb2lab(self.config_variables_dict[key][0:3])

            channel_a += lab_color[0]
            channel_b += lab_color[1]
            channel_c += lab_color[2]

            count += 1

        sum_a_avg = channel_a / count
        sum_b_avg = channel_b / count
        sum_c_avg = channel_c / count

        rgb_color = lab2rgb([sum_a_avg, sum_b_avg, sum_c_avg])

        return list(rgb_color)

    def update_gui(self, time_delta: tuple) -> None:

        """
        Main Program Loop for updating GUI widgets based on current view (graph, table, etc)
        """

        total_data_out_accumulator = 0
        total_data_in_accumulator = 0

        data_in_color = get_hex_from_color(self.config_variables_dict["Data IN Color"])
        data_out_color = get_hex_from_color(
            self.config_variables_dict["Data OUT Color"]
        )

        if self.current == "graph":  # Start graph loop

            self.widget_container.clear_widgets()
            self.my_computer.update(state=self.graph)

            for country in self.country_dictionary:  # Start of Country loop

                country_data_in_accumulator = 0
                country_data_out_accumulator = 0
                country_new_data = False

                country_widget = self.country_dictionary[country][0]
                country_total_city_widgets = len(
                    self.country_dictionary[country][1]
                )  # len(city dictionary)
                country_widget.city_total_count = country_total_city_widgets

                country_draw_angle = angle_between_points(
                    self.my_computer.icon_scatter_widget.pos,
                    country_widget.icon_scatter_widget.pos,
                )
                country_widget.country_draw_angle = country_draw_angle

                ip_total_count = 0

                country_color_dict = {}

                for city_index, city in enumerate(
                    self.country_dictionary[country][1]
                ):  # Start of City loop

                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0
                    city_new_data = False

                    city_widget = self.country_dictionary[country][1][city][0]
                    city_number_of_ips = (
                        len(self.country_dictionary[country][1][city]) - 1
                    )

                    city_color_dict = {}

                    for ip_index, ip_widget in enumerate(
                        self.country_dictionary[country][1][city][1:]
                    ):  # Start of IP loop

                        if (
                            ip_widget.new_data == True
                        ):  # check ip for new data then set flag
                            city_new_data = True

                        city_data_in_accumulator += ip_widget.ip_data["data_in"]
                        city_data_out_accumulator += ip_widget.ip_data["data_out"]

                        if ip_widget.ip_data["data_in"] > self.ip_largest_data_in:
                            self.ip_largest_data_in = ip_widget.ip_data["data_in"]

                        if ip_widget.ip_data["data_out"] > self.ip_largest_data_out:
                            self.ip_largest_data_out = ip_widget.ip_data["data_out"]

                        city_color_dict[ip_widget.ip_data["last_packet"]] = True

                        if ip_widget.show == True:

                            # city_widget.last_packet = ip_widget.ip_data['last_packet']
                            # country_widget.last_packet = ip_widget.ip_data['last_packet']

                            ip_widget.update(
                                city_widget=city_widget,
                                city_number_of_ips=city_number_of_ips,
                                ip_index=ip_index,
                                last_packet=ip_widget.ip_data["last_packet"],
                                state=self.graph,
                            )

                            self.widget_container.add_widget(ip_widget)

                        # End of IP loop

                    ip_total_count += ip_index + 1

                    # Continue City loop
                    # print(city_color_dict.keys())

                    city_mixed_color = self.mix_colors(city_color_dict)

                    country_color_dict = (
                        city_color_dict | country_color_dict
                    )  # combine dictionaries python >3.9

                    if city_data_out_accumulator > self.city_largest_data_out:
                        self.city_largest_data_out = city_data_out_accumulator

                    if city_data_in_accumulator > self.city_largest_data_in:
                        self.city_largest_data_in = city_data_in_accumulator

                    city_widget.total_data_out = city_data_out_accumulator
                    city_widget.total_data_in = city_data_in_accumulator

                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    city_widget.new_data = city_new_data

                    if city_new_data == True:
                        country_new_data = True

                    if city_widget.show == True:
                        city_widget.update(
                            state=self.graph, protocol_color=city_mixed_color
                        )
                        self.widget_container.add_widget(city_widget)

                    # End of City loop

                # Continue Country loop

                country_mixed_color = self.mix_colors(country_color_dict)

                country_widget.ip_total_count = ip_total_count

                country_widget.new_data = country_new_data

                country_widget.total_data_in = country_data_in_accumulator
                country_widget.total_data_out = country_data_out_accumulator

                if country_data_in_accumulator > self.country_largest_data_in:
                    self.country_largest_data_in = country_data_in_accumulator

                if country_data_out_accumulator > self.country_largest_data_out:
                    self.country_largest_data_out = country_data_out_accumulator

                total_data_out_accumulator += country_data_out_accumulator
                total_data_in_accumulator += country_data_in_accumulator

                if country_widget.show == True:

                    country_widget.update(
                        state=self.graph, protocol_color=country_mixed_color
                    )

                    self.widget_container.add_widget(country_widget)

                # End of Country loop

            # Continue Graph loop

            self.my_computer.total_data_out = total_data_out_accumulator
            self.my_computer.total_data_in = total_data_in_accumulator

            self.my_computer.total_data_in_label.text = f"Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f} [/color][/b]"
            self.my_computer.total_data_out_label.text = f"  Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            summary_data_color = get_hex_from_color(
                self.config_variables_dict["Summary Data Color"]
            )

            for country in self.misc_update_dictionary["country"].keys():

                self.misc_update_dictionary["country"][
                    country
                ].data_IN_label.text = f" Data IN (MB): [b][color={data_in_color}]{self.misc_update_dictionary['country'][country].total_data_in/1000000.0:.3f} [/color][/b]"

                self.misc_update_dictionary["country"][
                    country
                ].data_OUT_label.text = f" Data OUT (MB): [b][color={data_out_color}]{self.misc_update_dictionary['country'][country].total_data_out/1000000.0:.3f}[/color][/b]"

                city_total_count = self.misc_update_dictionary["country"][
                    country
                ].city_total_count

                self.misc_update_dictionary["country"][
                    country
                ].total_cities_label.text = (
                    f"[b][color={summary_data_color}]{city_total_count}[/color][/b]"
                )

                ip_total_count = self.misc_update_dictionary["country"][
                    country
                ].ip_total_count

                self.misc_update_dictionary["country"][
                    country
                ].total_ip_label.text = (
                    f"[b][color={summary_data_color}]{ip_total_count}[/color][/b]"
                )

            for city in self.misc_update_dictionary["city"].keys():

                self.misc_update_dictionary["city"][
                    city
                ].data_IN_label.text = f" Data IN (MB): [b][color={data_in_color}]{self.misc_update_dictionary['city'][city].total_data_in/1000000.0:.3f}  [/color][/b]"

                self.misc_update_dictionary["city"][
                    city
                ].data_OUT_label.text = f" Data OUT (MB): [b][color={data_out_color}]{self.misc_update_dictionary['city'][city].total_data_out/1000000.0:.3f}[/color][/b]"

                ip_total_count = self.misc_update_dictionary["city"][
                    city
                ].ip_total_count

                self.misc_update_dictionary["city"][
                    city
                ].total_ip_label.text = (
                    f"[b][color={summary_data_color}]{ip_total_count}[/color][/b]"
                )

            for ip in self.misc_update_dictionary["ip"].keys():

                self.misc_update_dictionary["ip"][
                    ip
                ].data_IN_label.text = f"Data IN (MB): [b][color={data_in_color}]{self.misc_update_dictionary['ip'][ip].ip_data['data_in']/1000000.0:.6f}[/color][/b]"

                self.misc_update_dictionary["ip"][
                    ip
                ].data_OUT_label.text = f"  Data OUT (MB): [b][color={data_out_color}]{self.misc_update_dictionary['ip'][ip].ip_data['data_out']/1000000.0:.6f}[/color][/b]"

                self.misc_update_dictionary["ip"][
                    ip
                ].packet_label.text = f"Packet Count: [b][color={summary_data_color}] {self.misc_update_dictionary['ip'][ip].ip_data['packet_count']}[/b][/color]"

            # End of Graph loop

        elif self.current == "table":  # Start table loop

            self.widget_container.clear_widgets()

            for country in self.country_dictionary:  # Start of Country loop

                country_data_in_accumulator = 0
                country_data_out_accumulator = 0

                for city_index, city in enumerate(
                    self.country_dictionary[country][1]
                ):  # Begin City Loop

                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0

                    for ip_index, ip_widget in enumerate(
                        self.country_dictionary[country][1][city][1:]
                    ):  # Begin IP loop

                        city_data_in_accumulator += ip_widget.ip_data["data_in"]
                        city_data_out_accumulator += ip_widget.ip_data["data_out"]

                        # End of IP loop

                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    # End of City loop

                total_data_out_accumulator += country_data_out_accumulator
                total_data_in_accumulator += country_data_in_accumulator

                # End of Country loop

            # Continue table loop

            self.my_computer.total_data_out = total_data_out_accumulator
            self.my_computer.total_data_in = total_data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of table loop

        elif self.current == "malicious":  # Start malicious loop

            self.widget_container.clear_widgets()

            for country in self.country_dictionary:  # Start of Country loop

                country_data_in_accumulator = 0
                country_data_out_accumulator = 0

                for city_index, city in enumerate(
                    self.country_dictionary[country][1]
                ):  # Begin City Loop

                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0

                    for ip_index, ip_widget in enumerate(
                        self.country_dictionary[country][1][city][1:]
                    ):  # Begin IP loop

                        city_data_in_accumulator += ip_widget.ip_data["data_in"]
                        city_data_out_accumulator += ip_widget.ip_data["data_out"]

                        # End of IP loop

                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    # End of City loop

                total_data_out_accumulator += country_data_out_accumulator
                total_data_in_accumulator += country_data_in_accumulator

                # End of Country loop

            # Continue malicious loop
            self.my_computer.total_data_out = total_data_out_accumulator
            self.my_computer.total_data_in = total_data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of malicious loop

        # self.widget_container.add_widget(self.popup)

        # End of GUI loop

    def update_from_sniffer(self, time_delta: tuple) -> None:

        """
        Update GUI widgets and/or make new GUI widgets from network sniffer data.
        """

        self.recieve_data_from_sniffer()

        for (
            new_ip
        ) in (
            self.sniffer_dictionary.keys()
        ):  # iterate over the json dictionary sent from network_sniffer.py

            if (
                new_ip in self.ip_dictionary
            ):  # IP, City and Country widgets exist. Update IP data.

                self.ip_dictionary[new_ip].data_in_delta += (
                    self.sniffer_dictionary[new_ip]["data_in"]
                    - self.ip_dictionary[new_ip].ip_data["data_in"]
                )
                self.ip_dictionary[new_ip].data_out_delta += (
                    self.sniffer_dictionary[new_ip]["data_out"]
                    - self.ip_dictionary[new_ip].ip_data["data_out"]
                )

                self.ip_dictionary[new_ip].ip_data = self.sniffer_dictionary[new_ip]

                delta_new_packet = (
                    time.time() - self.sniffer_dictionary[new_ip]["delta_time"]
                )
                self.ip_dictionary[new_ip].delta_new_packet = delta_new_packet
                self.ip_dictionary[new_ip].connection_opacity = map_to_range(
                    delta_new_packet, 20, 0, 0, 1
                )

                # TODO use a selectable time threshold to trigger new data flag.
                if delta_new_packet < 20:
                    self.ip_dictionary[new_ip].new_data = True
                else:
                    self.ip_dictionary[new_ip].new_data = False

            else:  # Case:  IP widget doesn't exist

                geoip_info = self.sniffer_dictionary[new_ip]["geoip_info"]

                if geoip_info == None:
                    city = "Unresolved"
                    country = "Unresolved"
                    ip_longitude = "Unresolved"
                    ip_latitude = "Unresolved"
                    country_code = "Unresolved"
                else:
                    country = remove_inline_quotes(geoip_info["country_name"])
                    city = remove_inline_quotes(geoip_info["city"])
                    country_code = geoip_info["country_code"]
                    ip_longitude = geoip_info["longitude"]
                    ip_latitude = geoip_info["latitude"]

                ip_longitude_x, ip_latitude_y = self.mercator_coordinates(
                    ip_longitude, ip_latitude
                )

                ip_placeholder = IP_Widget(
                    gui_manager=self,
                    ip=new_ip,
                    ip_data=self.sniffer_dictionary[new_ip],
                    window_x=self.window_x,
                    window_y=self.window_y,
                    country=country,
                    city=city,
                    ip_latitude=ip_latitude,
                    ip_longitude=ip_longitude,
                    ip_latitude_y=ip_latitude_y,
                    ip_longitude_x=ip_longitude_x,
                    protocol_dict=self.protocol_color_dict,
                    resource_path=self.resource_path,
                )

                # Check after IP_widget is created in order to have the ip_placeholder reference for whois lookup
                if new_ip in self.ip_whois_info_dict.keys():
                    ip_whois_description = self.ip_whois_info_dict[new_ip]["nets"][0][
                        "description"
                    ]
                    ip_placeholder.whois_description.text = ip_whois_description
                    self.live_table_dictionary[new_ip].children[
                        5
                    ].text = ip_whois_description

                    cursor = db.cursor()
                    cursor.execute(
                        f"""UPDATE Live SET description = "{ip_whois_description}" WHERE ip="{new_ip}" """
                    )
                    db.commit()

                else:
                    self.todo_ip_whois_array.append((new_ip, ip_placeholder))

                if (
                    new_ip in self.malicious_ips_dictionary
                    or new_ip in self.malicious_ips_local_database
                ):
                    ip_placeholder.tag_malicious()

                self.ip_dictionary[
                    new_ip
                ] = ip_placeholder  # add IP widget into convenience lookup dictionary, seperate from the hierarchical country dictionary

                self.ip_total_count += 1  # After we update total_ip_label.text

                #### ip widget made, now check to see if country and city widget exist

                if country in self.country_dictionary:  # Country widget exists

                    ip_placeholder.country_widget = self.country_dictionary[country][0]

                    if (
                        city in self.country_dictionary[country][1]
                    ):  # City widget exists

                        ip_placeholder.city_widget = self.country_dictionary[country][
                            1
                        ][city][0]

                        self.country_dictionary[country][1][city][
                            0
                        ].ip_total_count += 1  # first item in array is city widget
                        self.country_dictionary[country][1][city].append(
                            ip_placeholder
                        )  # add ip widget to array in city dictionary

                        self.country_dictionary[country][1][city][
                            0
                        ].set_mercator_inital_position()

                        if (
                            self.country_dictionary[country][1][city][0].show_ip_widgets
                            == True
                        ):
                            ip_placeholder.show = True  # flag to display IP widget

                    else:  # Case: Country widget exists, but no city widget exists. Build city widget

                        country_widget = self.country_dictionary[country][
                            0
                        ]  # first item in array is country widget
                        country_screen_x = (
                            country_widget.screen_x
                        )  # Get x screen position of Country Widget
                        country_screen_y = (
                            country_widget.screen_y
                        )  # Get y screen position of Country Widget

                        # convert to dictionary

                        city_widget = City_Widget(
                            x_cord_country=country_screen_x,
                            y_cord_country=country_screen_y,
                            gui_manager=self,
                            center_x=self.center_x,
                            center_y=self.center_y,
                            window_x=self.window_x,
                            window_y=self.window_y,
                            city=city,
                            country=country,
                            latitude=ip_latitude,
                            longitude=ip_longitude,
                            latitude_y=ip_latitude_y,
                            longitude_x=ip_longitude_x,
                            resource_path=self.resource_path,
                            protocol_dict=self.protocol_color_dict,
                            init_state=self.graph,
                        )

                        # set display flags for City and IP widgets
                        if country_widget.show_city_widgets == True:
                            city_widget.show = True

                            if city_widget.show_ip_widgets == True:
                                ip_placeholder.show = True

                        ip_placeholder.city_widget = city_widget

                        self.country_dictionary[country][1].setdefault(city, []).append(
                            city_widget
                        )  # set City widget to first position in array. See data structure documentation for clarification.
                        self.country_dictionary[country][1][city].append(
                            ip_placeholder
                        )  # add ip widget to array in city dictionary

                        city_widget.set_mercator_inital_position()

                        self.city_total_count += (
                            1  # After we update total_cities_label.text
                        )

                else:  # Case: Country widget and City widget don't exist.  Build Country and City widget

                    # initalize position for country widget on screen for graph view
                    # country_x = self.my_computer.icon_scatter_widget.pos[0]  + randrange(-100, 100) + cos(randrange(-100,100)) * self.my_computer.country_radius_slider.value
                    # country_y = self.my_computer.icon_scatter_widget.pos[1]  + randrange(-100, 100) + sin(randrange(-100,100)) * self.my_computer.country_radius_slider.value

                    country_screen_x = self.window_x * random()
                    country_screen_y = self.window_y * random()

                    country_widget = Country_Widget(
                        screen_x=country_screen_x,
                        screen_y=country_screen_y,
                        gui_manager=self,
                        center_x=self.center_x,
                        center_y=self.center_y,
                        window_x=self.window_x,
                        window_y=self.window_y,
                        country=country,
                        country_code=country_code,
                        country_index=self.country_total_count,
                        resource_path=self.resource_path,
                        protocol_dict=self.protocol_color_dict,
                        init_state=self.graph,
                    )

                    if self.my_computer.show_country_widgets == True:
                        country_widget.show = True

                    if self.my_computer.show_city_widgets == True:
                        country_widget.show_city_widgets = True

                    if self.my_computer.show_ip_widgets == True:
                        country_widget.show_ip_widgets = True

                    self.country_dictionary.setdefault(
                        country, [country_widget]
                    ).append(
                        {}
                    )  # Append to country dictionary. Set first item in array as country widget and second item as city dictionary. See data structure documentation for clarification.

                    city_widget = City_Widget(
                        gui_manager=self,
                        center_x=self.center_x,
                        center_y=self.center_y,
                        window_x=self.window_x,
                        window_y=self.window_y,
                        city=city,
                        country=country,
                        latitude=ip_latitude,
                        longitude=ip_longitude,
                        latitude_y=ip_latitude_y,
                        longitude_x=ip_longitude_x,
                        resource_path=self.resource_path,
                        protocol_dict=self.protocol_color_dict,
                        init_state=self.graph,
                    )

                    if self.my_computer.show_city_widgets == True:
                        city_widget.show = True

                    if self.my_computer.show_ip_widgets == True:
                        city_widget.show_ip_widgets = True
                        ip_placeholder.show = True

                    self.country_dictionary[country][1].setdefault(city, []).append(
                        city_widget
                    )  # set City widget to first position in array. See data structure documentation for clarification.
                    self.country_dictionary[country][1][city].append(
                        ip_placeholder
                    )  # add ip widget to array in city dictionary

                    city_widget.set_mercator_inital_position()

                    ip_placeholder.city_widget = city_widget
                    ip_placeholder.country_widget = country_widget
                    ip_placeholder.set_position()

                    self.city_total_count += (
                        1  # After we update total_cities_label.text
                    )
                    self.country_total_count += (
                        1  # After we update total_countries_label.text
                    )

        summary_data_color = get_hex_from_color(
            self.config_variables_dict["Summary Data Color"]
        )

        self.my_computer.total_ip_label.text = (
            f"[b][color={summary_data_color}] {self.ip_total_count} [/color][/b]"
        )

        self.my_computer.total_cities_label.text = (
            f"[b][color={summary_data_color}]{self.city_total_count}[/color][/b]"
        )

        self.my_computer.total_countries_label.text = (
            f"[b][color={summary_data_color}]{self.country_total_count}[/color][/b]"
        )

        cursor = db.cursor()
        cursor.execute("SELECT * from malicious_ips")
        malicious_ips = cursor.fetchall()
        self.my_computer.malicious_ip_count.text = (
            f"[color=FF0000]Detected Malicious IP's: [b]{str(len(malicious_ips))}[/b]"
        )

        if self.initalize_layout == False:
            self.initalize_layout = True
            self.my_computer.radius_slider.value += 1

    # End of update_from_sniffer loop

    def recieve_data_from_sniffer(self) -> None:

        """
        Get data (sniffer_dictionary) from network sniffer.
        """

        try:
            json_data = self.data_socket.recv(flags=zmq.NOBLOCK)
            self.sniffer_dictionary = json.loads(json_data)

        except Exception as e:
            pass

    def ip_whois_lookup(self, time_delta: float):

        """
        Scheduled function to periodically start a new thread for IP whois lookup.
        """

        # Check two conditions if the ip_whois_thread is not running.

        if self.ip_whois_thread == None:
            todo_ip_whois_array_copy = (
                self.todo_ip_whois_array.copy()
            )  # copy IP's that need lookup
            self.todo_ip_whois_array = []  # reset the datastructure
            self.ip_whois_thread = threading.Thread(
                target=self.ip_whois_lookup_thread,
                kwargs={"todo_ip_whois_array": todo_ip_whois_array_copy},
            ).start()  # start the thread with a batch of IP's

        elif self.ip_whois_thread.is_alive() == False:
            todo_ip_whois_array_copy = (
                self.todo_ip_whois_array.copy()
            )  # copy IP's that need lookup
            self.todo_ip_whois_array = []  # reset the datastructure
            self.ip_whois_thread = threading.Thread(
                target=self.ip_whois_lookup_thread,
                kwargs={"todo_ip_whois_array": todo_ip_whois_array_copy},
            ).start()  # start the thread with a batch of IP's

        elif (
            self.ip_whois_thread.is_alive() == True
        ):  # thread is still running so wait for it to finish before starting again
            pass

    def db_insert_ip_whois_info(self, time_delta: float) -> None:

        """
        Insert whois information into sqlite3 database. Done this way to prevent issue with opening db.cursor in seperate thread.
        """

        if (
            not self.resolved_whois_data
        ):  # if self.resolved_whois_data dictionary is not empty
            cursor = db.cursor()

            for key in self.resolved_whois_data:

                cursor.execute(
                    f"""UPDATE Live SET description = "{self.resolved_whois_data[key]}" WHERE ip="{key}" """
                )
                db.commit()

                del self.resolved_whois_data[key]

    def ip_whois_lookup_thread(self, **kwargs) -> None:

        """
        Function for whois lookup on a batch of IP's (kwargs["todo_ip_whois_array"]).
        Called in a seperate thread due to ~1 second network connection delay per IP.
        Creates a slightly noticable delay occasionally in the visualizer. May want to use an alternative pattern like python async if it can prevent this -- preliminary attempt proved otherwise.
        """

        for ip_tuple in kwargs["todo_ip_whois_array"]:
            ip, ip_object = ip_tuple

            try:
                ip_whois = IPWhois(ip)
                ip_whois_info = ip_whois.lookup_whois()
                ip_whois_description = ip_whois_info["nets"][0]["description"]

                if ip_whois_description == None:
                    ip_whois_description = "No Description Available"

                while ip_whois_description.find("'") >= 0:
                    ip_whois_description = ip_whois_description.replace("'", "")

                while ip_whois_description.find('"') >= 0:
                    ip_whois_description = ip_whois_description.replace('"', "")

                ip_whois_info["nets"][0]["description"] = ip_whois_description

            except ValueError as e:
                ip_whois_description = "Invalid IP address: %s." % ip
                self.ip_whois_info_dict[ip] = {
                    "nets": [{"description": ip_whois_description}]
                }
                ip_object.whois_description.text = ip_whois_description
                print(ip_whois_description, "<----ValueError")
            except ipwhois.exceptions.IPDefinedError as e:
                ip_whois_description = "Local IP Address"
                self.ip_whois_info_dict[ip] = {
                    "nets": [{"description": ip_whois_description}]
                }
                ip_object.whois_description.text = "Local IP Address"
                print(ip_whois_description, "<----ipwhois.exceptions.IPDefinedError")
            except ipwhois.exceptions.ASNRegistryError as e:
                ip_whois_description = "%s" % e
                self.ip_whois_info_dict[ip] = {
                    "nets": [{"description": ip_whois_description}]
                }
                ip_object.whois_description.text = ip_whois_description
                print(ip_whois_description, "<---ipwhois.exceptions.ASNRegistryError")
            except Exception as e:
                ip_whois_description = "Error %s" % e
                self.ip_whois_info_dict[ip] = {
                    "nets": [{"description": ip_whois_description}]
                }
                ip_object.whois_description.text = ip_whois_description
                print(ip_whois_description, "<----Exception")

            try:
                ip_object.whois_description.text = ip_whois_description
                self.ip_whois_info_dict[ip] = ip_whois_info
                self.resolved_whois_data[ip] = ip_whois_description
                self.live_table_dictionary[ip].children[5].text = ip_whois_description

                if self.malicious_table_dictionary[ip]:
                    self.malicious_table_dictionary[ip].children[
                        6
                    ].text = ip_whois_description

                # TODO: use isInstance() or id to search children instead of hard coded children[5]
            except:
                pass

    def set_graph_view(self, *button: Button):

        """
        Transition screenmanager to graph view and display appropriate widgets.
        """

        self.widget_container.clear_widgets()
        current_view = self.current  # get current screenmanager state

        if self.graph == False:
            self.graph_view.add_widget(self.mercator_container)

        ###### Clean up previous view

        if current_view == "table":
            Clock.unschedule(self.update_table)
            self.table_view.clear_widgets()
            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.icon_scatter_widget.remove_widget(country_widget.label)

        elif current_view == "malicious":
            Clock.unschedule(self.update_malicious_table)
            self.malicious_view.clear_widgets()
            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.icon_scatter_widget.remove_widget(country_widget.label)

        #####

        # Produce graph view

        # if self.settings_panel.summary_data_popup_open == True and self.settings_panel.summary_data_layout not in self.persistent_widget_container.children:
        #     self.persistent_widget_container.add_widget(self.settings_panel.summary_data_layout)

        if (
            self.settings_panel.color_picker_popup_open == True
            and self.settings_panel.color_picker_layout
            not in self.persistent_widget_container.children
        ):
            self.persistent_widget_container.add_widget(
                self.settings_panel.color_picker_layout
            )

        if self.misc_update_dictionary["my_computer"]:
            self.persistent_widget_container.add_widget(
                self.misc_update_dictionary["my_computer"].menu_popup
            )

        for country in self.misc_update_dictionary["country"].keys():
            self.persistent_widget_container.add_widget(
                self.misc_update_dictionary["country"][country].menu_popup
            )

        for city in self.misc_update_dictionary["city"].keys():
            self.persistent_widget_container.add_widget(
                self.misc_update_dictionary["city"][city].menu_popup
            )

        for widget in self.graph_widgets:
            
            self.graph_view.add_widget(widget)
 
        

        self.transition.direction = "right"
        self.current = "graph"  # set screenmanager view

    def mercator_gui_update(self, dt):

        for country in self.country_dictionary:

            for city in self.country_dictionary[country][1]:
                data_in = 0
                data_out = 0

                for ip in self.country_dictionary[country][1][city][1:]:

                    data_in += ip.data_in_delta
                    data_out += ip.data_out_delta

                    ip.data_in_delta = 0
                    ip.data_out_delta = 0

                if data_in > 0:
                    self.country_dictionary[country][1][city][0].animate_mercator(
                        data_in
                    )

    def set_table_view(self, button: Button) -> None:

        """
        Transition screenmanager to table view and display appropriate widgets.
        """

        current_view = self.current  # get current screenmanager state

        ##### Clean up previous view
        if current_view == "graph":
            self.graph_view.clear_widgets()

            if self.settings_panel.color_picker_popup_open == True:
                self.persistent_widget_container.remove_widget(
                    self.settings_panel.color_picker_layout
                )

            if self.misc_update_dictionary["my_computer"]:
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["my_computer"].menu_popup
                )

            for country in self.misc_update_dictionary["country"].keys():
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["country"][country].menu_popup
                )

            for city in self.misc_update_dictionary["city"].keys():
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["city"][city].menu_popup
                )

        elif current_view == "malicious":
            Clock.unschedule(self.update_malicious_table)
            self.malicious_view.clear_widgets()
        #####

        # Produce table view

        self.live_data_in_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN Color"])}] Data IN (MB)[/color]   {icon("fa-sort", 25)}'
        # self.live_data_in_button.text = f"""[color={get_hex_from_color(self.config_variables_dict["Data IN Color"])}] Data IN (MB) [font=/Users/hack/Network-Visualizer/assets/fonts/fontello]{chr(62062)}[/font] [/color]"""
        # {icon('icon-minus-1', 25, 'extra_font')}

        self.live_data_out_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT Color"])}] Data OUT (MB)[/color]   {icon("fa-sort", 25)}'

        for widget in self.table_widgets:
            self.table_view.add_widget(widget)

        self.transition.direction = "down"
        self.current = "table"  # set screenmanager view

        Clock.schedule_interval(self.update_table, 1)

    def update_table(self, time_delta) -> None:

        cursor = db.cursor()

        # TODO: ip_dictionary?
        for n, ip in enumerate(self.sniffer_dictionary.keys()):

            data_out = self.sniffer_dictionary[ip]["data_out"]
            data_in = self.sniffer_dictionary[ip]["data_in"]
            total_packets = self.sniffer_dictionary[ip]["packet_count"]

            self.live_table_dictionary[ip].children[
                0
            ].text = f"{self.sniffer_dictionary[ip]['data_out']/1000000:.6f}"
            self.live_table_dictionary[ip].children[
                1
            ].text = f"{self.sniffer_dictionary[ip]['data_in']/1000000:.6f}"
            self.live_table_dictionary[ip].children[2].text = str(total_packets)

            cursor.execute(
                f"""UPDATE OR IGNORE Live SET total_packets = "{total_packets}", data_in = "{data_in}", data_out = "{data_out}" WHERE ip = "{ip}" """
            )

            db.commit()

    def sort_table(self, calling_button: Button) -> None:

        cursor = db.cursor()

        if calling_button.count % 2 == 0:
            cursor.execute(
                f"""SELECT * FROM Live ORDER BY "{calling_button.sorting_key}" DESC"""
            )

        else:
            cursor.execute(
                f"""SELECT * FROM Live ORDER BY "{calling_button.sorting_key}" ASC"""
            )

        calling_button.count += 1

        sorted_ips = cursor.fetchall()

        self.table.clear_widgets()
        self.table_count = 0
        for ip in sorted_ips:

            if (
                self.table_count % 2 == 0
                and ip[0] not in self.malicious_table_dictionary
            ):
                for row_item in self.live_table_dictionary[ip[0]].children:
                    if isinstance(row_item, BoxLayout):
                        row_item.children[1].background_color = (0, 1, 0, 0.8)
                    
                    else:
                        row_item.color = (1, 1, 1, 1)

            elif (
                self.table_count % 2 != 0
                and ip[0] not in self.malicious_table_dictionary
            ):
                for row_item in self.live_table_dictionary[ip[0]].children:
                    if isinstance(row_item, BoxLayout):

                        row_item.children[1].background_color = (0, 1, 0, 0.3)
                    else:
                        row_item.color = (1, 1, 1, 0.7)

            # BUG: when changing sniffers there is a key error
            self.table.add_widget(self.live_table_dictionary[ip[0]])
            self.table_count += 1

    def sort_malicious_table(self, calling_button: Button) -> None:

        cursor = db.cursor()

        if calling_button.count % 2 == 0:
            cursor.execute(
                f"""SELECT * FROM malicious_ips ORDER BY "{calling_button.sorting_key}" DESC"""
            )

        else:
            cursor.execute(
                f"""SELECT * FROM malicious_ips ORDER BY "{calling_button.sorting_key}" ASC"""
            )

        calling_button.count += 1

        sorted_ips = cursor.fetchall()

        self.malicious_table.clear_widgets()
        self.malicious_table_count = 0

        for ip in sorted_ips:

            if self.malicious_table_count % 2 == 0:
                for row_item in self.malicious_table_dictionary[ip[0]].children:
                    if isinstance(row_item, BoxLayout):
                        row_item.children[1].background_color = (0.3, 0.3, 0.3, 1)
                    else:
                        row_item.color = (1, 1, 1, 1)

            else:
                for row_item in self.malicious_table_dictionary[ip[0]].children:
                    if isinstance(row_item, BoxLayout):
                        row_item.children[1].background_color = (0.15, 0.15, 0.15, 1)
                    else:
                        row_item.color = (1, 1, 1, 0.7)

            self.malicious_table.add_widget(self.malicious_table_dictionary[ip[0]])
            self.malicious_table_count += 1

    def set_malicious_view(self, button: Button) -> None:

        """
        Transition screenmanager to malicious view and display appropriate widgets.
        """

        current_view = self.current  # get current screenmanager state

        ##### Clean up previous view
        if current_view == "graph":
            self.graph_view.clear_widgets()

            if self.settings_panel.color_picker_popup_open == True:
                self.persistent_widget_container.remove_widget(
                    self.settings_panel.color_picker_layout
                )

            if self.misc_update_dictionary["my_computer"]:
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["my_computer"].menu_popup
                )

            for country in self.misc_update_dictionary["country"].keys():
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["country"][country].menu_popup
                )

            for city in self.misc_update_dictionary["city"].keys():
                self.persistent_widget_container.remove_widget(
                    self.misc_update_dictionary["city"][city].menu_popup
                )

        elif current_view == "table":
            Clock.unschedule(self.update_table)
            self.table_view.clear_widgets()
        #####

        # Produce malicious view
        # if self.settings_panel.summary_data_popup_open == True:
        #     self.persistent_widget_container.remove_widget(self.settings_panel.summary_data_layout)

        for widget in self.malicious_widgets:
            self.malicious_view.add_widget(widget)

        self.transition.direction = "up"
        self.current = "malicious"  # set screenmanager view

        self.malicious_data_in_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN Color"])}] Data IN (MB)[/color]   {icon("fa-sort", 25)}'

        self.malicious_data_out_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT Color"])}] Data OUT (MB)[/color]   {icon("fa-sort", 25)} '

        Clock.schedule_interval(self.update_malicious_table, 1)

    def update_malicious_table(self, time_delta) -> None:

        cursor = db.cursor()

        for ip in self.malicious_table_dictionary.keys():

            if ip not in self.sniffer_dictionary:
                pass

            else:

                data_out = self.sniffer_dictionary[ip]["data_out"]
                data_in = self.sniffer_dictionary[ip]["data_in"]
                packet_count = self.sniffer_dictionary[ip]["packet_count"]

                self.malicious_table_dictionary[ip].children[
                    0
                ].text = f"{self.sniffer_dictionary[ip]['data_out']/1000000:.6f}"
                self.malicious_table_dictionary[ip].children[
                    1
                ].text = f"{self.sniffer_dictionary[ip]['data_in']/1000000:.6f}"
                self.malicious_table_dictionary[ip].children[2].text = str(packet_count)

                cursor.execute(
                    f"""UPDATE OR IGNORE malicious_ips SET packet_count = "{packet_count}", data_in = "{data_in}", data_out = "{data_out}" WHERE ip = "{ip}" """
                )

                db.commit()

    

    def make_settings_panel(self) -> None:

        """
        Convience function for constructing Settings Panel -- need to construct this first before make_GUI_widgets().
        """

        self.settings_panel = Settings_Panel(resource_path=self.resource_path)
        self.settings_panel.gui_manager = self
        self.settings_panel.init_accordion()

    def turn_mercator_on(self, checkbox: CheckBox, value: bool) -> None:

        if value == True:

            self.graph_view.add_widget(
                self.mercator_container, len(self.graph_view.children) + 1
            )

        else:
            self.graph_view.remove_widget(self.mercator_container)

    def toggle_mercator_position(self, checkbox: CheckBox, value: bool) -> None:

        if value == True:

            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.set_mercator_layout()

                for city in self.country_dictionary[country][1]:
                    city_widget = self.country_dictionary[country][1][city][0]
                    city_widget.set_mercator_layout()

                    for ip_widget in self.country_dictionary[country][1][city][1:]:
                        ip_widget.set_mercator_layout()

        else:

            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.set_graph_layout()

                for city in self.country_dictionary[country][1]:
                    city_widget = self.country_dictionary[country][1][city][0]
                    city_widget.set_graph_layout()

                    for ip_widget in self.country_dictionary[country][1][city][1:]:
                        ip_widget.set_graph_layout()

    def make_GUI_widgets(self) -> None:

        """
        Convience function for constructing all GUI widgets.
        """

        self.widget_container = FloatLayout()
        self.persistent_widget_container = FloatLayout()

        self.persistent_widget_container.add_widget(
            self.settings_panel.connection_label_layout
        )

        # Building menu icons (triggers view changes)
        self.main_settings_icon = self.make_icon(
            image=os.path.join(self.resource_path, "assets/images/UI/shield.png"),
            on_press_toggle=self.settings_panel_toggle,
            icon_pos=self.config_variables_dict["main_settings_icon_pos"],
            identity="main_settings",
        )

        self.table_icon = self.make_icon(
            image=os.path.join(self.resource_path, "assets/images/UI/table_view.png"),
            on_press_toggle=self.set_table_view,
            icon_pos=self.config_variables_dict["table_icon_pos"],
            identity="table_icon",
        )

        self.graph_icon = self.make_icon(
            image=os.path.join(self.resource_path, "assets/images/UI/graph.png"),
            on_press_toggle=self.set_graph_view,
            icon_pos=self.config_variables_dict["graph_icon_pos"],
            identity="graph_icon",
        )

        self.malicious_icon = self.make_icon(
            image=os.path.join(self.resource_path, "assets/images/UI/malicious.png"),
            on_press_toggle=self.set_malicious_view,
            icon_pos=self.config_variables_dict["malicious_icon_pos"],
            identity="malicious_icon",
        )

        # Building Graph Wigets
        self.my_computer = My_Computer(
            id="My Computer",
            window_x=self.window_x,
            window_y=self.window_y,
            gui_manager=self,
            center_position=(self.center_x, self.center_y),
            resource_path=self.resource_path,
        )

        self.mercator_container = Widget()  # for mercator background image
        self.mercator_container.orientation = "horizontal"
        self.mercator_container.id = "mercator-layout"
        self.mercator_container.size = (self.window_x, self.window_y)

        self.mercator_image = Image(
            source=os.path.join(self.resource_path, "assets/images/UI/mercator.png"),
            size_hint=(None, None),
            keep_ratio=False,
            allow_stretch=True,
            size=(self.window_x, self.window_y),
        )

        self.mercator_container.add_widget(self.mercator_image)

        # Building Table  Widgets
        self.table_scroll = ScrollView(
            scroll_distance=50, size_hint_y=self.window_ratio - 0.05, pos=(0, 85)
        )

        self.table = GridLayout(
            size_hint=(None, None),
            col_default_width=self.window_x / 2,
            row_default_height=30,
            cols=1,
            padding=(10, 0),
        )

        self.table.bind(minimum_height=self.table.setter("height"))
        self.table.bind(minimum_width=self.table.setter("width"))

        self.box_header_container = AnchorLayout(anchor_y="top")
        self.box_header = self.create_table_header()

        self.box_header_container.add_widget(self.box_header)
        self.table_scroll.add_widget(self.table)

    def clear_malicious_table(self, *args) -> None:

        """
        Clear malcious_ips table and re-create it.
        """

        cursor = db.cursor()
        cursor.execute("DELETE FROM malicious_ips")
        cursor.execute("VACUUM")

        db.commit()

        self.malicious_table_dictionary.clear()
        self.malicious_table.clear_widgets()

        self.malicious_dropdown.dismiss()

    def open_malicious_dropdown(self, calling_button: Button) -> None:

        """
        Kivy dropdown bug hack
        """

        self.malicious_dropdown.open(calling_button)

    def clear_livetable(self, *args) -> None:

        """ """

        cursor = db.cursor()
        cursor.execute("DELETE FROM Live")
        cursor.execute("VACUUM")

        db.commit()

        # TODO:
        # self.live_table.clear_widgets()
        self.table.clear_widgets()
        self.live_table_dictionary.clear()
        self.livetable_dropdown.dismiss()

    def save_livetable(self, *args) -> None:

        """
        Clear malcious_ips table and re-create it.
        """

        pass

    def open_livetable_dropdown(self, calling_button: Button) -> None:

        """
        Kivy dropdown bug hack
        """

        self.livetable_dropdown.open(calling_button)

    def init_database_(self, session_name):

        """
        Initialize sqlite3 database
        """

        cursor = db.cursor()

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS sessions ( session_name TEXT PRIMARY KEY, session_data dictionary )"
        )

        cursor.execute("DROP TABLE IF EXISTS Live")

        cursor.execute(
            "CREATE TABLE Live (ip TEXT PRIMARY KEY, description TEXT DEFAULT 'NONE', time_stamp TEXT DEFAULT 'NONE', location_city TEXT DEFAULT 'NONE', location_country TEXT DEFAULT 'NONE', longitude INTEGER, latitude INTEGER, total_packets INTEGER DEFAULT 0, data_in INTEGER DEFAULT 0, data_out INTEGER DEFAULT 0, tcp_packets INTEGER DEFAULT 0, udp_packets INTEGER DEFAULT 0, other_packets INTEGER DEFAULT 0, blocked INTEGER DEFAULT 0, safe_listed INTEGER DEFAULT 0, flagged INTEGER DEFAULT 0)"
        )

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS malicious_ips (ip TEXT PRIMARY KEY, description TEXT DEFAULT 'NONE', ban_lists INTEGER DEFAULT 0, time_stamp TEXT DEFAULT 'NONE',location_country TEXT DEFAULT 'NONE', packet_count INTEGER DEFAULT 0, data_in INTEGER DEFAULT 0, data_out INTEGER DEFAULT 0,  ip_data dictionary)"
        )

        cursor.execute("SELECT * from malicious_ips")
        malicious_ips = cursor.fetchall()

        # TODO:find a better place to make these. ##########################################
        self.malicious_ip_scroll = ScrollView(
            scroll_distance=50,
            size_hint_y=self.window_ratio - 0.05,
            size_hint_x=1,
            pos=(0, 85),
        )

        ###############################

        self.livetable_dropdown = DropDown()

        clear_livetable_button = Button(
            text="Save Table",
            size_hint=(None, None),
            width=dp(200),
            height=dp(25),
            background_color=(0, 0, 0, 1),
            on_press=self.save_livetable,
        )

        self.livetable_dropdown.add_widget(clear_livetable_button)

        livetable_menu_button = Button(
            text="Menu",
            pos=(self.center_x - dp(100), dp(5)),
            size_hint=(None, None),
            size=(dp(200), dp(25)),
            background_color=(1, 1, 1, 0.3),
        )

        livetable_menu_button.bind(on_press=self.open_livetable_dropdown)

        self.livetable_menu = FloatLayout()
        self.livetable_menu.add_widget(livetable_menu_button)

        ####################################

        # TODO:put these somewhere else
        self.malicious_dropdown = DropDown()

        malicious_dropdown_button = Button(
            text="Clear Table",
            size_hint=(None, None),
            width=dp(200),
            height=dp(25),
            background_color=(0, 0, 0, 1),
            on_press=self.clear_malicious_table,
        )

        self.malicious_dropdown.add_widget(malicious_dropdown_button)

        malicious_menu_button = Button(
            text="Menu",
            pos=(self.center_x - dp(100), dp(5)),
            size_hint=(None, None),
            size=(dp(200), dp(25)),
            background_color=(1, 1, 1, 0.3),
        )
        malicious_menu_button.bind(on_press=self.open_malicious_dropdown)

        self.malicious_menu = FloatLayout()
        self.malicious_menu.add_widget(malicious_menu_button)

        self.malicious_table = GridLayout(
            size_hint=(None, None),
            col_default_width=self.window_x,
            row_default_height=30,
            cols=1,
            padding=(10, 0),
        )
        self.malicious_table.bind(minimum_height=self.malicious_table.setter("height"))
        self.malicious_table.bind(minimum_width=self.malicious_table.setter("width"))

        self.malicious_ip_container = AnchorLayout(anchor_y="top", anchor_x="left")
        self.malicious_ip_header = self.create_malicious_header()

        self.malicious_ip_scroll.add_widget(self.malicious_table)
        self.malicious_ip_container.add_widget(self.malicious_ip_header)
        ######################################################################################

        for ip in malicious_ips:
            self.malicious_ips_local_database[ip[0]] = ip[2]
            malicious_row = self.generate_malicious_table_row(ip)
            self.malicious_table_dictionary[ip[0]] = malicious_row
            self.malicious_table.add_widget(malicious_row)

        db.commit()

    def generate_malicious_table_row(self, ip_data: tuple) -> BoxLayout:

        """
        Construct a row for Malicious view
        """

        length_per_label = self.window_x / 6

        box_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            pos=(0, 0),
            padding=1,
            size=(self.window_x, dp(20)),
        )

        ip_button = Button()
        ip_button.text = ip_data[0]
        ip_button.id = ip_data[0]
        ip_button.on_press = lambda ip=ip_data[0], description=ip_data[1]: self.ip_button_display(ip, description)

        if self.malicious_table_count % 2 == 0:
            ip_button.background_color = (0.3, 0.3, 0.3, 1)
            ip_button.color = (1, 0, 0, 1)
            text_color = (1, 1, 1, 1)

        else:
            ip_button.background_color = (0.15, 0.15, 0.15, 1)
            ip_button.color = (1, 0, 0, 1)
            text_color = (1, 1, 1, 0.7)

        self.malicious_table_count += 1

        description_label = self.make_label(ip_data[1], length_per_label)
        description_label.color = text_color

        banlist_count_label = self.make_label(str(ip_data[2]), length_per_label)
        banlist_count_label.color = text_color

        timestamp_label = self.make_label(ip_data[3], length_per_label)
        timestamp_label.color = text_color

        country_label = self.make_label(ip_data[4], length_per_label)
        country_label.color = text_color

        packet_label = self.make_label(str(ip_data[5]), length_per_label)
        packet_label.color = text_color

        data_in_label = self.make_label(f"{ip_data[6]/1000000:.6f}", length_per_label)
        data_in_label.color = text_color

        data_out_label = self.make_label(f"{ip_data[7]/1000000:.6f}", length_per_label)
        data_out_label.color = text_color

        ip_button_container = BoxLayout(orientation="horizontal")
        ip_button_container.add_widget(Label(size_hint_x=0.1))
        ip_button_container.add_widget(ip_button)
        ip_button_container.add_widget(Label(size_hint_x=0.1))

        box_layout.add_widget(ip_button_container)
        box_layout.add_widget(description_label)
        box_layout.add_widget(banlist_count_label)
        box_layout.add_widget(timestamp_label)
        box_layout.add_widget(country_label)
        box_layout.add_widget(packet_label)
        box_layout.add_widget(data_in_label)
        box_layout.add_widget(data_out_label)

        return box_layout

    def ip_button_display(self, ip_key: str, *ip_description: str) -> None:

        """
        Display IP widget menu or popup when IP widget doesn't exist for the session.  (for malicious view)
        """

        if ip_key in self.ip_dictionary:  # IP_widget exists so use its member function
            ip_obj = self.ip_dictionary[ip_key]
            ip_obj.display_menu()

        else:  # IP_widget doesn't exists, so create a menu item for malicious IP options

            grid_layout = GridLayout()
            grid_layout.cols = 1

            malicious_ip_popup = Popup(
                title="This will not effect the curated banlist from the Internet",
                content=grid_layout,
                size_hint=(None, None),
                size=(sp(400), sp(175)),
                auto_dismiss=True,
            )

            # self.persistent_widget_container.add_widget(self.malicious_ip_popup)

            ip = Label()
            ip.text = ip_key

            ip_info = Label()
            ip_info.text = str(ip_description[0])

            unblock_button = Button()
            unblock_button.text = "Remove from Local Malicious Database"
            unblock_button.on_press = lambda ip=ip_key, popup=malicious_ip_popup: self.remove_from_local_malicious_database(
                ip, popup
            )
            unblock_button.background_normal = os.path.join(
                self.resource_path, "assets/images/buttons/green.png"
            )
            unblock_button.background_down = os.path.join(
                self.resource_path, "assets/images/buttons/green_down.png"
            )

            grid_layout.add_widget(ip)
            grid_layout.add_widget(ip_info)
            grid_layout.add_widget(Label(size_hint_y=0.5))
            grid_layout.add_widget(unblock_button)
            malicious_ip_popup.open()

    def remove_from_local_malicious_database(self, ip, popup) -> None:

        """
        Remove IP entry from malicious_ips database table.
        """

        cursor = db.cursor()
        cursor.execute(f"""DELETE FROM malicious_ips WHERE ip='{ip}' """)

        self.malicious_table.remove_widget(self.malicious_table_dictionary[ip])
        popup.dismiss()

    def create_table_header(self) -> BoxLayout:

        """
        Convience function for creating table header - view 3.
        """

        register(
            "default_font",
            os.path.join(self.resource_path, "assets/fonts/fontawesome-webfont"),
            os.path.join(self.resource_path, "assets/fonts/font-awesome.fontd"),
        )

        box = BoxLayout(
            orientation="horizontal",
            pos_hint=(None, None),
            size_hint=(None, 0.04),
            size=(self.window_x, 0),
        )

        self.ip_label_header = Button()
        self.ip_label_header.text = f'IP Address   {icon("fa-sort", 25)}'
        self.ip_label_header.sorting_key = "ip"
        self.ip_label_header.background_color = (0.3, 0.3, 0.3, 0.7)
        self.ip_label_header.on_press = lambda: self.sort_table(
            calling_button=self.ip_label_header
        )
        self.ip_label_header.count = 0
        self.ip_label_header.markup = True

        description_button = Button()
        description_button.text = f'Description   {icon("fa-sort", 25)}'
        description_button.sorting_key = "description"
        description_button.on_press = lambda: self.sort_table(
            calling_button=description_button
        )
        description_button.background_color = (0.3, 0.3, 0.3, 0.7)
        description_button.count = 0
        description_button.markup = True

        city_button = Button()
        city_button.text = f'City   {icon("fa-sort", 25)}'
        city_button.sorting_key = "location_city"
        city_button.on_press = lambda: self.sort_table(calling_button=city_button)
        city_button.background_color = (0.3, 0.3, 0.3, 0.7)
        city_button.count = 0
        city_button.markup = True

        country_button = Button()
        country_button.text = f'Country   {icon("fa-sort", 25)}'
        country_button.sorting_key = "location_country"
        country_button.on_press = lambda: self.sort_table(calling_button=country_button)
        country_button.background_color = (0.3, 0.3, 0.3, 0.7)
        country_button.count = 0
        country_button.markup = True

        packets_button = Button()
        packets_button.text = f'Total Packets   {icon("fa-sort", 25)}'
        packets_button.sorting_key = "total_packets"
        packets_button.on_press = lambda: self.sort_table(calling_button=packets_button)
        packets_button.background_color = (0.3, 0.3, 0.3, 0.7)
        packets_button.count = 0
        packets_button.markup = True

        self.live_data_in_button = Button()
        self.live_data_in_button.markup = True
        # self.live_data_in_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN Color"])}] Data IN (MB) [/color]'
        self.live_data_in_button.sorting_key = "data_in"
        self.live_data_in_button.on_press = lambda: self.sort_table(
            calling_button=self.live_data_in_button
        )
        self.live_data_in_button.background_color = (0.3, 0.3, 0.3, 0.7)
        self.live_data_in_button.count = 0

        self.live_data_out_button = Button()
        self.live_data_out_button.markup = True
        # self.live_data_out_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT Color"])}] Data OUT (MB) [/color]'
        self.live_data_out_button.sorting_key = "data_out"
        self.live_data_out_button.on_press = lambda: self.sort_table(
            calling_button=self.live_data_out_button
        )
        self.live_data_out_button.background_color = (0.3, 0.3, 0.3, 0.7)
        self.live_data_out_button.count = 0

        box.add_widget(self.ip_label_header)
        box.add_widget(description_button)
        box.add_widget(city_button)
        box.add_widget(country_button)
        box.add_widget(packets_button)
        box.add_widget(self.live_data_in_button)
        box.add_widget(self.live_data_out_button)

        return box

    def create_malicious_header(self) -> BoxLayout:

        """
        Convience function for building malicious header - view 4.
        """

        box = BoxLayout(
            orientation="horizontal",
            pos_hint=(None, None),
            size_hint=(None, 0.04),
            size=(self.window_x, 0),
        )

        self.malcious_ip_label_header = Button()
        self.malcious_ip_label_header.text = (
            f'[color=FF0000]Malicious IP[/color]   {icon("fa-sort", 25)}'
        )
        self.malcious_ip_label_header.sorting_key = "ip"
        self.malcious_ip_label_header.background_color = (0.3, 0.3, 0.3, 0.8)
        self.malcious_ip_label_header.count = 0
        self.malcious_ip_label_header.on_press = lambda: self.sort_malicious_table(
            calling_button=self.malcious_ip_label_header
        )
        self.malcious_ip_label_header.markup = True

        description_button = Button()
        description_button.text = (
            f'[color=FF0000]Description[/color]   {icon("fa-sort", 25)}'
        )
        description_button.sorting_key = "description"
        description_button.on_press = lambda: self.sort_malicious_table(
            calling_button=description_button
        )
        description_button.background_color = (0.3, 0.3, 0.3, 0.8)
        description_button.count = 0
        description_button.markup = True

        ban_lists_button = Button()
        ban_lists_button.text = (
            f'[color=FF0000]Confidence Score[/color]   {icon("fa-sort", 25)}'
        )
        ban_lists_button.sorting_key = "ban_lists"
        ban_lists_button.on_press = lambda: self.sort_malicious_table(
            calling_button=ban_lists_button
        )
        ban_lists_button.background_color = (0.3, 0.3, 0.3, 0.8)
        ban_lists_button.count = 0
        ban_lists_button.markup = True

        time_stamp_button = Button()
        time_stamp_button.text = (
            f'[color=FF0000]Last Packet[/color]   {icon("fa-sort", 25)}'
        )
        time_stamp_button.sorting_key = "time_stamp"
        time_stamp_button.on_press = lambda: self.sort_malicious_table(
            calling_button=time_stamp_button
        )
        time_stamp_button.background_color = (0.3, 0.3, 0.3, 0.8)
        time_stamp_button.count = 0
        time_stamp_button.markup = True

        country_button = Button()
        country_button.text = f'[color=FF0000]Country[/color]   {icon("fa-sort", 25)}'
        country_button.sorting_key = "location_country"
        country_button.on_press = lambda: self.sort_malicious_table(
            calling_button=country_button
        )
        country_button.background_color = (0.3, 0.3, 0.3, 0.8)
        country_button.count = 0
        country_button.markup = True

        packets_button = Button()
        packets_button.text = (
            f'[color=FF0000]Total Packets[/color]   {icon("fa-sort", 25) }'
        )
        packets_button.sorting_key = "packet_count"
        packets_button.on_press = lambda: self.sort_malicious_table(
            calling_button=packets_button
        )
        packets_button.background_color = (0.3, 0.3, 0.3, 0.8)
        packets_button.count = 0
        packets_button.markup = True

        self.malicious_data_in_button = Button()
        self.malicious_data_in_button.markup = True
        # self.malicious_data_in_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN Color"])}] Data IN (MB) [/color]'
        self.malicious_data_in_button.sorting_key = "data_in"
        self.malicious_data_in_button.on_press = lambda: self.sort_malicious_table(
            calling_button=self.malicious_data_in_button
        )
        self.malicious_data_in_button.background_color = (0.3, 0.3, 0.3, 0.8)
        self.malicious_data_in_button.count = 0

        self.malicious_data_out_button = Button()
        self.malicious_data_out_button.markup = True
        # self.malicious_data_out_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT Color"])}] Data OUT (MB) [/color]'
        self.malicious_data_out_button.sorting_key = "data_out"
        self.malicious_data_out_button.on_press = lambda: self.sort_malicious_table(
            calling_button=self.malicious_data_out_button
        )
        self.malicious_data_out_button.background_color = (0.3, 0.3, 0.3, 0.8)
        self.malicious_data_out_button.count = 0

        box.add_widget(self.malcious_ip_label_header)
        box.add_widget(description_button)
        box.add_widget(ban_lists_button)
        box.add_widget(time_stamp_button)
        box.add_widget(country_button)
        box.add_widget(packets_button)
        box.add_widget(self.malicious_data_in_button)
        box.add_widget(self.malicious_data_out_button)

        return box

    def make_icon(
        self, image: str, on_press_toggle: Callable, icon_pos: int, identity: str
    ) -> FloatLayout:

        """
        Convience function for creating menu GUI icons with layered positioning.
        """

        position = [icon_pos[0], icon_pos[1]]

        icon_scatter_widget = Scatter(
            size_hint=(None, None), pos=position, size=(dp(40), dp(40))
        )

        with icon_scatter_widget.canvas.before:
            Color(1, 1, 1, 0.1)
            RoundedRectangle(
                size=icon_scatter_widget.size,
                pos=(0, 0),
                radius=[
                    (dp(60), dp(50)),
                    (dp(50), dp(50)),
                    (dp(50), dp(50)),
                    (dp(50), dp(50)),
                ],
            )

        container = FloatLayout()
        container.pos = position
        container.size_hint = (None, None)
        container.size = ("40sp", "40sp")
        container.id = identity

        icon_image = Image(
            source=image,
            size_hint=(None, None),
            pos=("5sp", "5sp"),
            size=("30sp", "30sp"),
        )

        toggle_button = Button(
            on_press=on_press_toggle,
            size_hint=(None, None),
            size=("20sp", "20sp"),
            pos=("10sp", "10sp"),
            background_color=(0, 0, 0, 0),
        )

        toggle_button.add_widget(icon_image)
        icon_scatter_widget.add_widget(toggle_button)
        container.add_widget(icon_scatter_widget)

        return container

    def make_label(self, text: str, length_per_label: float) -> Label:

        """
        Convience function to make kivy Labels with specified length.
        """

        custom_label = Label()
        custom_label.halign = "center"
        custom_label.text_size = (length_per_label, 20)
        custom_label.valign = "middle"
        custom_label.markup = True
        custom_label.shorten = True
        custom_label.text = text

        return custom_label

    def settings_panel_toggle(self, *button: Button) -> None:

        """
        Toggle settings menu on/off.
        """

        if self.settings_toggle_boolean == True:
            self.persistent_widget_container.remove_widget(
                self.settings_panel.settings_panel_scatter
            )
            self.settings_toggle_boolean = False

        else:
            self.persistent_widget_container.add_widget(
                self.settings_panel.settings_panel_scatter
            )
            self.settings_toggle_boolean = True

    def mercator_coordinates(
        self, longitude: float, latitude: float
    ) -> tuple[float, float]:

        """
        Given global longitude and latitude return screen x and y position
        """

        if (
            longitude == "Unresolved"
        ):  # No latitude or longitude information, use default
            return self.center_x / 2 - 25, 40

        x, y = self.projection(longitude - 11, latitude)  # x,y in meters

        px = self.center_x + x * self.x_pixels_per_meter  # x in pixels
        py = self.center_y + y * self.y_pixels_per_meter  # y in pixels

        return px, py

    def close(self) -> None:

        """
        GUI_Manager closing cleanup function.
        """

        cursor = db.cursor()
        cursor.execute("DROP TABLE IF EXISTS Live")
        db.commit()

        # TODO:create pos dictionary
        self.config_variables_dict["main_settings_icon_pos"] = self.main_settings_icon.children[0].pos
        self.config_variables_dict["graph_icon_pos"] = self.graph_icon.children[0].pos
        self.config_variables_dict["table_icon_pos"] = self.table_icon.children[0].pos
        self.config_variables_dict["malicious_icon_pos"] = self.malicious_icon.children[0].pos
        self.config_variables_dict["connection_label_pos"] = self.settings_panel.connection_label_scatter.pos
        self.config_variables_dict["settings_panel_pos"] = self.settings_panel.settings_panel_scatter.pos
        self.config_variables_dict["computer_menu_pos"] = self.my_computer.menu_popup.pos

        self.config_variables_dict["country_labels"] = self.country_labels
        self.config_variables_dict["city_labels"] = self.city_labels
        self.config_variables_dict["ip_labels"] = self.ip_labels
        self.config_variables_dict["my_computer"]["my_label"] = self.my_computer.mylabel_bool

        self.config_variables_dict["my_computer"]["mercator_position"] = self.my_computer.mercator_position
        self.config_variables_dict["my_computer"]["graph_position"] = self.my_computer.graph_position
        self.config_variables_dict["initalize"] = True

        if self.settings_panel.auto_connect_checkbox.active == True:
            self.config_variables_dict["auto_connect"] = True
        else:
            self.config_variables_dict["auto_connect"] = False

        # Save configuations
        with open(
            os.path.join(self.resource_path, "configuration/config.json"), "w"
        ) as configuration_file:
            json.dump(self.config_variables_dict, configuration_file)

        # Save cached IP whois information
        with open(
            os.path.join(self.resource_path, "assets/database/whois.json"), "w"
        ) as ip_whois_info_file:
            json.dump(self.ip_whois_info_dict.copy(), ip_whois_info_file)
