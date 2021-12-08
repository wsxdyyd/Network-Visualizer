# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.



import time
from utils import map_to_range, distance_between_points
from math import sin, cos, pi
from random import random, randrange

from database_config import db

from kivy.metrics import sp
from kivy.graphics import Color, Line
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout





class IP_Widget(Widget):

    """
    GUI Widget for each IP address with member functions for various IP logic.
    """

    def __init__(self, **kwargs):

        """
        Construct GUI widget and associated state.
        """

        super().__init__()

        self.size_hint = (None, None)
        self.id = kwargs['ip'] #ip address used as unique idenifier
        self.window_x = kwargs['window_x']
        self.window_y = kwargs['window_y'] 
        self.center_X = self.window_x/2
        self.center_Y = self.window_y/2
        self.scale_array = kwargs['scale_array']  
        self.latitude = kwargs['ip_latitude']
        self.longitude = kwargs['ip_longitude']
        self.longitude_x = kwargs['ip_longitude_x']
        self.latitude_y = kwargs['ip_latitude_y']
        self.ip_data = kwargs['ip_data']
        self.ip_banned_on_creation = kwargs['ip_banned_on_creation']
        self.gui_manager = kwargs['gui_manager']
        self.country = kwargs['country']
        self.country_label = "Unresolved" if self.country == None else self.country
        self.city  = kwargs['city']
        self.city_label = 'Unresolved' if self.city == None else self.city
        self.whois_description = "Waiting on update"
        self.size = ("50sp","50sp")
        self.x_position = self.pos[0]
        self.y_position = self.pos[1]
    
        
        self.random_radius = randrange(sp(100),sp(200))
        self.pos = (random()*self.window_x, random() * self.window_y)
        self.old_pos = self.pos

        self.spring_constant_1 = 0.04
        self.spring_constant_2 = 0.08
        self.colision = 0
        self.delta_new_packet = 0
        self.new_pos = (0,0)
        self.connection_opacity = 0
        self.tcp_color = kwargs['tcp_color']
        self.udp_color = kwargs['udp_color']
        self.other_color = kwargs['other_color']
       
        self.new_data = True
        self.show = False
        self.data = True
        self.display_popup = False
        self.display_whois_popup = False
        self.do_layout = False
        self.banned = False

        self.menu_popup = None
        self.whois_popup = None
        self.whois_information = None
        

        #Graph view
        self.graph_position = self.pos
        #

        #Mercator view
        self.mercator_position = [0,0]
        self.mercator_show = False
        self.resize = False
        self.packet_display = False
        #
  

        #GUI
        self.container = FloatLayout()
        self.container.pos = self.pos
        self.container.size_hint = (None,None) 
        self.container.size = (50,50) 

        self.icon_image = Image()
        self.icon_image.source = '../assets/images/UI/ip.png'
        self.icon_image.size_hint = (None, None)
        self.icon_image.size = (40,40)
        self.icon_image.pos = (-6,2)

        self.banned_image = Image()
        self.banned_image.source = '../assets/images/UI/banned.png'
        self.banned_image.size_hint = (None, None)
        self.banned_image.size = (20, 20)
        self.banned_image.pos = (3, 6)

        self.display_menu_button = Button()
        self.display_menu_button.on_press = self.display_menu
        self.display_menu_button.size_hint = (None, None)
        self.display_menu_button.size = (15, 15)
        self.display_menu_button.pos_hint = (None,None)
        self.display_menu_button.pos = (6,6)
        self.display_menu_button.background_color = (0,0,1,0)
        
        self.icon_scatter_widget = Scatter()
        self.icon_scatter_widget.size_hint = (None,None)
        self.icon_scatter_widget.pos = self.pos
        self.icon_scatter_widget.size = (35, 35)
        self.icon_scatter_widget.environmental_manager = self

        self.packet_stream = Scatter()
        self.packet_stream.size_hint = (None,None)
        self.packet_stream.pos = self.icon_scatter_widget.pos
        self.packet_stream.size = ("200sp","200sp")
        self.packet_stream.gui_manager = self
  
        self.packet_stream_scrollview = ScrollView()
        self.packet_stream_scrollview.scroll_distance = 50
        self.packet_stream_scrollview.size = ("500sp", "500sp")
        self.packet_stream_scrollview.pos = (0,"75sp")

        self.display_menu_button.add_widget(self.icon_image)
        self.icon_scatter_widget.add_widget(self.display_menu_button)
        self.container.add_widget(self.icon_scatter_widget)
        self.add_widget(self.container)

        self.icon_scatter_widget.pos = self.pos

        if self.ip_banned_on_creation == True: #check to see if this ip is banned
            self.block()

        


    def block(self, *button: Button) -> None:

        """
        Block IP -- not implmented
        """
   
        if self.banned == False: #check to see if already banned
            
            self.icon_scatter_widget.add_widget(self.banned_image)
            self.gui_manager.banned_ips_array.append(self.id)
            self.banned = True



    def unblock(self, *button: Button) -> None:

        """
        Unblock IP -- not implemented
        """

        if self.banned == True: #make sure ip has already been banned

            self.icon_scatter_widget.remove_widget(self.banned_image)
            self.gui_manager.banned_ips_array.remove(self.id) #remove from tracking array
            self.banned = False

   



    def remove_whois_popup(self, button: Button) -> None:

        """
        Remove whois popup for associated IP
        """

        self.gui_manager.persistent_widget_container.remove_widget(self.whois_popup)
        self.whois_popup = None
        self.display_whois_popup = False



    def display_whois(self, button: Button) -> None:

        """
        Display whois information for associated IP. 
        """

        if self.display_whois_popup == False:
            self.display_whois_popup = True

            self.whois_popup = Scatter(size_hint= (None, None), size= ("375sp","125sp"), pos=(self.menu_popup.pos[0], self.menu_popup.pos[1]+sp(150)))

            dismiss_button = Button(text="Dismiss Whois & Abuse (email)", background_color = [1,1,1,.2])
            dismiss_button.bind(on_press=self.remove_whois_popup)

            if self.whois_popup.pos[0] + sp(375) > self.window_x:
                self.whois_popup.pos = (self.window_x - sp(375), self.whois_popup.pos[1])

            if self.whois_popup.pos[1] + sp(125) > self.window_y:
                self.whois_popup.pos = (self.whois_popup.pos[0], self.window_y - sp(125))

            grid_layout = GridLayout(cols=1, size_hint=(None,None), size= ("350sp", "105sp"), pos = ("15sp", "15sp"))

            ip_whois_info_label = Label(text = str(self.whois_description))
            
            try:
                ip_whois_abuse_emails_label = Label(text = str(self.gui_manager.ip_whois_info_dict[self.id]["nets"][0]['emails']))
            except KeyError as e:
                ip_whois_abuse_emails_label = Label(text = "None")

            grid_layout.add_widget(ip_whois_info_label)
            grid_layout.add_widget(ip_whois_abuse_emails_label)

            grid_layout.add_widget(dismiss_button)

            self.whois_popup.add_widget(grid_layout)
            self.gui_manager.persistent_widget_container.add_widget(self.whois_popup)



    def display_menu(self) -> None:

        """
        Create popup menu when user clicks on IP widget.
        """
    

        if self.display_popup == False:
            self.display_popup = True

            packet_count = self.ip_data['packet_count']
            data_in = self.ip_data['data_in']
            data_out = self.ip_data['data_out']

            self.menu_popup = Scatter()
            self.menu_popup.size_hint = (None, None) 
            self.menu_popup.size = ("375sp", "155sp") 
            self.menu_popup.pos = (self.icon_scatter_widget.pos[0] +25 , self.icon_scatter_widget.pos[1]+25) 
            self.menu_popup.id = self.id + 'p' 
            
            if self.menu_popup.pos[0] + sp(350) > self.window_x:
                self.menu_popup.pos = (self.window_x - sp(375), self.menu_popup.pos[1])

            if self.menu_popup.pos[1] + sp(155) > self.window_y:
                self.menu_popup.pos = (self.menu_popup.pos[0], self.window_y - sp(150))


            grid_layout = GridLayout()
            grid_layout.cols = 2
            grid_layout.size_hint = (None,None)
            grid_layout.size = ('350sp', '125sp')
            grid_layout.pos = ("15sp","15sp")

            ip = Label()
            ip.text = "IP: " + self.id

            country = Label()
            country.text = "Country: " + self.country_label

            city_label = Label()
            city_label.text = "City: " + self.city_label

            packet_label = Label()
            packet_label.text = "Packet Count: " + str(packet_count)

            data_from_label = Label()
            data_from_label.text = f"Data From (MB): {data_in/1000000.0:.6f}"

            data_to_label = Label()
            data_to_label.text = f"Data To (MB): {data_out/1000000.0:.6f}"

            block_button = Button()
            block_button.text = "Block"
            block_button.background_normal = "../assets/images/buttons/red.png"
            block_button.background_down = "../assets/images/buttons/red_down.png"
            block_button.bind(on_press=self.block)

            whois_button = Button()
            whois_button.text = "Whois & Abuse"
            whois_button.background_normal = "../assets/images/buttons/orange.png"
            whois_button.background_down = "../assets/images/buttons/orange_down.png"
            whois_button.bind(on_press=self.display_whois)

            unblock_button = Button(text="Unblock", background_normal = "../assets/images/buttons/green.png", background_down="..images/buttons/green_down.png")
            unblock_button.bind(on_press=self.unblock)

            dismiss_button = Button()
            dismiss_button.text="Dismiss"
            dismiss_button.background_color = [1,1,1,.1]
            dismiss_button.bind(on_press=self.remove_popup)

            grid_layout.add_widget(ip)
            grid_layout.add_widget(country)
            grid_layout.add_widget(packet_label)
            grid_layout.add_widget(city_label)
            grid_layout.add_widget(data_from_label)
            grid_layout.add_widget(data_to_label)
            grid_layout.add_widget(block_button)
            grid_layout.add_widget(whois_button)
            grid_layout.add_widget(unblock_button)
            grid_layout.add_widget(dismiss_button)

            self.menu_popup.add_widget(grid_layout)
            self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)

                


    def remove_popup(self, button: Button) -> None:

        """
        Remove IP widget display popup.  
        """

        self.gui_manager.persistent_widget_container.remove_widget(self.menu_popup)
        self.menu_popup = None
        self.display_popup = False 


    def set_mercator_layout(self) -> None:

        """
        Called when screenmanager view is changed to mercator view.
        """
        self.pos  = self.mercator_position
        self.icon_scatter_widget.pos = self.mercator_position

 


    def set_graph_layout(self) -> None:

        """
        Called when screenmanager view is changed to graph view.
        """
        
        self.pos = self.graph_position
        self.icon_scatter_widget.pos = self.graph_position

            

    def update(self, **kwargs) -> None:

        """
        Update GUI widget. Called every cycle. 
        """

        state = kwargs['state']
        last_packet = kwargs['last_packet']
        ip_index = kwargs['ip_index']
        city_number_of_ips = kwargs['city_number_of_ips']
        city_position = kwargs['city_widget'].icon_scatter_widget.pos

     

        if state == 'graph': #graph view update

            attach = kwargs['attach']
            draw_angle = kwargs['city_draw_angle']

            #Ensure ip widget stays on screen
            if self.x+50 > self.window_x:
                self.x = self.x - 500
                self.icon_scatter_widget.pos = self.pos
            elif self.x < 0:
                self.x = self.x + 500
                self.icon_scatter_widget.pos = self.pos
            elif self.y+50 > self.window_y:
                self.y = self.y - 500
                self.icon_scatter_widget.pos = self.pos
            elif self.y < 0:
                self.y = self.y + 500
                self.icon_scatter_widget.pos = self.pos
            ######

            
            if attach == True: #check to see if we are attached to city

                distance_to_city, x_distance, y_distance = distance_between_points(city_position, self.pos)

                if distance_to_city > 200: #if more than 200 pixels away from city

                    self.pos[0] += x_distance * self.spring_constant_1
                    self.pos[1] += y_distance * self.spring_constant_1
                    self.icon_scatter_widget.pos = self.pos

            
                if distance_to_city < 50: #if less than 50 pixels away from city

                    angle_slice = (2*pi) / city_number_of_ips
                    final_position = [city_position[0] + self.random_radius * cos( draw_angle + angle_slice*ip_index - (pi/2) ), city_position[1] + self.random_radius * sin( draw_angle + angle_slice*ip_index - (pi/2) )]

                    distance_to_position, x_distance, y_distance = distance_between_points(final_position, self.pos)

                    self.pos[0] = city_position[0] + x_distance 
                    self.pos[1] = city_position[1] + y_distance 
                    self.icon_scatter_widget.pos = self.pos


            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0-largest_data_from/to_IP --> 0-50 pixels (compares data relatively)
            data_in = map_to_range(self.ip_data['data_in'], 0, self.gui_manager.ip_largest_data_in, 0, 50 )
            data_out = map_to_range(self.ip_data['data_out'], 0, self.gui_manager.ip_largest_data_out, 0, 50 )
             
            x, y = self.icon_scatter_widget.pos
            
            #draw ip widget lines
            self.canvas.before.clear()
            with self.canvas.before:

                if self.connection_opacity > 0: #packet delta less than 20 seconds
            
                    self.gui_manager.country_dictionary[self.country][1][self.city][0].new_data_counter = time.time() 

                    if self.banned == True: Color(1,0,0, self.connection_opacity)
                      
                    else: #select appropriate color according to the protocol of the last packet
                        if last_packet == "TCP":
                            self.tcp_color[3] = self.connection_opacity
                            Color(rgba = self.tcp_color)
                        elif last_packet == "UDP":
                            self.udp_color[3] = self.connection_opacity
                            Color(rgba = self.udp_color)
                        elif last_packet == "OTHER":
                            self.other_color[3] = self.connection_opacity
                            Color(rgba = self.other_color) 

                else: #new packet delta greater than 20 seconds use grey color
                    Color(1,1,1,.3) 
      
                Line(points=(city_position[0]+ 25, city_position[1]+ 25, self.icon_scatter_widget.pos[0] + 20, self.icon_scatter_widget.pos[1] + 20), width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y, x + data_in, y], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y - sp(5), x + data_out, y - sp(5)], width=1)

                if self.menu_popup:
                    Color(1,1,1,.3)
                    Line(points=[self.icon_scatter_widget.pos[0] + sp(15), self.icon_scatter_widget.pos[1]+ sp(15), self.menu_popup.pos[0]+ sp(180), self.menu_popup.pos[1]+sp(16)] , width = sp(1) )

                    if self.whois_popup:
                        Color(1,1,1,.3)
                        Line(points=[self.menu_popup.pos[0]+ sp(180), self.menu_popup.pos[1]+ sp(16), self.whois_popup.pos[0]+ sp(180), self.whois_popup.pos[1]+ sp(14)] , width = sp(1) )

           


        elif state == 'mercator': #mercator update

            self.distance_to_city, self.x_distance, self.y_distance = distance_between_points(city_position, self.pos)

            if self.distance_to_city > 200: #if more than 200 pixels away from city

                    self.pos[0] += self.x_distance * self.spring_constant_1
                    self.pos[1] += self.y_distance * self.spring_constant_1
                    self.icon_scatter_widget.pos = self.pos

            if self.distance_to_city < 50: #if less than 50 pixels away from city

                angle_slice = (2*pi) / city_number_of_ips

                final_position = [city_position[0] + self.random_radius * cos(angle_slice*ip_index - (pi/2) ), city_position[1] + self.random_radius * sin(angle_slice*ip_index - (pi/2) )]
                final_position = [city_position[0] + self.random_radius * cos(angle_slice*ip_index - (pi/2) ), city_position[1] + self.random_radius * sin(angle_slice*ip_index - (pi/2) )]

                distance_to_position, x_distance, y_distance = distance_between_points(final_position, self.pos)

                self.pos[0] = city_position[0] + x_distance 
                self.pos[1] = city_position[1] + y_distance 
                self.icon_scatter_widget.pos = self.pos


            x, y = self.icon_scatter_widget.pos
            self.container.size = ("19sp", "19sp")

            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0-largest_data_from/to_IP --> 0-50 pixels (compares data relatively)
            data_in = map_to_range(self.ip_data['data_in'], 0, self.gui_manager.ip_largest_data_in, 0, 30.0 )
            data_out = map_to_range(self.ip_data['data_out'], 0, self.gui_manager.ip_largest_data_out, 0, 30.0 )

            self.canvas.before.clear()
            with self.canvas.before:

                if self.connection_opacity > 0: #connection opacity calculated from delta between packets
    
                    self.gui_manager.country_dictionary[self.country][1][self.city][0].new_data_counter = time.time() 

                    if self.banned == True:
                        Color(1,0,0, self.connection_opacity) #red color for banned (functionality not implemented)

                    else: #select appropriate color according to last packet protocol

                        if last_packet == "TCP":
                            self.tcp_color[3] = self.connection_opacity
                            Color(rgba = self.tcp_color)
                        elif last_packet == "UDP":
                            self.udp_color[3] = self.connection_opacity
                            Color(rgba = self.udp_color)
                        elif last_packet == "OTHER":
                            self.other_color[3] = self.connection_opacity
                            Color(rgba = self.other_color) 

                else: #old connection, line color is grey
                    Color(1,1,1,.3) 

                Line(points=[city_position[0]+ 10, city_position[1]+ 10,  self.icon_scatter_widget.pos[0] + 15, self.icon_scatter_widget.pos[1]+ 15], width=1)

              
                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y, x + data_in, y], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y- sp(5), x + data_out, y-sp(5)], width=1)

                if self.menu_popup:
                    Color(1,1,1,.1)
                    Line(points=[self.icon_scatter_widget.pos[0] + sp(15), self.icon_scatter_widget.pos[1]+ sp(15), self.menu_popup.pos[0]+ sp(180), self.menu_popup.pos[1]+sp(16)] , width = sp(1) )

                    if self.whois_popup:
                        Color(1,1,1,.2)
                        Line(points=[self.menu_popup.pos[0]+ sp(180), self.menu_popup.pos[1]+ sp(16), self.whois_popup.pos[0]+ sp(180), self.whois_popup.pos[1]+ sp(14)] , width = sp(1) )

#end of IP widget