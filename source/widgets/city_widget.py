# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.


import os
import sys 
sys.path.append("..") # Adds higher directory to python modules path.
import time
from utils import map_to_range, Icon_Scatter_Override
from random import random, randrange
from math import sin, pi, cos, sqrt

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line
from kivy.metrics import sp





class City_Widget(Widget):

    """
    GUI Widget for each geographic city with member functions for displaying associated IP widgets.
    """

    def __init__(self, **kwargs) -> None:

        """
        Construct GUI widget and associated state.
        """

        super().__init__()

        self.gui_manager = kwargs['gui_manager']
        self.city_color = self.gui_manager.config_variables_dict["city_color"]
        self.x_coordinate_country = kwargs['x_cord_country']
        self.y_coordinate_country = kwargs['y_cord_country']
        self.center_x = kwargs['center_x']
        self.center_y = kwargs['center_y']
        self.window_x = kwargs['window_x']
        self.window_y = kwargs['window_y']
        self.scale_array = kwargs['scale_array']
        self.country = kwargs['country']
        self.city = kwargs['city'] 
        self.city_label = 'Unresolved' if self.city == None else self.city
        self.latitude = kwargs['latitude']
        self.longitude = kwargs['longitude']
        self.longitude_x = kwargs['longitude_x']
        self.latitude_y = kwargs['latitude_y']

        
        self.random_radius = randrange(sp(300), sp(500))
        self.attach = True
        self.show = False
        self.do_layout = True
        self.display_popup = False
        self.new_data = True
        self.show_ip_widgets = False
        self.total_data_out = 0
        self.total_data_in = 0
        self.draw_angle = 0
        self.k = 0.07
        self.k_1 = .07
        self.spring_constant_1 = 0.1        
        self.total_count = 1
        self.state = 'graph'
        self.new_data_counter = time.time() 
        self.x_, self.y_ = self.set_position()
        self.pos = (self.x_, self.y_)
        self.old_pos = self.pos


        ##Create GUI widget
        self.label = Label()
        self.label.text=self.city_label
        self.label.pos = (-30,10) 
        self.label.font_size = sp(self.scale_array[1]*15) 
        self.label.font_blended = False 
        self.label.font_hinting = 'normal'  
   
        self.container = FloatLayout()
        self.container.pos = self.pos 
        self.container.size_hint = (None,None) 
        self.container.size = ("50sp", "50sp") 

        self.icon_image = Image()
        self.icon_image.source='../assets/images/UI/city.png'
        self.icon_image.size_hint=(None, None)
        self.icon_image.size=(40, 40)
        #self.icon_image.size=("40sp", "40sp")
        self.icon_image.pos = ("6sp", "5sp")

        self.display_menu_button = Button()
        self.display_menu_button.on_press=self.display_menu 
        self.display_menu_button.size_hint=(None, None) 
        self.display_menu_button.size=("25sp", "25sp") 
        self.display_menu_button.pos=("13sp","13sp") 
        self.display_menu_button.background_color=(1,1,1,0) 

        self.icon_scatter_widget = Icon_Scatter_Override()
        self.icon_scatter_widget.size_hint = (None,None)
        self.icon_scatter_widget.pos=self.pos
        #self.icon_scatter_widget.size=("55sp","55sp")
        self.icon_scatter_widget.size=(55,55)
        self.icon_scatter_widget.parent_widget = self

        self.display_menu_button.add_widget(self.icon_image)
        self.icon_scatter_widget.add_widget(self.display_menu_button)
        self.icon_scatter_widget.add_widget(self.label)
        self.container.add_widget(self.icon_scatter_widget)
        self.add_widget(self.container)
        self.icon_scatter_widget.pos = (self.x_, self.y_)


        #Mercator view state
        self.intial_layout = False
        self.mercator_position = (self.longitude_x, self.latitude_y)
        if self.gui_manager.current == "mercator": self.set_mercator_layout()
        self.mercator_show = True
        self.is_city = True
        self.ip_do_layout = False 
        #

        #Graph view state
        self.graph_position = self.icon_scatter_widget.pos
        #        

        


    
    def circular_display(self) -> None:

        """
        Display associated IP widgets in a circle.
        """   
     
        for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][self.city][1:]): #access relevant IP widgets
            self.x_, self.y_ = self.set_position_for_ip_widgets(n, self.total_count-1)
            ip.new_pos = (self.x_, self.y_)
            ip.pos = (self.pos[0] + self.x_,   self.pos[1] + self.y_)  
            ip.icon_scatter_widget.pos = ip.pos


    
    def toggle_display_ips(self) -> None:

        """
        Toggle display of all associated IP widgets.
        """

        if self.show_ip_widgets == True:
            self.show_ip_widgets = False

            if self.state == 'graph':
                for ip in self.gui_manager.country_dictionary[self.country][1][self.city][1:]: #access associated IP widgets
                    ip.show = False
                    self.gui_manager.layout.remove_widget(ip)

            elif self.state == 'mercator':
                for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][self.city][1:]): #access associated IP widgets  
                    ip.mercator_show = False

        else:
            self.show_ip_widgets = True

            if self.state == 'graph':
                for ip in self.gui_manager.country_dictionary[self.country][1][self.city][1:]: #access associated IP widgets
                    ip.show = True

            elif self.state == 'mercator':
                for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][self.city][1:]): #access associated IP widgets
                    self.x_, self.y_ = self.set_position_for_ip_widgets(n, self.total_count)
                    ip.new_pos = (self.x_, self.y_)
                    ip.pos = (self.x_, self.y_)  
                    ip.icon_scatter_widget.pos = ip.pos
                    ip.mercator_show = True
    

    
    def set_position(self) -> tuple[float, float]:

        """
        Calculate random x and y screen position for city widget.
        """

        x = self.x_coordinate_country + sp(150) * sin(2*pi * random()) 
        y = self.y_coordinate_country + sp(150) * cos(2*pi * random())

        return x, y


    
    def set_position_for_ip_widgets(self, ip_position: int, total_count: int) -> tuple[float, float]:
        
        """
        Calculate x, y position using slider radius for associated IP widgets.
        """
        
        pi_slice = (2*pi)/(total_count)
        radius = self.radius_slider.value

        x = radius * sin(pi_slice * ip_position )
        y = radius * cos(pi_slice * ip_position ) 
        print("IP position---> ", ip_position)
        print("x-->", x)
        print("y-->", y)

        return x, y


    
    def distance_between_points(self, destination: tuple[float, float], source: tuple[float, float]) -> tuple[float, float, float]:

        """
        Find the distance between two points.
        """

        x_distance = destination[0] - source[0] 
        y_distance = destination[1] - source[1]
        distance = sqrt( x_distance*x_distance + y_distance*y_distance )

        return distance, x_distance, y_distance


    
    def attach_to_children(self) -> None:

        """
        Toggle attach/detach for IP widgets to follow city widget when moved.
        """

        if self.attach == True:
            self.attach_button.text = "Attach"
            self.attach = False

        else:
            self.attach_button.text = "Detach"
            self.attach = True



    
    def display_menu(self) -> None:
        
        """
        Create popup menu when user clicks on the City widget.
        """
    
        if self.display_popup == False:
            self.display_popup = True

            self.menu_popup = Scatter()
            self.menu_popup.size_hint = (None, None)
            self.menu_popup.size = (sp(self.scale_array[0]*210), sp(self.scale_array[1]*200))
            self.menu_popup.pos = (self.icon_scatter_widget.pos[0], self.icon_scatter_widget.pos[1] + 50)
            self.menu_popup.id = self.country

            if self.menu_popup.pos[0] + sp(self.scale_array[0]*175) > self.window_x:
                self.menu_popup.pos = (self.window_x - sp(self.scale_array[0]*175), self.menu_popup.pos[1])

            if self.menu_popup.pos[1] + sp(self.scale_array[1]*150) > self.window_y:
                self.menu_popup.pos = (self.menu_popup.pos[0], self.window_y - sp(self.scale_array[1]*160))


            grid_layout = GridLayout()
            grid_layout.cols = 1
            grid_layout.size_hint = (None,None)
            grid_layout.size = (sp(self.scale_array[0]*175), sp(self.scale_array[1]*150))
            grid_layout.pos = (sp(self.scale_array[0]*15),sp(self.scale_array[1]*15))
      

            city_label = Label()
            city_label.text = self.city_label
            city_label.font_size = sp(self.scale_array[1]*15)
            city_label.font_blended = False
            city_label.font_hinting = None


            data_from_label = Label()
            data_from_label.text = f"Data From (MB): {self.total_data_in/1000000.0:.6f}" 
            data_from_label.font_size = sp(self.scale_array[1]*15)
            data_from_label.font_blended = False
            data_from_label.font_hinting = None


            data_to_label = Label()
            data_to_label.text = f"Data To (MB): {self.total_data_out/1000000.0:.6f}"
            data_to_label.font_size = sp(self.scale_array[1]*15)
            data_to_label.font_blended = False
            data_to_label.font_hinting = None


            toggle_ips_button = Button()
            toggle_ips_button.text = "Toggle IP's"
            toggle_ips_button.on_press = self.toggle_display_ips
            toggle_ips_button.background_down = '../assets/images/buttons/darkblue.png'
            toggle_ips_button.background_normal = '../assets/images/buttons/darkblue_down.png'
            toggle_ips_button.font_size = sp(self.scale_array[1]*15)
            toggle_ips_button.border = (0,0,0,0)


            self.radius_slider = Slider()
            self.radius_slider.value_track = False
            self.radius_slider.min = 50
            self.radius_slider.max = self.window_x/4
            self.radius_slider.value = self.window_x/8
            self.radius_slider.cursor_height = sp(10)
            self.radius_slider.cursor_size = (sp(12), sp(5))
            self.radius_slider.source = '../assets/images/UI/slider.png'
            self.radius_slider.cursor_image = '../assets/images/UI/slider.png'
            self.radius_slider.padding = "16sp"


            circular_display = Button()
            circular_display.text = "Circular Display"
            circular_display.on_press = self.circular_display
            circular_display.background_normal = '../assets/images/buttons/purple.png'
            circular_display.background_down = '../assets/images/buttons/purple_down.png'
            circular_display.font_size = sp(self.scale_array[1]*15)
            circular_display.border = (0,0,0,0)


            
            if self.attach:                                                                                                                             
                self.attach_button = Button()
                self.attach_button.text = 'Detach'
                self.attach_button.on_press = self.attach_to_children
                self.attach_button.background_normal = '../assets/images/buttons/lightblue.png'
                self.attach_button.background_down = "../assets/images/buttons/lightblue_down.png"
                self.attach_button.font_size = sp(self.scale_array[1]*15)
                self.attach_button.border = (0,0,0,0)
               

            else:

                self.attach_button = Button()
                self.attach_button.text='Attach'
                self.attach_button.on_press = self.attach_to_children
                self.attach_button.background_normal = '../assets/images/buttons/lightblue.png'
                self.attach_button.background_down = "../assets/images/buttons/lightblue_down.png"
                self.attach_button.font_size = sp(self.scale_array[1]*15)
                self.attach_button.border = (0,0,0,0)


            dismiss_button = Button()
            dismiss_button.text = "Dismiss"
            dismiss_button.background_color = [.1, .1, .1,.8]
            dismiss_button.font_size = sp(self.scale_array[1]*15)

            dismiss_button.bind(on_press=self.remove_popup)


            if self.state == 'graph':
                grid_layout.add_widget(city_label)
                grid_layout.add_widget(data_from_label)
                grid_layout.add_widget(data_to_label)
                grid_layout.add_widget(toggle_ips_button)
                grid_layout.add_widget(self.radius_slider)
                grid_layout.add_widget(circular_display)
                grid_layout.add_widget(self.attach_button)
                grid_layout.add_widget(dismiss_button)

            elif self.state == 'mercator':
                grid_layout.add_widget(city_label)
                grid_layout.add_widget(data_from_label)
                grid_layout.add_widget(data_to_label)
                grid_layout.add_widget(toggle_ips_button)
                grid_layout.add_widget(self.radius_slider)
                grid_layout.add_widget(circular_display)
                grid_layout.add_widget(dismiss_button)
              
            self.menu_popup.add_widget(grid_layout)
            self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)

   
            
     
    def remove_popup(self, button: Button) -> None:

        """
        Remove city widget display popup.  
        """
      
        self.gui_manager.persistent_widget_container.remove_widget(self.menu_popup)
        self.display_popup = False




   
    def set_mercator_layout(self) -> None:

        """
        Called when screenmanager view is changed to mercator view - changes widget size, image and position.
        """
        
        self.label.pos = ("-30sp", "-30sp")
        self.label.font_size = sp(self.scale_array[1]*15)
        self.label.color = [1,1,1,1]

        self.icon_image.size = ("10sp", "10sp")
        self.icon_image.pos = ("3sp", "3sp")
        self.icon_image.source = '../assets/images/country_icons/{country}.png'.format(country=self.country) #change from city image to country image

        self.icon_scatter_widget.pos = self.mercator_position
        self.icon_scatter_widget.size = ("16sp", "16sp")

        self.container.size = ("19sp","19sp")

        self.display_menu_button.pos = ("3sp","3sp")
        self.display_menu_button.size = ("10sp","8sp")  

        self.icon_scatter_widget.remove_widget(self.label)

       
        
        

    def set_graph_layout(self) -> None:

        """
        Called once when screenmanager view is changed to graph view - changes widget size and city image
        """

        self.label.pos = (sp(-30),sp(10))
        self.label.font_size = sp(self.scale_array[1]*15)
        self.label.color = [1,1,1,1]

        self.icon_scatter_widget.pos = self.graph_position
        self.icon_scatter_widget.size = (55, 55)

        self.display_menu_button.pos = (13, 13)
        self.display_menu_button.size = (25,25)

        self.icon_image.source = '../assets/images/UI/city.png' #change from country image to city image
        self.icon_image.size = (40, 40)

        

        

        try: #bugged in kivy 
            self.icon_scatter_widget.add_widget(self.label)
        except:
            pass
    


    

    def update(self, **kwargs) -> None:

        """
        Update GUI widget. Called every cycle. 
        """

        self.state = kwargs['state']
        
        if self.state == 'graph': 

            country_position = kwargs['country_widget'].icon_scatter_widget.pos

            ##### So city widget doesn't go off screen
            if self.x+50 > self.window_x:
                self.x = self.x - 100
                self.icon_scatter_widget.pos = self.pos

            if self.x < 0:
                self.x = self.x + 100
                self.icon_scatter_widget.pos = self.pos

            if self.y+50 > self.window_y:
                self.y = self.y - 100
                self.icon_scatter_widget.pos = self.pos

            if self.y < 0:
                self.y = self.y + 100
                self.icon_scatter_widget.pos = self.pos
            #####
            
           
            if self.do_layout == True: # Prevents bug if icon_scatter_widget is being dragged 

                attach = kwargs['attach']
                if attach == True: #update position if widget is attached to parent 

                           
                    country_draw_angle = kwargs['country_draw_angle']
                    number_of_cities = kwargs['number_of_cities']
                    city_index = kwargs['city_index']
                    
             

                    distance_to_country, x_distance, y_distance = self.distance_between_points(country_position, self.pos)  #calculate time-step distance for linear interpolation

                    if distance_to_country > 300: #if widget is more than 300 pixels away from country
                            self.pos[0] += x_distance * self.spring_constant_1
                            self.pos[1] += y_distance * self.spring_constant_1
                            self.icon_scatter_widget.pos = self.pos

                    elif distance_to_country < 50: #if widget is less than 50 pixels away from country

                            angle_slice = (2*pi) / number_of_cities
                            new_position = [country_position[0] + self.random_radius * cos( country_draw_angle + angle_slice * city_index - (pi/2) ), country_position[1] + self.random_radius * sin( country_draw_angle + angle_slice * city_index - (pi/2) )]

                            distance_to_position, x_distance, y_distance = self.distance_between_points(new_position, self.pos)

                            self.pos[0] = country_position[0] + x_distance
                            self.pos[1] = country_position[1] + y_distance 
                            self.icon_scatter_widget.pos = self.pos


            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0-largest_data_from_city --> 0-50 pixels (compare data relatively)
            data_in = map_to_range(self.total_data_in, 0, self.gui_manager.city_largest_data_in, 0, 50.0 )
            data_out = map_to_range(self.total_data_out, 0, self.gui_manager.city_largest_data_out, 0, 50.0 )
            x, y = self.icon_scatter_widget.pos

            #draw connecting line and data sent/recieved lines (blue and green)
            self.canvas.before.clear()
            with self.canvas.before:
                
                
                Color(rgba=self.city_color) if self.new_data else Color(1, 1, 1, .1)
                Line(points=(country_position[0] + 20, country_position[1] + 20, self.icon_scatter_widget.pos[0]+20, self.icon_scatter_widget.pos[1]+20), width=1.3)


                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y, x + data_in, y], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y-sp(5), x + data_out, y-sp(5)], width=1)
         

        elif self.state == 'mercator': #mercator update


            #need these for drawing bezier curve
            self.dist_c, self.x_dist_c, self.y_dist_c = self.distance_between_points( ( self.gui_manager.my_computer.icon_scatter_widget.pos[0], self.gui_manager.my_computer.icon_scatter_widget.pos[1]), 
                                                                         (self.longitude_x, self.latitude_y)
                                                                        )

            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0-largest_data_from_city --> 0-50 pixels (compare data relatively)
            data_in = map_to_range(self.total_data_in, 0, self.gui_manager.city_largest_data_in, 0, 30.0 )
            data_out = map_to_range(self.total_data_out, 0, self.gui_manager.city_largest_data_out, 0, 30.0 )
            x, y = self.icon_scatter_widget.pos

            #draw bezier curves
            self.canvas.before.clear()
            with self.canvas.before:

                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y, x + data_in, y], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y-sp(5), x + data_out, y-sp(5)], width=1)


            

                Color(rgba=self.city_color) if self.new_data else Color(1, 1, 1, .1)
                try: #self.latiitude sometimes "unresolved"
                    if self.latitude > 0:
                        Line(bezier=( 
                                    self.icon_scatter_widget.pos[0] + sp(5), self.icon_scatter_widget.pos[1] + sp(5) , 
                                    self.longitude_x + (self.x_dist_c/2), self.latitude_y+(.3*self.dist_c),
                                    self.gui_manager.my_computer.icon_scatter_widget.pos[0] + sp(10), self.gui_manager.my_computer.icon_scatter_widget.pos[1]+ sp(10)
                                ),)
                    else:
                        Line(bezier=( 
                                    self.icon_scatter_widget.pos[0] + sp(5) , self.icon_scatter_widget.pos[1] + sp(5), 
                                    self.longitude_x + (self.x_dist_c/2), self.latitude_y-(.3*self.dist_c),
                                    self.gui_manager.my_computer.icon_scatter_widget.pos[0]+ sp(10), self.gui_manager.my_computer.icon_scatter_widget.pos[1]+ sp(10)
                                ),)
                except Exception as e:
                    #TODO
                    pass
                    # exc_type, exc_obj, exc_tb = sys.exc_info()
                    # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    # print(exc_type, fname, exc_tb.tb_lineno)
                
            



#end of City_Widget