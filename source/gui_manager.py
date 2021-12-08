# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.


import sys
import os
import time
import netifaces
import threading
import json
import ast
import atexit                           # program exit cleanup
import sqlite3                          # Database - store banned countires/ip's and sessions
import pygeoip                          # ip geolocation
import zmq                              # Networking - client/server and publish/subscribe patterns
import zmq.auth                         #TODO: authorize who can connect
from typing import Callable
from random import random
from requests import get                #used to identiy sniffer external facing IP
import ipwhois
from ipwhois import IPWhois             # IP description and abuse emails
from pyproj import Proj                 # Mercator projection: latitude and longitude --> screen x and y coordinates 
from uuid import getnode as get_mac     #identify hardware mac address
from importlib import reload            #Dynamic code reloading
from multiprocessing import Process     #Used to run local sniffer as new process
from network_sniffer import Sniffer     #Class that parses network packets and sends to the visualizer
from utils import map_to_range, angle_between_points, country_lat_long #dictionary to look up all the countries latitude and longitude

#Considered using these to run whois lookups async. Didn't see any performance benefit over just running in a seperate thread. May try again later.. 
#import asyncio
#from concurrent.futures import ThreadPoolExecutor


from kivy.core.window import Window
from kivy.clock import Clock
from kivy.metrics import sp
from kivy.utils import get_hex_from_color

from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.progressbar import ProgressBar





###################################################################
#Dynamic Reloading - reload code without having to restart the program. Saves time not having to restart the program while developing. 
#There is an issue with exception handling since upgrading to python3~. I use visual studio to catch exception that are silenced when running directly from terminal. Not sure why this is so.. 


try:
    import database_config
    reload(database_config)
    from database_config import *

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broken in database_config.py")


try:
    import widgets.computer_widget 
    reload(widgets.computer_widget )
    from widgets.computer_widget  import My_Computer

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broken in computer_widget.py")


try: 
    import widgets.country_widget
    reload(widgets.country_widget)
    from widgets.country_widget import Country_Widget

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in country_widget.py")


try: 
    import widgets.city_widget
    reload(widgets.city_widget)
    from widgets.city_widget import City_Widget
    
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in city_widget.py")


try: 
    import widgets.ip_widget
    reload(widgets.ip_widget)
    from widgets.ip_widget import IP_Widget

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in ip_widget.py")


try: 
    import settings_panel
    reload(settings_panel)
    from settings_panel import  Settings_Panel

except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print(exc_type, fname, exc_tb.tb_lineno)
    print("Code broke in settings_panel.py")

########################################################################






class GUI_Manager(ScreenManager): 

    """
    GUI_Manager runs the show. This class stores program state, update loops, data structures, and anything else used for the visualizer.
    """

    def __init__(self, **kwargs):
        super().__init__()

        self.kivy_application = kwargs["kivy_application"]


        #Load saved configuration
        with open('../configuration/config.json', 'r+') as configuration_file:
            self.config_variables_dict = json.load(configuration_file)
           
        #Load cached IP whois information
        with  open('../assets/database/whois.json', 'r+') as ip_whois_info_file:
            self.ip_whois_info_dict = json.load(ip_whois_info_file)
  

        self.scale_factor_height = Window.size[0] / 4064.0 #calculated using original x dimension from development display
        if self.scale_factor_height < .8: self.scale_factor_height = .8
        self.scale_factor_width = Window.size[1] / 2258.0 #calculated using original y dimension from development display
        if self.scale_factor_width < .8: self.scale_factor_width = .8

        self.scale_array = [self.scale_factor_height, self.scale_factor_width ]


        self.window_x = Window.size[0] 
        self.window_y = Window.size[1]
        self.center_x = self.window_x/2
        self.center_y = self.window_y/2 
        self.window_ratio = (self.window_y-75.0) / (self.window_y)

        self.session_name = '' 
        self.session_query = ''

        self.x_pixels_per_meter = self.window_x / 40030000.0 #circumfrence of earth in meters (around equator)
        self.y_pixels_per_meter = self.window_y / 18500000.0 #circumfrence/2 of earth in meters (from pole to pole) 
       
        
        

        self.ip_total_count = 1 
        self.city_total_count = 1
        self.country_total_count = 1
        self.ip_largest_data_in = 1000 
        self.ip_largest_data_out = 1000
        self.city_largest_data_out = 1000
        self.city_largest_data_in = 1000
        self.country_largest_data_out = 1000
        self.country_largest_data_in = 1000


        #Data Structures - See data structure documentation for proper use. 
        self.country_dictionary = {} # Contains all the created GUI widgets (country, city, ip) in heirarchy. 
        self.interface_dictionary = {} # Contains networking interface information
        self.ip_dictionary = {} # Containes all the ip widgets
        self.sniffer_dictionary = {} # Data from sniffer
        self.banned_ips_array = [] # Stores the banned ip's. TODO:convert to dictionary
        self.iptables_list = [] #rules from iptables (already in the system) - populated at startup in init_database_()
        self.built_table = {} #convience dictionary to quickly lookup if IP is in database
        self.todo_ip_whois_array = [] #array container for batch IP whois lookup
        
        self.settings_toggle_on = False
        self.database_in_action = False
        self.generate_table_init_bool = False

        #variables to be populated
        self.sniffer_process = None
        self.data_socket = None #ZMQ publish/subscribe pattern
        self.server_socket = None #ZMQ client/server pattern
        self.sniffer_ip = None
        self.ip_whois_thread = None


        self.my_mac_address = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2)) #store MAC address
        self.ip_database_lookup = pygeoip.GeoIP("../assets/geolocation/GeoLiteCity.dat") #ip gelocation 
        self.projection = Proj(init='epsg:32663') #equirectangular projection (plate) on WGS84 (for mercator view) http://spatialreference.org/ref/epsg/wgs-84-plate-carree/
                                                  

        #convience functions to cleanup the constructor
        self.populate_network_interfaces()
        self.init_database_(self.session_name)
        self.make_settings_panel()
        if self.config_variables_dict["auto_connect"] == True: self.setup_sniffer_communication() 
        self.make_GUI_widgets()
        self.initalize_ip_from_sniffer() 

        
        #Array of widgets for each Kivy Screenmanager view. When Sreenmanager switches views, the appropriate container of widgets is added/removed. 
        #add widgets to these containers to populate them for the appropriate view. (Create a new array of widgets for a new view)

        #graph_view container
        self.graph_widgets = [ 
                                self.widget_container, 
                                self.my_computer, 
                                self.main_settings_icon, 
                                self.mercator_icon, 
                                self.table_icon,
                                self.banned_icon,
                                self.persistent_widget_container
                             ]

        #mercator_view container
        self.mercator_widgets = [  
                                    self.mercator_container,
                                    self.widget_container,
                                    self.my_computer,
                                    self.graph_icon, 
                                    self.main_settings_icon, 
                                    self.table_icon,
                                    self.banned_icon,
                                    self.persistent_widget_container
                                ]

        #table_view container
        self.table_widgets = [  
                                self.table_scroll, 
                                self.select_data_label,
                                self.box_header_container, 
                                self.update_table_button, 
                                self.update_table_button_live, 
                                self.graph_icon, 
                                self.main_settings_icon, 
                                self.mercator_icon,
                                self.banned_icon,
                                self.persistent_widget_container,
                                self.session_label
                             ]

        #banned_view container
        self.banned_widgets = [    
                                   self.ip_scroll,
                                   self.banned_ip_container,
                                   self.clear_banned_ips_button,
                                   self.persistent_widget_container,
                                   self.graph_icon, 
                                   self.main_settings_icon, 
                                   self.table_icon,
                                   self.mercator_icon,
                              ]

    
        #Views created for ScreenManager - Graph, Mercator, Table, and Banned
        self.graph_view = Screen(name='graph')
        self.mercator_view = Screen(name = 'mercator')
        self.table_view = Screen(name='table')
        self.banned_view = Screen(name='banned')
        
        self.add_widget(self.graph_view)
        self.add_widget(self.mercator_view)
        self.add_widget(self.table_view)
        self.add_widget(self.banned_view)
 

        self.current = "graph" # self.current is the variable name used by ScreenManager to select the view (see kivy docs)
        self.set_graph_view() # start graph view on startup #TODO: give option to set default view
        

        Clock.schedule_interval(self.update_gui, 1/60) # Main program loop to update GUI widget
        Clock.schedule_interval(self.update_from_sniffer, 1) # Update data from sniffer --> self.sniffer_dictionary
        Clock.schedule_interval(self.ip_whois_lookup, 10) # Batch lookup of IP whois 

    # End of GUI_Manager constructor



    def setup_sniffer_communication(self):
        
        """
        Setup ZMQ client/server and pub/sub sockets. If LocalHost, start Sniffer as new process. 
        """
        

        if self.config_variables_dict["auto_connect"] == True and self.config_variables_dict["connect_to"] == "localhost": 

            self.settings_panel.checkbox_local.active = True
            
            keywords = {"port": self.config_variables_dict["local_port"]}
            self.sniffer_process = Process(name= 'sniffer', target=Sniffer, kwargs=keywords) #start sniffer as new process for localhost condition
            self.sniffer_process.start()
            atexit.register(self.sniffer_process.close) #register sniffer cleanup function
            
            sniffer_port = self.config_variables_dict["local_port"]
            sniffer_subscribe_port = sniffer_port + 1

            connect_string_sniffer = f"tcp://localhost:{sniffer_port}"
            connect_string_subscribe = f"tcp://localhost:{sniffer_subscribe_port}"


        elif self.config_variables_dict["auto_connect"] == True and self.config_variables_dict["connect_to"] == "remotehost":

            self.settings_panel.checkbox_remote.active = True

            remote_ip = self.config_variables_dict["remote_ip"][0]
            remote_sniffer_port = self.config_variables_dict["remote_ip"][1]
            remote_subscribe_port = remote_sniffer_port + 1

            connect_string_sniffer = f"tcp://{remote_ip}:{remote_sniffer_port}"
            connect_string_subscribe = f"tcp://{remote_ip}:{remote_subscribe_port}"


        try:         
            context = zmq.Context()
        
            keys = zmq.auth.load_certificate('../configuration/keys/client.key_secret')
            server_key, _ = zmq.auth.load_certificate('../configuration/keys/server.key')
    
            self.server_socket = context.socket(zmq.REQ) #client/server pattern for message passing
            self.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.server_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.server_socket.connect(connect_string_sniffer)    
        
            self.data_socket = context.socket(zmq.SUB) #PUB/SUB pattern for sniffer data
            self.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")     
            self.data_socket.connect(connect_string_subscribe)

        except Exception as e:
            print("Issue setting up ZMQ sockets")
            self.kivy_application.get_running_app().stop() #Do we want to shutdown the application if program can't setup ZMQ sockets? 

    
        

      
    def initalize_ip_from_sniffer(self) -> None:

        """
        Query Sniffer to setup outward facing IP and set my_computer.mercator_position
        """

        if self.sniffer_process is not None: 

            self.server_socket.send(b'ip_info')
            encoded_ip = self.server_socket.recv()
            self.sniffer_ip = encoded_ip.decode("utf-8")

            my_ip_info = self.ip_database_lookup.record_by_addr(self.sniffer_ip)
            self.interface_dictionary[self.sniffer_ip] = my_ip_info
            screen_x, screen_y = self.mercator_coordinates(my_ip_info['longitude'], my_ip_info['latitude'])
            self.my_computer.mercator_position = (screen_x, screen_y)


    def update_gui(self, time_delta: tuple) -> None:        
        
        """
        Main Program Loop for updating GUI widgets based on current view (graph, mercator, table, etc)
        """  

        data_out_accumulator = 0 
        data_in_accumulator = 0 

        data_in_color = get_hex_from_color(self.config_variables_dict["Data IN"])
        data_out_color = get_hex_from_color(self.config_variables_dict["Data OUT"])


        if self.current == 'graph': #Start graph loop

            self.widget_container.clear_widgets()
            self.my_computer.update(state='graph')

            

            for country in self.country_dictionary: #Start of Country loop

                country_data_in_accumulator = 0 
                country_data_out_accumulator = 0 
                country_new_data = False 

                country_widget = self.country_dictionary[country][0] 
                country_total_city_widgets = len(self.country_dictionary[country][1]) #len(City dictionary) 
                country_widget.total_city_widgets = country_total_city_widgets

                country_draw_angle = angle_between_points(self.my_computer.icon_scatter_widget.pos, country_widget.icon_scatter_widget.pos)
                country_widget.country_draw_angle = country_draw_angle
                


                for city_index, city in enumerate(self.country_dictionary[country][1]): #Start of City loop

                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0  
                    city_new_data = False 
                    
                    city_widget = self.country_dictionary[country][1][city][0] 
                    city_number_of_ips = len(self.country_dictionary[country][1][city]) - 1 
                    city_draw_angle = angle_between_points(country_widget.icon_scatter_widget.pos, city_widget.icon_scatter_widget.pos)
                    

                    for ip_index, ip_widget in enumerate(self.country_dictionary[country][1][city][1:]): #Start of IP loop

                        if ip_widget.new_data == True: #check ip for new data then set flag
                            city_new_data = True


                        city_data_in_accumulator += ip_widget.ip_data['data_in']
                        city_data_out_accumulator += ip_widget.ip_data['data_out']
                

                        if ip_widget.ip_data['data_in'] > self.ip_largest_data_in:
                            self.ip_largest_data_in = ip_widget.ip_data['data_in']

                        if ip_widget.ip_data['data_out'] > self.ip_largest_data_out:
                            self.ip_largest_data_out = ip_widget.ip_data['data_out']

                        if ip_widget.show == True:

                            ip_widget.update( attach = city_widget.attach, 
                                       city_widget = city_widget,
                                       city_number_of_ips = city_number_of_ips,
                                       city_draw_angle = city_draw_angle,
                                       ip_index = ip_index,
                                       last_packet = ip_widget.ip_data['last_packet'],
                                       state = 'graph'
                                      )
                        
                            self.widget_container.add_widget(ip_widget)
            
                        # End of IP loop


                    
                    # Continue City loop
                
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

                        city_widget.update( attach = country_widget.attach, 
                                            city_index = city_index,
                                            country_draw_angle = country_draw_angle,
                                            country_widget = country_widget,
                                            number_of_cities = country_total_city_widgets,
                                            state = 'graph'
                                            )
                        self.widget_container.add_widget(city_widget)

                    # End of City loop

                        
                # Continue Country loop 

                country_widget.total_city_widgets = city_index
                country_widget.new_data = country_new_data

                country_widget.total_data_in = country_data_in_accumulator
                country_widget.total_data_out = country_data_out_accumulator

                if country_data_in_accumulator > self.country_largest_data_in:
                    self.country_largest_data_in = country_data_in_accumulator


                if country_data_out_accumulator > self.country_largest_data_out:
                    self.country_largest_data_out = country_data_out_accumulator

                data_out_accumulator += country_data_out_accumulator
                data_in_accumulator += country_data_in_accumulator

                if country_widget.show == True:

                        country_widget.update( state = 'graph',
                                               attach = self.my_computer.attach,
                                             )

                        self.widget_container.add_widget(country_widget)

                # End of Country loop

            # Continue Graph loop

            self.my_computer.total_data_out  = data_out_accumulator 
            self.my_computer.total_data_in = data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of Graph loop



        elif self.current == 'mercator': #Start Mercator loop

            self.widget_container.clear_widgets()
            self.my_computer.update(state='mercator')
            
            for country_index, country in enumerate(self.country_dictionary): # Begin Country Loop

                country_data_in_accumulator = 0 
                country_data_out_accumulator = 0
                country_new_data = False

                country_widget = self.country_dictionary[country][0]

                for city_index, city in enumerate(self.country_dictionary[country][1]): # Begin City Loop
                    
                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0
                    city_new_data = False
                    city_widget = self.country_dictionary[country][1][city][0]
                    city_number_of_ips = len(self.country_dictionary[country][1][city]) - 1

                    for ip_index, ip_widget in enumerate(self.country_dictionary[country][1][city][1:]): # Begin IP loop
                        
                        if ip_widget.ip_data['data_in'] > self.ip_largest_data_in:
                            self.ip_largest_data_in = ip_widget.ip_data['data_in']

                        if ip_widget.ip_data['data_out'] > self.ip_largest_data_out:
                            self.ip_largest_data_out = ip_widget.ip_data['data_out']

                        city_data_in_accumulator += ip_widget.ip_data['data_in']
                        city_data_out_accumulator += ip_widget.ip_data['data_out']

                        
                        if ip_widget.new_data == True:
                            city_new_data = True
                            
                        if ip_widget.mercator_show == True:

                            ip_widget.update(
                                        state = 'mercator',
                                        ip_index = ip_index, 
                                        city_number_of_ips = city_number_of_ips,
                                        last_packet = ip_widget.ip_data['last_packet'],
                                        city_widget = city_widget
                                        )

                            self.widget_container.add_widget(ip_widget)

                        # End of IP loop

                    # Continue City loop

                    city_widget.total_data_out = city_data_out_accumulator
                    city_widget.total_data_in = city_data_in_accumulator

                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    city_widget.new_data = city_new_data

                    if city_new_data == True:
                        country_new_data = True


                    if city_widget.mercator_show == True:

                        city_widget.update(index = city_index,
                                           state='mercator'
                                          )

                        self.widget_container.add_widget(city_widget)

                    # End of City loop


                
                # Continue Country loop

                country_widget.new_data = country_new_data

                country_widget.total_data_in = country_data_in_accumulator
                country_widget.total_data_out = country_data_out_accumulator

                data_out_accumulator += country_data_out_accumulator
                data_in_accumulator += country_data_in_accumulator

                if country_widget.mercator_show == True:

                    country_widget.update( country_index = country_index,
                                           state = 'mercator'
                                         )

                    self.widget_container.add_widget(country_widget)

                # End of Country loop


            # Continue Mercator loop

            self.my_computer.total_data_out  = data_out_accumulator 
            self.my_computer.total_data_in = data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of Mercator loop



        elif self.current == 'table': #Start table loop

            self.widget_container.clear_widgets()

            for country in self.country_dictionary: #Start of Country loop

                country_data_in_accumulator = 0 
                country_data_out_accumulator = 0

                for city_index, city in enumerate(self.country_dictionary[country][1]): # Begin City Loop
                    
                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0

                    for ip_index, ip_widget in enumerate(self.country_dictionary[country][1][city][1:]): # Begin IP loop
                        
                        city_data_in_accumulator += ip_widget.ip_data['data_in']
                        city_data_out_accumulator += ip_widget.ip_data['data_out']
                    
                        # End of IP loop
    
                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    # End of City loop

                data_out_accumulator += country_data_out_accumulator
                data_in_accumulator += country_data_in_accumulator

                # End of Country loop

            # Continue table loop

            self.my_computer.total_data_out  = data_out_accumulator 
            self.my_computer.total_data_in = data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total Data IN (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total Data OUT (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of table loop



        elif self.current == 'banned': #Start banned loop

            self.widget_container.clear_widgets()

            for country in self.country_dictionary: #Start of Country loop

                country_data_in_accumulator = 0 
                country_data_out_accumulator = 0

                for city_index, city in enumerate(self.country_dictionary[country][1]): # Begin City Loop
                    
                    city_data_in_accumulator = 0
                    city_data_out_accumulator = 0

                    for ip_index, ip_widget in enumerate(self.country_dictionary[country][1][city][1:]): # Begin IP loop
                        
                        city_data_in_accumulator += ip_widget.ip_data['data_in']
                        city_data_out_accumulator += ip_widget.ip_data['data_out']
                    
                        # End of IP loop
    
                    country_data_in_accumulator += city_data_in_accumulator
                    country_data_out_accumulator += city_data_out_accumulator

                    # End of City loop

                data_out_accumulator += country_data_out_accumulator
                data_in_accumulator += country_data_in_accumulator

                # End of Country loop

            # Continue banned loop
            self.my_computer.total_data_out  = data_out_accumulator 
            self.my_computer.total_data_in = data_in_accumulator

            self.settings_panel.total_data_in_label.text = f"Total data in (GB): [b][color={data_in_color}]{self.my_computer.total_data_in/1000000000.0:.3f}[/color][/b]"
            self.settings_panel.total_data_out_label.text = f"Total data out (GB): [b][color={data_out_color}]{self.my_computer.total_data_out/1000000000.0:.3f}[/color][/b]"

            # End of banned loop
            
        # End of GUI loop 
    


   
    

    def update_from_sniffer(self, time_delta: tuple) -> None:
        
        """
        Update GUI widgets and/or make new GUI widgets from network sniffer data. 
        """

        self.recieve_data_from_sniffer()
         

        for new_ip in self.sniffer_dictionary.keys(): # iterate over the json dictionary sent from network_sniffer.py

            

            if new_ip in self.ip_dictionary: # IP, City and Country widgets exist. Only update IP data. 
                
                self.ip_dictionary[new_ip].ip_data = self.sniffer_dictionary[new_ip]
                
                delta_new_packet = time.time() - self.sniffer_dictionary[new_ip]['delta_time']
                self.ip_dictionary[new_ip].delta_new_packet = delta_new_packet
                self.ip_dictionary[new_ip].connection_opacity = map_to_range(delta_new_packet, 20, 0, 0,1)
                
                #TODO use a selectable time threshold to trigger new data flag. 
                if delta_new_packet < 20:
                        self.ip_dictionary[new_ip].new_data = True
                else:
                    self.ip_dictionary[new_ip].new_data = False
                    

            else: #Case:  IP widget doesn't exist, so lets make it 
                
                
                geoip_info = self.sniffer_dictionary[new_ip]['geoip_info'] 

                if geoip_info == None:
                    city = "Unresolved"
                    country = "Unresolved"
                    ip_longitude = "Unresolved"
                    ip_latitude = "Unresolved"  
                    country_code = "Unresolved"
                else:
                    country = geoip_info['country_name']
                    country_code = geoip_info['country_code']
                    ip_longitude = geoip_info['longitude']
                    ip_latitude = geoip_info['latitude']
                    city = geoip_info['city']

                
                ip_longitude_x , ip_latitude_y = self.mercator_coordinates(ip_longitude, ip_latitude)


                #TODO:Use banned_ips_dict for constant time lookup
                ip_banned_on_creation = False #intialize value. 
                if new_ip in self.banned_ips_array : 
                    ip_banned_on_creation = True 
                

                
                ip_placeholder = IP_Widget(
                                            gui_manager = self,
                                            ip = new_ip,
                                            ip_data = self.sniffer_dictionary[new_ip],
                                            window_x = self.window_x,
                                            window_y = self.window_y,
                                            country = country,
                                            city = city,
                                            ip_latitude = ip_latitude,
                                            ip_longitude = ip_longitude,
                                            ip_latitude_y = ip_latitude_y,
                                            ip_longitude_x = ip_longitude_x,
                                            ip_banned_on_creation = ip_banned_on_creation,
                                            scale_array = self.scale_array,
                                            tcp_color = self.config_variables_dict['tcp_color'],
                                            udp_color = self.config_variables_dict['udp_color'],
                                            other_color = self.config_variables_dict['other_color']       
                                            ) 

       
                
                #need check after IP_widget is created in order to have the ip_placeholder reference for whois lookup
                if new_ip in self.ip_whois_info_dict.keys():
                    ip_whois_description = self.ip_whois_info_dict[new_ip]["nets"][0]['description']
                    ip_placeholder.whois_description = ip_whois_description
                
                else:
                    self.todo_ip_whois_array.append((new_ip, ip_placeholder))

                
                self.ip_dictionary[new_ip] = ip_placeholder # add IP widget into convenience lookup dictionary, seperate from the hierarchical country dictionary

                 
                self.ip_total_count += 1 # After we update total_ip_label.text
            

                #### ip widget made, now check to see if country and city widget exist

                if country in self.country_dictionary: # Country widget exists
                    
                    if city in self.country_dictionary[country][1]: # City widget exists

                        self.country_dictionary[country][1][city][0].total_count += 1 #first item in array is city widget
                        self.country_dictionary[country][1][city].append(ip_placeholder) # add ip widget to array in city dictionary
                        
                        if self.country_dictionary[country][1][city][0].show_ip_widgets == True:
                            ip_placeholder.show = True # flag to display IP widget
                

                    else: # Case: Country widget exists, but no city widget exists. Build city widget
                        
                        country_widget = self.country_dictionary[country][0] #first item in array is country widget
                        country_x =  country_widget.x_ # Get x screen position of Country Widget
                        country_y = country_widget.y_  # Get y screen position of Country Widget

                        
                        city_widget = City_Widget(  
                                                    x_cord_country = country_x,
                                                    y_cord_country = country_y,
                                                    gui_manager = self,
                                                    center_x = self.center_x,
                                                    center_y = self.center_y,
                                                    window_x = self.window_x,
                                                    window_y = self.window_y,
                                                    city = city,
                                                    country = country,
                                                    latitude = ip_latitude,
                                                    longitude = ip_longitude,
                                                    latitude_y = ip_latitude_y,
                                                    longitude_x = ip_longitude_x,
                                                    scale_array = self.scale_array
                                                    
                                                    ) 
                        
                       

                        # set display flags for City and IP widgets
                        if country_widget.show_city_widgets == True:
                            city_widget.show = True #

                            if city_widget.show_ip_widgets == True:
                                ip_placeholder.show = True


                        self.country_dictionary[country][1].setdefault(city, []).append(city_widget) #set City widget to first position in array. See data structure documentation for clarification.
                        self.country_dictionary[country][1][city].append(ip_placeholder) # add ip widget to array in city dictionary
                        self.city_total_count += 1 # After we update total_cities_label.text
                        


                else: # Case: Country widget and City widget don't exist.  Build Country and City widget
                    
                    
                    #randomly initalize position for country widget on screen for graph view
                    country_x = 200 + random()*(self.window_x-300)
                    country_y = 200 + random()*(self.window_y-300)
                        
                    country_widget = Country_Widget( 
                                                    x_cord = country_x,
                                                    y_cord = country_y,
                                                    gui_manager = self,
                                                    center_x = self.center_x,
                                                    center_y = self.center_y,
                                                    window_x = self.window_x,
                                                    window_y = self.window_y,
                                                    country = country,
                                                    country_code = country_code,
                                                    scale_array = self.scale_array,
                                                    country_index = self.country_total_count
                                                )
                    
                    

                

                    self.country_dictionary.setdefault(country, [country_widget]).append({}) # Append to country dictionary. Set first item in array as country widget and second item as city dictionary. See data structure documentation for clarification.                            

                    city_widget = City_Widget(      
                                                    gui_manager = self,
                                                    x_cord_country = country_x,
                                                    y_cord_country = country_y,
                                                    center_x = self.center_x,
                                                    center_y = self.center_y,
                                                    window_x = self.window_x,
                                                    window_y = self.window_y,
                                                    city = city,
                                                    country = country,
                                                    latitude = ip_latitude,
                                                    longitude = ip_longitude,
                                                    latitude_y = ip_latitude_y,
                                                    longitude_x = ip_longitude_x,
                                                    scale_array = self.scale_array,
                                                    )

                    
            
                    self.country_dictionary[country][1].setdefault(city, []).append(city_widget)  # set City widget to first position in array. See data structure documentation for clarification.
                    self.country_dictionary[country][1][city].append(ip_placeholder) # add ip widget to array in city dictionary
                    
                    self.city_total_count += 1  #After we update total_cities_label.text
                    self.country_total_count += 1 #After we update total_countries_label.text



        geographic_data_color = get_hex_from_color(self.config_variables_dict["Geographic Data"]) 

        self.settings_panel.total_ip_label.text = f"IP's: [b][color={geographic_data_color}] {self.ip_total_count} [/color][/b]" 

        self.settings_panel.total_cities_label.text = f"Cities: [b][color={geographic_data_color}]{self.city_total_count}[/color][/b]"

        self.settings_panel.total_countries_label.text = f"Countries: [b][color={geographic_data_color}]{self.country_total_count}[/color][/b]"

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
       
       
        #Check two conditions if the ip_whois_thread is not running.
    
        if self.ip_whois_thread == None: 
            todo_ip_whois_array_copy = self.todo_ip_whois_array.copy() #copy IP's that need lookup
            self.todo_ip_whois_array = [] #reset the datastructure
            self.ip_whois_thread = threading.Thread(target = self.ip_whois_lookup_thread, kwargs = {'todo_ip_whois_array': todo_ip_whois_array_copy}).start() #start the thread with a batch of IP's

        elif self.ip_whois_thread.is_alive() == False:
            todo_ip_whois_array_copy = self.todo_ip_whois_array.copy() #copy IP's that need lookup
            self.todo_ip_whois_array = [] #reset the datastructure
            self.ip_whois_thread = threading.Thread(target = self.ip_whois_lookup_thread, kwargs = {'todo_ip_whois_array': todo_ip_whois_array_copy}).start() #start the thread with a batch of IP's

        elif self.ip_whois_thread.is_alive() == True: #thread is still running so wait for it to finish before starting again
            pass

    
    
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
                ip_whois_description = ip_whois_info["nets"][0]['description'] 

                if ip_whois_description == None:
                    ip_whois_description = "No information Available"

                ip_whois_info["nets"][0]['description'] = ip_whois_description
                self.ip_whois_info_dict[ip] = ip_whois_info
                ip_object.whois_description = ip_whois_description 
        
            except ValueError as e:
                ip_whois_description = "Invalid IP address: %s." % ip
                self.ip_whois_info_dict[ip] = {"nets":[{'description':ip_whois_description}]}
                ip_object.whois_description = ip_whois_description 
                print(ip_whois_description, "<----ValueError")
            except ipwhois.exceptions.IPDefinedError as e:
                ip_whois_description = "%s" % e
                self.ip_whois_info_dict[ip] = {"nets":[{'description':ip_whois_description}]}
                ip_object.whois_description = ip_whois_description 
                print(ip_whois_description, "<----ipwhois.exceptions.IPDefinedError")
            except ipwhois.exceptions.ASNRegistryError as e:
                ip_whois_description = "%s" % e
                self.ip_whois_info_dict[ip] = {"nets":[{'description':ip_whois_description}]}
                ip_object.whois_description = ip_whois_description 
                print(ip_whois_description, "<---ipwhois.exceptions.ASNRegistryError" )
            except Exception as e:
                ip_whois_description = "Error %s" % e
                self.ip_whois_info_dict[ip] = {"nets":[{'description':ip_whois_description}]}
                ip_object.whois_description = ip_whois_description 
                print(ip_whois_description, "<----Exception")




    def set_graph_view(self, *button: Button):

        """
        Transition screenmanager to graph view and display appropriate widgets.
        """

        self.widget_container.clear_widgets()
        current_view = self.current #get current screenmanager state
        
        ##### Clean up previous view
        if current_view == 'mercator':
            self.mercator_view.clear_widgets()
            self.my_computer.mercator_position = self.my_computer.icon_scatter_widget.pos
          
            for country in self.country_dictionary:
                self.country_dictionary[country][0].mercator_position = self.country_dictionary[country][0].icon_scatter_widget.pos
            
                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].mercator_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save mercator position
                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.mercator_position = ip.icon_scatter_widget.pos
            
            
                             
        elif current_view == 'table':
            self.table_view.clear_widgets()
            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.icon_scatter_widget.remove_widget(country_widget.label)

        elif current_view == 'banned':
            self.banned_view.clear_widgets()
            for country in self.country_dictionary:
                country_widget = self.country_dictionary[country][0]
                country_widget.icon_scatter_widget.remove_widget(country_widget.label)

        
        #####



        #Produce graph view

        if self.settings_panel.summary_data_popup_open == True and self.settings_panel.summary_data_layout not in self.persistent_widget_container.children:
            self.persistent_widget_container.add_widget(self.settings_panel.summary_data_layout)

        if self.settings_panel.color_picker_popup_open == True and self.settings_panel.color_picker_layout not in self.persistent_widget_container.children:
            self.persistent_widget_container.add_widget(self.settings_panel.color_picker_layout)

        for widget in self.graph_widgets: 
            self.graph_view.add_widget(widget)

        
        self.current = 'graph' #set screenmanager view

        self.my_computer.set_graph_layout()

        for country in self.country_dictionary:
            self.country_dictionary[country][0].set_graph_layout()

            for city in self.country_dictionary[country][1]:
                self.country_dictionary[country][1][city][0].set_graph_layout()
            
                for ip in self.country_dictionary[country][1][city][1:]:
                    ip.set_graph_layout()
        


       



    def set_mercator_view(self, *button: Button) -> None:

        """
        Transition screenmanager to mercator view and display appropriate widgets.
        """

       
        
        self.widget_container.clear_widgets()
        current_view = self.current #get current screenmanager state


        #Query remote sniffer to get geolocation. Use bool(sniffer_dictionary) to see if remote connection has already been established. 
        if self.sniffer_ip == None and bool(self.sniffer_dictionary) == True:
            
                self.server_socket.send(b'ip_info')
                encoded_ip = self.server_socket.recv()
                self.sniffer_ip = encoded_ip.decode("utf-8")
                my_ip_info = self.ip_database_lookup.record_by_addr(self.sniffer_ip)
                self.interface_dictionary[self.sniffer_ip] = my_ip_info
                screen_x, screen_y = self.mercator_coordinates(my_ip_info['longitude'], my_ip_info['latitude'])
                self.my_computer.mercator_position = (screen_x, screen_y)
                self.my_computer.mercator_layout_finished = False
                
            

        ##### Clean up previous view
        if current_view == 'graph':
            self.graph_view.clear_widgets()
            self.my_computer.graph_position = self.my_computer.icon_scatter_widget.pos #save graph position

            for country in self.country_dictionary:
                self.country_dictionary[country][0].graph_position = self.country_dictionary[country][0].icon_scatter_widget.pos #save graph position

                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].graph_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save graph position

                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.graph_position = ip.icon_scatter_widget.pos #save graph position

             
        elif current_view == 'table':
            self.table_view.clear_widgets()
        elif current_view == 'banned':
            self.banned_view.clear_widgets()


        
        #####


        #Produce mercator view
        if self.settings_panel.summary_data_popup_open == True and self.settings_panel.summary_data_layout not in self.persistent_widget_container.children:
            self.persistent_widget_container.add_widget(self.settings_panel.summary_data_layout)

        if self.settings_panel.color_picker_popup_open == True and self.settings_panel.color_picker_layout not in self.persistent_widget_container.children:
            self.persistent_widget_container.add_widget(self.settings_panel.color_picker_layout)

        for widget in self.mercator_widgets:    
            self.mercator_view.add_widget(widget)

        self.current = "mercator" #set screenmanager view
   
        self.my_computer.set_mercator_layout()
  
        for country in self.country_dictionary:
            self.country_dictionary[country][0].set_mercator_layout()
            
            for city in self.country_dictionary[country][1]:
                self.country_dictionary[country][1][city][0].set_mercator_layout()

                for ip in self.country_dictionary[country][1][city][1:]:
                    ip.set_mercator_layout()
        
      

        

    def set_table_view(self, button: Button) -> None:
        
        """
        Transition screenmanager to table view and display appropriate widgets.
        """
        
        current_view = self.current #get current screenmanager state

        ##### Clean up previous view
        if current_view == 'graph':
            self.graph_view.clear_widgets()

            self.my_computer.graph_position = self.my_computer.icon_scatter_widget.pos  #save graph position

            for country in self.country_dictionary:
                self.country_dictionary[country][0].graph_position = self.country_dictionary[country][0].icon_scatter_widget.pos #save graph position

                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].graph_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save graph position

                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.graph_position = ip.icon_scatter_widget.pos #save graph position

        elif current_view == 'mercator':

            self.mercator_view.clear_widgets()

            self.my_computer.mercator_position = self.my_computer.icon_scatter_widget.pos
          
            for country in self.country_dictionary:
                self.country_dictionary[country][0].mercator_position = self.country_dictionary[country][0].icon_scatter_widget.pos
            
                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].mercator_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save mercator position

                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.mercator_position = ip.icon_scatter_widget.pos

        elif current_view == 'banned':
            self.banned_view.clear_widgets()
        #####


        #Produce table view
        if self.settings_panel.summary_data_popup_open == True:
            self.persistent_widget_container.remove_widget(self.settings_panel.summary_data_layout)

        if self.settings_panel.color_picker_popup_open == True:
            self.persistent_widget_container.remove_widget(self.settings_panel.color_picker_layout)

        self.data_from_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN"])}] Data IN (MB) [/color]'
        self.data_to_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT"])}] Data OUT (MB) [/color]'

        for widget in self.table_widgets:  
            self.table_view.add_widget(widget)

        self.current = "table" #set screenmanager view

        self.select_data_label.pos = (self.center_x, self.center_y)

        if self.database_in_action:
            self.table_view.add_widget(self.loading_widget_progress_bar)
            self.select_data_label.pos = (-500,-500)

        if self.generate_table_init_bool:
            self.select_data_label.pos = (-500,-500)

        
        self.update_table_button.text = "Display Stored Data" #prevents a bug when no saved sessions changes button text permanently

            
        

    def set_banned_view(self, button: Button) -> None:
        
        """
        Transition screenmanager to banned view and display appropriate widgets.
        """

        current_view = self.current #get current screenmanager state

        ##### Clean up previous view
        if current_view == 'graph':
            self.graph_view.clear_widgets()
            
            self.my_computer.graph_position = self.my_computer.icon_scatter_widget.pos  #save graph position
            
            for country in self.country_dictionary:
                self.country_dictionary[country][0].graph_position = self.country_dictionary[country][0].icon_scatter_widget.pos #save graph position

                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].graph_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save graph position

                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.graph_position = ip.icon_scatter_widget.pos #save graph position

        elif current_view == 'mercator':
            self.mercator_view.clear_widgets()

            self.my_computer.mercator_position = self.my_computer.icon_scatter_widget.pos
          
            for country in self.country_dictionary:
                self.country_dictionary[country][0].mercator_position = self.country_dictionary[country][0].icon_scatter_widget.pos
            
                for city in self.country_dictionary[country][1]:
                    self.country_dictionary[country][1][city][0].mercator_position = self.country_dictionary[country][1][city][0].icon_scatter_widget.pos #save mercator position
                    for ip in self.country_dictionary[country][1][city][1:]:
                        ip.mercator_position = ip.icon_scatter_widget.pos
            

            

        elif current_view == 'table':
            self.table_view.clear_widgets()
       #####



        #Produce banned view
        if self.settings_panel.summary_data_popup_open == True:
            self.persistent_widget_container.remove_widget(self.settings_panel.summary_data_layout)

        if self.settings_panel.color_picker_popup_open == True:
            self.persistent_widget_container.remove_widget(self.settings_panel.color_picker_layout)

        for widget in self.banned_widgets: 
            self.banned_view.add_widget(widget)

        self.current = "banned" #set screenmanager view

        #Query database for data to populate banned table
        cursor = db.cursor()
        sql_query = ("SELECT * from banned_IP")
        cursor.execute(sql_query) 
        banned_ips = cursor.fetchall() 
   
        sql_index = [0,1,2,3] #use this array as index selector when populating data from banned_IP database
        length_per_label = self.window_x /4 -100

        self.banned_ip_table.clear_widgets()        
        for ip in banned_ips: 
            box_layout = BoxLayout( 
                                    orientation = 'horizontal',
                                    pos_hint = (None,None),
                                    size_hint = (None,None),
                                    padding=25,
                                    spacing=length_per_label,
                                    size = (self.window_x, 20 )
                                    )

            for index in sql_index:

                label_placeholder = self.make_label(str(ip[index]), length_per_label)
                box_layout.add_widget(label_placeholder)

            self.banned_ip_table.add_widget(box_layout)




    def populate_network_interfaces(self) -> None:

        """
        Identify network interfaces.
        """

        self.my_mac_address = ':'.join(("%012x" % get_mac())[i:i+2] for i in range(0, 12, 2)) 



         


    def make_settings_panel(self) -> None:

        """
        Convience function for constructing Settings Panel -- need to construct this first before make_GUI_widgets().
        """

        self.settings_panel = Settings_Panel()
        self.settings_panel.gui_manager = self
        self.settings_panel.init_accordion()
        self.settings_panel.scale_array = self.scale_array 
        self.settings_panel_container = AnchorLayout(anchor_x = 'right', anchor_y = 'center')
        self.settings_panel_container.add_widget(self.settings_panel)



    def make_GUI_widgets(self) -> None:

        """
        Convience function for constructing all GUI widgets.
        """

        self.widget_container = FloatLayout()
        self.persistent_widget_container = FloatLayout()

        self.settings_panel.summary_data_toggle()



        # Building menu icons (triggers view changes)
        self.main_settings_icon = self.make_icon( 
                                                  image = '../assets/images/UI/shield.png',
                                                  on_press_toggle = self.settings_toggle, 
                                                  icon_pos = self.config_variables_dict["main_settings_icon_pos"],
                                                  identity = 'main_settings'   
                                                )

        self.table_icon = self.make_icon( 
                                          image = '../assets/images/UI/table_view.png',
                                          on_press_toggle = self.set_table_view, 
                                          icon_pos = self.config_variables_dict["table_icon_pos"],
                                          identity = 'table_icon'
                                        )

        self.mercator_icon = self.make_icon( 
                                             image = '../assets/images/UI/world.png', 
                                             on_press_toggle = self.set_mercator_view, 
                                             icon_pos = self.config_variables_dict["mercator_icon_pos"],
                                             identity = 'mercator_icon'
                                           )

        self.graph_icon = self.make_icon( 
                                         image = '../assets/images/UI/graph.png',
                                         on_press_toggle = self.set_graph_view,
                                         icon_pos = self.config_variables_dict["graph_icon_pos"],
                                         identity = 'graph_icon'
                                        )

        self.banned_icon = self.make_icon(image = '../assets/images/UI/banned.png',
                                         on_press_toggle=self.set_banned_view, 
                                         icon_pos = self.config_variables_dict["banned_icon_pos"],
                                         identity = 'banned_icon'
                                         )


        # Building Graph (view1) 
        self.my_computer = My_Computer( 
                                        id = 'My Computer',
                                        window_x = self.window_x,
                                        window_y = self.window_y,
                                        gui_manager = self,
                                        center_position = (self.center_x, self.center_y),
                                        scale_array = self.scale_array
                                      ) 


        # Building Mercator (view2)
        self.mercator_container = Widget() # for mercator background image
        self.mercator_container.orientation = "horizontal"
        self.mercator_container.id = "mercator-layout"
        self.mercator_container.size = (self.window_x, self.window_y)

        self.mercator_image = Image(    
                                    source = "../assets/images/UI/mercator.png",
                                    size_hint= (None,None),
                                    keep_ratio= False,
                                    allow_stretch=True, 
                                    size = (self.window_x, self.window_y)
                                    )

        self.mercator_container.add_widget(self.mercator_image)



        # Building Table (view3) 
        self.loading_widget_progress_bar = ProgressBar(max=1, size_hint=(.5,.5), pos=(self.center_x/2, self.center_y/2))
        
        self.select_data_label = Label(
                                    text= "Select Data  -- Live or Stored",
                                    text_size=(500,200),
                                    pos = (-500, -500),
                                    size = (300,200),
                                    size_hint =(None,None)
                                   )

        self.update_table_button =  Button()
        self.update_table_button.on_press = self.table_dropdown_show
        self.update_table_button.size_hint = (None,None)
        self.update_table_button.size = (self.window_x *.175, 40)
        self.update_table_button.pos = (self.window_x * .25,20)
        self.update_table_button.background_color = (.15,.15,.15,.8)
        self.update_table_button.text = "Display Stored Data"
        self.update_table_button.id = 'database data_in'

        self.update_table_button_live =  Button()
        self.update_table_button_live.on_press = lambda : self.generate_table_sort_wrapper(calling_button = self.update_table_button_live)
        self.update_table_button_live.size_hint = (None,None)
        self.update_table_button_live.size = (self.window_x *.175, 40)
        self.update_table_button_live.pos = (self.window_x * .45,20)
        self.update_table_button_live.background_color = (.15,.15,.15,.8)
        self.update_table_button_live.text = "Display Live Data Snapshot"
        self.update_table_button_live.id = 'Live data_in'
        self.update_table_button_live.sorting_key = 'Live data_in'

        self.session_label = Label()
        self.session_label.text = "Session: " + self.session_name
        self.session_label.size_hint = (None,None)
        self.session_label.size = (self.window_x *.175, 40)
        self.session_label.pos = (self.window_x * .65,20)

        self.table_selection_dropdown = DropDown() #used for selecting a saved session (from database)
        self.table_selection_dropdown.size_hint = (None,None)
        self.table_selection_dropdown.id = 'database data_in'  #id is used as parameters for building database logic see generate_table_sort_wrapper()
        
        self.table_scroll = ScrollView(
                                       scroll_distance = 50,
                                       size_hint_y =  self.window_ratio-0.05,
                                       pos = (0,75 )
                                      )

        self.table = GridLayout(
                                size_hint = (None, None),
                                col_default_width = self.window_x/2,
                                row_default_height = 30,
                                cols=1,
                                padding= (10, 0)
                               )

        self.table.bind(minimum_height=self.table.setter('height'))
        self.table.bind(minimum_width=self.table.setter('width'))
        self.update_table_button.bind(on_release = self.table_selection_dropdown.open)
        self.table_selection_dropdown.bind(on_select = lambda drop_down_btn, session : self.generate_table_sort_wrapper(calling_button = session))

        self.box_header_container = AnchorLayout(anchor_y='top')
        self.box_header = self.create_table_header()        

        self.box_header_container.add_widget(self.box_header)
        self.table_scroll.add_widget(self.table)

        self.session_label = Label()
        self.session_label.text = "Session: " + self.session_name
        self.session_label.size_hint = (None,None)
        self.session_label.size = (self.window_x *.175, 40)
        self.session_label.pos = (self.window_x * .65,20)

        self.clear_banned_ips_button =  Button( on_press=self.clear_banned_ips,
                                                size_hint=(None,None),
                                                size = (self.window_x *.2, 40),
                                                pos=(self.window_x*.4,20),
                                                background_color=(.3,.3,.3, .8),
                                                text = "Clear Banned IP Addresses",
                                                )

        self.ip_scroll = ScrollView(
                                      scroll_distance = 50,
                                      size_hint_y =  self.window_ratio-0.05,
                                      size_hint_x =  1,
                                      pos = (0,75 )
                                      )

        self.banned_ip_table = GridLayout(
                                            size_hint = (None, None),
                                            col_default_width = self.window_x,
                                            row_default_height = 30,
                                            cols=1,
                                            padding= (0, 60)
                                            )
        self.banned_ip_table.bind(minimum_height = self.banned_ip_table.setter('height'))
        self.banned_ip_table.bind(minimum_width = self.banned_ip_table.setter('width'))

        self.banned_ip_container = AnchorLayout(anchor_y='top', anchor_x='left')
        self.banned_ip_header = self.create_banned_header()

        self.ip_scroll.add_widget(self.banned_ip_table)
        self.banned_ip_container.add_widget(self.banned_ip_header)




    def init_database_(self, session_name):

        """
        Initalize sqlite3 database
        """ 
   
        cursor = db.cursor()
        init_session_sql = ("CREATE TABLE IF NOT EXISTS sessions (session_name TEXT PRIMARY KEY, session_data dictionary )")
        cursor.execute(init_session_sql)

        init_banned_ips_sql = "CREATE TABLE IF NOT EXISTS banned_IP (ip TEXT PRIMARY KEY, whois TEXT, country TEXT, time_stamp TEXT, ip_data dictionary)"
        cursor.execute(init_banned_ips_sql)
 
        cursor.execute("SELECT * FROM banned_IP")
        database_dump = cursor.fetchall()

        for ip in database_dump:
            self.banned_ips_array.append(ip[0])

      






















    def generate_table_sort_wrapper(self, calling_button): #hack function (prequel) --use decorator or metaclass?  to get correct animation behavior (excutes "sort" in a seperate thread)
        
        if self.database_in_action:
            return


        self.table_view.add_widget(self.loading_widget_progress_bar)
        button_arguments = calling_button.sorting_key.split(' ') #used the button id(a space deliminated string) to pass sorting parameters for different conditions

        if button_arguments[0] == 'sort':

            if self.session_query == '':
                self.table_view.remove_widget(self.loading_widget_progress_bar)
            else:
                self.table.clear_widgets()
                self.select_data_label.pos = (-500, -500)
                self.database_in_action = True
                self.generate_table_init_bool = True
                self.loading_thread = threading.Thread(target = self.sort_database_table_view_GUI_member, kwargs = {'data_table': self.session_query, 'sort_by': button_arguments[1], 'case': 'sort' }).start()

        elif button_arguments[0] == 'Live':
            self.select_data_label.pos = (-500, -500)
            self.session_query = 'Live'
            self.session_label.text = "Session: " + self.session_query
            self.table.clear_widgets()
            self.database_in_action = True
            self.generate_table_init_bool = True
            self.loading_thread = threading.Thread(target = self.sort_database_table_view_GUI_member, kwargs = {'data_table': self.session_query, 'sort_by': 'data_in',  'case': 'Live' } ).start()
                
        elif button_arguments[0] == 'database':
            self.select_data_label.pos = (-500, -500)
            self.session_query = button_arguments[1]
            self.session_label.text = "Session: " + self.session_query
            self.table.clear_widgets()
            self.database_in_action = True
            self.generate_table_init_bool = True
            self.loading_thread = threading.Thread(target = self.sort_database_table_view_GUI_member, kwargs = {'data_table': self.session_query, 'sort_by': 'data_in', 'case': 'database' })
            self.loading_thread.start()
    
        elif button_arguments[0] == 'banned':
            self.select_data_label.pos = (-500, -500)
            self.database_in_action = True
            self.generate_table_init_bool = True
            self.loading_thread = threading.Thread(target = self.sort_database_table_view_GUI_member, kwargs = {'data_table': self.session_query, 'sort_by': 'data_in',  }).start()
        

         









        #query sql database and generate GUI table
    def sort_database_table_view_GUI_member(self, **kwargs) -> None:
        
        """


        """

        db = sqlite3.connect('../assets/database/sessions.sqlite', isolation_level=None, timeout=10)
        cursor = db.cursor()
        

        data_table = kwargs['data_table']
        sort_by = kwargs['sort_by']
        case = kwargs['case']



        if case == 'Live': #BUGS

            cursor.execute("CREATE TABLE IF NOT EXISTS {data_table} (ip TEXT PRIMARY KEY, description TEXT DEFAULT 'NONE', time_stamp TEXT DEFAULT 'NONE', location_city TEXT DEFAULT 'NONE', location_country TEXT DEFAULT 'NONE', longitude INTEGER, latitude INTEGER, total_packets INTEGER DEFAULT 0, data_in INTEGER DEFAULT 0, data_out INTEGER DEFAULT 0, tcp_packets INTEGER DEFAULT 0, udp_packets INTEGER DEFAULT 0, other_packets INTEGER DEFAULT 0, blocked INTEGER DEFAULT 0, safe_listed INTEGER DEFAULT 0, flagged INTEGER DEFAULT 0)".format(data_table = data_table))
            

            stored_sniffer_dict = self.sniffer_dictionary #TODO:copy dict to prevent thread collision (necessary?)

            number_of_ips = str(len(stored_sniffer_dict.keys()))
            number_of_ips_int = len(stored_sniffer_dict.keys())
            


            self.ip_label_header.text = 'IP Address (' + number_of_ips + ')' # of ip's - gives visual cue for users



            for n, ip in enumerate(stored_sniffer_dict.keys()):
                


                if ip in self.built_table: #check to see if inserted into database (faster than sql query?)
                    
                    

           
                    ip_whois_description = self.ip_dictionary[ip].whois_description

                    #single or double quotes in the whois description may break when inserted into database
                    if ip_whois_description.find("\'") >= 0:
                        ip_whois_description = ip_whois_description.replace("\'", "")

                    elif ip_whois_description.find("\"") >= 0:
                        ip_whois_description = ip_whois_description.replace("\"", "")


                    data_out = stored_sniffer_dict[ip]['data_out']
                    data_in = stored_sniffer_dict[ip]['data_in']
                    total_packets = stored_sniffer_dict[ip]['packet_count']

                    cursor.execute(f"""UPDATE OR IGNORE {data_table} SET total_packets = "{total_packets}", data_in = "{data_in}", data_out = "{data_out}", description = '{ip_whois_description}'  WHERE ip = "{ip}" """)


                    db.commit()

                    

                else: #not in database, so insert into database

                    geoip_info = stored_sniffer_dict[ip]['geoip_info']

                    if geoip_info == None:
                        city = 'Unresolved'
                        country = 'Unresolved'
                        ip_longitude = None
                        ip_latitude = None
                    else:
                        city = geoip_info['city']
                        country = geoip_info['country_name']
                        ip_longitude = geoip_info['longitude']
                        ip_latitude = geoip_info['latitude']      
            
                                        
                    ip_whois_description = self.ip_dictionary[ip].whois_description


                    #once we have everything we need, insert into database - insert into database so we can leverage SQL functionality
                    try:
                        cursor.execute("""INSERT OR IGNORE INTO {data_table} (ip, location_city, location_country,  longitude, latitude, description, total_packets, data_in, data_out, blocked) VALUES ( '{ip_string}', '{location_city}', '{location_country}', '{longitude}', '{latitude}', "{description}", '{total_packets}', '{data_in}', '{data_out}', '{blocked}' )""".format(ip_string=ip, location_city=city, location_country=country, longitude = ip_longitude , latitude=ip_latitude, description= ip_whois_description, data_table = data_table, total_packets = stored_sniffer_dict[ip]['packet_count'], data_in = stored_sniffer_dict[ip]['data_in'], data_out = stored_sniffer_dict[ip]['data_out'], blocked = 'False' ))
                        db.commit()
                        self.built_table[ip] = 'True'

                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)
                        print("BROKEN insert or ignore into database ")

                    
                    self.loading_widget_progress_bar.value = n/number_of_ips_int

       

            #select from database (sorted)

            #TODO
            #DISPLAY LIVE SNAPSHOT followed by resize reset generates this bug
            #Exception has occurred: OperationalError
            #no such table: Live
            cursor.execute("SELECT * FROM {data_table} ORDER BY {sort} DESC".format(sort=sort_by, data_table= data_table))
            database_dump = cursor.fetchall()




        elif case == 'database':

  
            try: #check if db is built, if not we need to build it
                #use this to check if database exists to remove try/catch block
                #cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='table_name';")

                print("trying in database")
                cursor.execute("SELECT * FROM {data_table} ORDER BY {sort} DESC".format(sort=sort_by, data_table= data_table))
                database_dump = cursor.fetchall()
                self.ip_label_header.text = 'IP Address (' + str(len(database_dump)) + ')' # of ip's - gives visual cue for users

            except Exception as e:
                #<class 'sqlite3.OperationalError'> interface.py 1448  
                #if database not built, then we need to build it...better way to do this? 
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                
                #do this first? 
                cursor.execute("CREATE TABLE IF NOT EXISTS {data_table} (ip TEXT PRIMARY KEY, description TEXT DEFAULT 'NONE', time_stamp TEXT DEFAULT 'NONE', location_city TEXT DEFAULT 'NONE', location_country TEXT DEFAULT 'NONE', longitude INTEGER, latitude INTEGER, total_packets INTEGER DEFAULT 0, data_in INTEGER DEFAULT 0, data_out INTEGER DEFAULT 0, tcp_packets INTEGER DEFAULT 0, udp_packets INTEGER DEFAULT 0, other_packets INTEGER DEFAULT 0, blocked INTEGER DEFAULT 0, safe_listed INTEGER DEFAULT 0, flagged INTEGER DEFAULT 0)".format(data_table = data_table))

                cursor.execute("SELECT session_data FROM sessions WHERE session_name = '{data_table}' ".format(data_table = data_table))
                
                database_query = cursor.fetchall()

                stored_sniffer_dict = database_query[0][0]
                stored_sniffer_dict = ast.literal_eval(stored_sniffer_dict)

              
                
                self.ip_label_header.text = 'IP Address (' + str(len(stored_sniffer_dict.keys())) + ')' # of ip's - gives visual cue for users
                number_of_ips_int = len(stored_sniffer_dict.keys())

                for n, ip in enumerate(stored_sniffer_dict.keys()):

                    geoip_info = stored_sniffer_dict[ip]['geoip_info']
            
                    if geoip_info == None:
                        city = 'Unresolved'
                        country = 'Unresolved'
                        ip_longitude = None
                        ip_latitude = None
                    else:
                        city = geoip_info['city']
                        country = geoip_info['country_name']
                        ip_longitude = geoip_info['longitude']
                        ip_latitude = geoip_info['latitude']                    
            
                    try: #IPWhois throws an exception if IP is local
                        ip_whois = IPWhois(ip)
                        ip_whois_info = ip_whois.lookup_whois()
                        ip_whois_description = ip_whois_info["nets"][0]['description']

                
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print(exc_type, fname, exc_tb.tb_lineno)
                        ip_whois_description = 'Unresolved or Local'            
                
                        
                
                    cursor.execute("""INSERT OR IGNORE INTO {data_table} (ip, location_city, location_country,  longitude, latitude, description, total_packets, data_in, data_out, blocked) VALUES ( '{ip_string}', '{location_city}', '{location_country}', '{longitude}', '{latitude}', "{description}", '{total_packets}', '{data_in}', '{data_out}', '{blocked}' )""".format(ip_string=ip, location_city=city, location_country=country, longitude = ip_longitude , latitude=ip_latitude, description= ip_whois_description, data_table = data_table, total_packets = stored_sniffer_dict[ip]['packet_count'], data_in = stored_sniffer_dict[ip]['data_in'], data_out = stored_sniffer_dict[ip]['data_out'], blocked = 'False' ))
                    db.commit()

                    self.loading_widget_progress_bar.value = n/number_of_ips_int



                cursor.execute("SELECT * FROM {data_table} ORDER BY {sort} DESC".format(sort=sort_by, data_table= data_table))
                database_dump = cursor.fetchall()

                print("finished with DB case")



        elif case == 'sort':

            cursor.execute("SELECT * FROM {data_table} ORDER BY {sort} DESC".format(sort=sort_by, data_table= data_table))
            database_dump = cursor.fetchall()

            self.ip_label_header.text = 'IP Address (' + str(len(database_dump)) + ')' # of ip's - gives visual cue for users

    



    #case specific functionality finished, begin general construction
        
        #* need to see if ip has been banned
        cursor.execute("SELECT * FROM banned_IP")
        banned_ips = cursor.fetchall() 
        



        #TODO:use self.banned_ips_array?
        banned_ips_array = [ip[0] for ip in banned_ips]

        label_index = [1,3,4,7,8,9] #select which indices we want from SQL query
        length_per_label = self.window_x / 6


        for ip in database_dump: #database dump is generated by case-specific switch

            box_layout = BoxLayout( 
                orientation = 'horizontal',
                size_hint = (None,None),
                pos = (0,300),
                padding=1,
                size = (self.window_x, 15 )
                )

            if ip[0] in banned_ips_array:

                ip_button = Button()
                ip_button.text = ip[0]
                ip_button.id = ip[0]
                ip_button.on_press = lambda ip_key=ip_button.id : self.ip_button_display(ip_key)
                ip_button.background_color = (1,0,0,1)

                box_layout.add_widget(ip_button)

                for i in label_index:
                    if i == 8 or i == 9:
                        label_placeholder = self.make_label( f"{ip[i]/1000000:.6f}", length_per_label)
                    else:
                        label_placeholder = self.make_label( str(ip[i]), length_per_label)
                    box_layout.add_widget(label_placeholder)

            else:
                
                ip_button = Button()
                ip_button.text = ip[0]
                ip_button.id = ip[0]
                ip_button.on_press = lambda ip_key=ip_button.id : self.ip_button_display(ip_key)
                ip_button.background_color = (0,1,0,1)
                box_layout.add_widget(ip_button)

                for i in label_index:
                    if i == 8 or i == 9:
                        label_placeholder = self.make_label( f"{ip[i]/1000000:.6f}", length_per_label)
                    else:
                        label_placeholder = self.make_label( str(ip[i]), length_per_label)
            
                    box_layout.add_widget(label_placeholder)
        
            
            self.table.add_widget(box_layout)  
 

        self.loading_widget_progress_bar.value = 1
        self.table_view.remove_widget(self.loading_widget_progress_bar)
        self.database_in_action = False

























    def ip_button_display(self, ip_key: str) -> None:
        
        """
        Callable to display IP widget menu (from tableview).
        """

        ip_obj = self.ip_dictionary[ip_key]
        ip_obj.display_menu()



    def table_dropdown_show(self) -> None:

        """
        Callable for selecting a saved database session to display in table view.
        """


        cursor = db.cursor()
        query = ("SELECT * FROM sessions")
        cursor.execute(query)
        stored_session = cursor.fetchall()
        
        if not stored_session:
            self.update_table_button.text = "No saved sessions"

        self.table_selection_dropdown.clear_widgets()
        for n, item in enumerate(stored_session):

            btn = Button(text=str(item[0]), size_hint_y=None, height=44)
            btn.sorting_key = "database " + str(item[0])
            btn.bind(on_release=lambda btn: self.table_selection_dropdown.select(btn))

            self.table_selection_dropdown.add_widget(btn)




    def create_table_header(self) -> BoxLayout:
        
        """
        Convience function for creating table header - view 3.
        """

        box = BoxLayout( 
                        orientation = 'horizontal',
                        pos_hint = (None,None),
                        size_hint = (None,.05),
                        size = (self.window_x, 0)
                        )


        self.ip_label_header = Button()
        self.ip_label_header.text = 'IP Address'  
        self.ip_label_header.id = 'sort ip'
        self.ip_label_header.sorting_key = 'sort ip'
        self.ip_label_header.background_color = (.15,.15,.15,.8)
        self.ip_label_header.on_press = lambda : self.generate_table_sort_wrapper(calling_button = self.ip_label_header)

        description_button = Button()
        description_button.text = 'Description'
        description_button.sorting_key = 'sort description'
        description_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = description_button)
        description_button.id = 'sort description'
        description_button.background_color = (.15,.15,.15,.8)

        city_button = Button() 
        city_button.text = 'City'
        city_button.sorting_key = 'sort location_city'
        city_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = city_button)
        city_button.id = 'sort location_city'
        city_button.background_color = (.15,.15,.15,.8)
        
        country_button = Button()
        country_button.text = 'Country'
        country_button.sorting_key = 'sort location_country'
        country_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = country_button)
        country_button.id = 'sort location_country'
        country_button.background_color = (.15,.15,.15,.8)

        packets_button = Button()
        packets_button.text = 'Total Packets'
        packets_button.sorting_key = 'sort total_packets'
        packets_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = packets_button)
        packets_button.id = 'sort total_packets'
        packets_button.background_color = (.15,.15,.15,.8)

        self.data_from_button = Button()
        self.data_from_button.markup = True
        self.data_from_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data IN"])}] Data IN (MB) [/color]'
        self.data_from_button.sorting_key = 'sort data_in'
        self.data_from_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = data_from_button)
        self.data_from_button.id = 'sort data_in'
        self.data_from_button.background_color = (.15,.15,.15,.8)

        self.data_to_button = Button()
        self.data_to_button.markup = True
        self.data_to_button.text = f'[color={get_hex_from_color(self.config_variables_dict["Data OUT"])}] Data OUT (MB) [/color]'
        self.data_to_button.sorting_key = 'sort data_out' 
        self.data_to_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = data_to_button)
        self.data_to_button.id = 'sort data_out'
        self.data_to_button.background_color = (.15,.15,.15,.8)


        box.add_widget(self.ip_label_header)
        box.add_widget(description_button)
        box.add_widget(city_button)
        box.add_widget(country_button)
        box.add_widget(packets_button)
        box.add_widget(self.data_from_button)
        box.add_widget(self.data_to_button)

        return box





    def create_banned_header(self) -> BoxLayout:

        """
        Convience function for building banned header - view 4.
        """

        box = BoxLayout( 
                        orientation = 'horizontal',
                        pos_hint = (None,None),
                        size_hint = (1,.05),
                        )

        ip_button = Button()
        ip_button.text = 'IP Address'
        ip_button.on_press = lambda : self.generate_table_sort_wrapper( calling_button = ip_button)
        ip_button.id = 'banned ip'
        ip_button.sorting_key = 'banned ip'
        ip_button.background_color = (.15,.15,.15,.8)

        description_button = Button()
        description_button.text = 'Description'
        description_button.on_press = lambda : self.generate_table_sort_wrapper( calling_button = description_button)
        description_button.id = 'banned whois'
        description_button.sorting_key = 'banned whois'
        description_button.background_color = (.15,.15,.15,.8)

        country_button = Button()
        country_button.text = 'Country'
        country_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = country_button)
        country_button.id = 'banned country'
        country_button.sorting_key = 'banned country'
        country_button.background_color = (.15,.15,.15,.8)

        time_button = Button()
        time_button.text = 'Time Stamp'
        time_button.on_press = lambda : self.generate_table_sort_wrapper(calling_button = time_button)
        time_button.id = 'banned time_stamp'
        time_button.sorting_key = 'banned time_stamp'
        time_button.background_color = (.15,.15,.15,.8)
        
        box.add_widget(ip_button)
        box.add_widget(description_button)
        box.add_widget(country_button)
        box.add_widget(time_button)

        return box




    def make_icon(self, image: str, on_press_toggle: Callable, icon_pos: int, identity: str) -> FloatLayout:
        
        """
        Convience function for creating menu GUI icons with layered positioning.
        """

        #print(icon_pos)
        position = [ icon_pos[0], icon_pos[1] ]

        icon_scatter_widget = Scatter(
                              size_hint = (None,None),
                              pos=position,
                              size=("40sp", "40sp")
                              )

        container = FloatLayout()
        container.pos = position
        container.size_hint = (None, None)
        container.size = ("40sp", "40sp")
        container.id = identity

        icon_image = Image( source=image, 
                            size_hint=(None, None),
                            pos = ("5sp","5sp"),
                            size=("30sp", "30sp"),
                            )

        toggle_button = Button(on_press=on_press_toggle,
                                size_hint=(None, None),
                                size=("20sp", "20sp"),
                                pos=("10sp","10sp"),
                                background_color=(0,0,0,0)
                                )

        toggle_button.add_widget(icon_image)
        icon_scatter_widget.add_widget(toggle_button)
        container.add_widget(icon_scatter_widget)

        return container



    def make_label(self, text: str, length_per_label: float) -> Label:

        """
        Convience function to make kivy Labels with specified length.
        """

        custome_label = Label()
        custome_label.halign= 'center'
        custome_label.text_size=(length_per_label,20)
        custome_label.valign= 'middle'
        custome_label.markup=True
        custome_label.shorten= True
        custome_label.text=text

        return custome_label




    def settings_toggle(self, button: Button) -> None:

        """
        Toggle settings menu on/off. 
        """

        if self.settings_toggle_on == True:
            self.persistent_widget_container.remove_widget(self.settings_panel_container)
            self.settings_toggle_on = False

        else:
            self.persistent_widget_container.add_widget(self.settings_panel_container)
            self.settings_toggle_on = True

      


    def mercator_coordinates(self, longitude: float, latitude: float) -> tuple[float, float]:

        """
        Given global longitude and latitude return screen x and y position
        """

        if longitude == 'Unresolved': # No latitude or longitude information, use default
            return self.center_x-100, 20 

        x, y = self.projection(longitude-11, latitude) # x,y in meters

        px = self.center_x + x * self.x_pixels_per_meter # x in pixels
        py = self.center_y + y * self.y_pixels_per_meter # y in pixels

        return px, py



    def clear_banned_ips(self, button: Button) -> None:

        """
        Clear any banned IP's
        """

        for ip in self.banned_ips_array:
            self.ip_dictionary[ip].unblock()

        self.banned_ip_table.clear_widgets()


    def clear_live_database(self) -> None:

        """
        Delete Live database Entry.
        """

        try: #drop sql Live table at end of session.
            cursor = db.cursor()
            query = ("DROP TABLE Live")
            cursor.execute(query)
            db.commit()
            db.close()

        except sqlite3.OperationalError as e:
            pass


       


    def close(self) -> None:

        """
        GUI_Manager closing cleanup function. 
        """

        try: #drop sql Live table at end of session.
            cursor = db.cursor()
            query = ("DROP TABLE Live")
            cursor.execute(query)
            db.commit()
            db.close()
        except sqlite3.OperationalError as e:
            pass

        self.config_variables_dict["main_settings_icon_pos"] = self.main_settings_icon.children[0].pos
        self.config_variables_dict["graph_icon_pos"] = self.graph_icon.children[0].pos
        self.config_variables_dict["table_icon_pos"] = self.table_icon.children[0].pos
        self.config_variables_dict["mercator_icon_pos"] = self.mercator_icon.children[0].pos
        self.config_variables_dict["banned_icon_pos"] = self.banned_icon.children[0].pos
        self.config_variables_dict["summary_data_pos"] = self.settings_panel.summary_data_layout.children[0].pos



        
        #check these attributes for any needed saved changes to configuration file
        if self.settings_panel.checkbox_local.active or self.settings_panel.checkbox_remote.active:
            
            self.config_variables_dict["auto_connect"] = True

            if self.settings_panel.checkbox_local.active == True:
                self.config_variables_dict["connect_to"] = "localhost"
            else:
                self.config_variables_dict["connect_to"] = "remotehost"

        else:
            self.config_variables_dict["auto_connect"] = False


        #Save configuations
        with open('../configuration/config.json', 'w') as configuration_file:
            json.dump(self.config_variables_dict, configuration_file)

        #Save cached IP whois information
        with open('../assets/database/whois.json', 'w') as ip_whois_info_file:
            json.dump(self.ip_whois_info_dict, ip_whois_info_file)