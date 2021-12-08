# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.



from kivy.graphics import Color, Line
from kivy.metrics import sp
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.scatter import Scatter
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout


import sys
sys.path.append("..") # Adds higher directory to python modules path.
from math import sin, cos, pi
from utils import map_to_range, distance_between_points, angle_between_points, Icon_Scatter_Override



class Country_Widget(Widget):

    """
    GUI Widget for each geographic Country with member functions for displaying associated City and IP widgets.
    """

    def __init__(self, **kwargs):

        """
        Construct GUI widget and associated state.
        """
        
        super().__init__()

        #TODO: change name of x_ and y_ to screen_x and screen_y
        self.x_ = kwargs['x_cord']
        self.y_ = kwargs['y_cord']
        self.center_x = kwargs['center_x']
        self.center_y = kwargs['center_y']
        self.window_x = kwargs['window_x']
        self.window_y = kwargs['window_y']
        self.scale_array = kwargs['scale_array']
        self.country = kwargs['country']
        self.country_code = kwargs['country_code'].lower()
        self.gui_manager = kwargs['gui_manager']
        self.country_color = self.gui_manager.config_variables_dict["country_color"]

        self.pos = (self.x_, self.y_)
        self.old_pos = self.pos
        self.spring_constant_k = 0.07
        self.spring_constant_k1 = 0.07
        self.draw_angle = 0
        self.total_city_widgets = 1
        self.total_data_in = 1
        self.total_data_out = 1
        self.city_draw_angles = [0, 0]

        self.display_popup = False
        self.banned = False
        self.attach = False
        self.do_layout = True
        self.show = True
        self.mercator_show = True
        self.new_data = True
        self.show_city_widgets = False
        self.show_all_widgets = False

        


        ##Create GUI widgets
        self.label = Label()
        self.label.text = self.country
        self.label.pos = (sp(-15), sp(7))
        self.label.font_size = sp(self.scale_array[1]*15) 
        
        self.container = FloatLayout()
        self.container.pos = self.pos 
        self.container.size_hint = (None, None) 
        self.container.size = (sp(50), sp(50))

        self.icon_image = Image()
        self.icon_image.source = '../assets/images/country_icons/{country}.png'.format(country=self.country)
        self.icon_image.size_hint = (None, None)
        self.icon_image.size = (40, 40)
        #self.icon_image.size = (sp(40), sp(40))
        self.icon_image.pos = (sp(5), sp(5))
      
        self.banned_country_image = Image()
        self.banned_country_image.source='../assets/images/UI/banned.png'
        self.banned_country_image.size_hint=(None, None)
        self.banned_country_image.size= (40, 40)
        #self.banned_country_image.size=(sp(40), sp(40))
        self.banned_country_image.pos = (sp(5), sp(5))

        self.display_menu_button = Button()
        self.display_menu_button.on_press = self.display_menu 
        self.display_menu_button.size_hint = (None, None) 
        self.display_menu_button.size = (sp(27), sp(27)) 
        self.display_menu_button.pos = (sp(13), sp(13)) 
        self.display_menu_button.background_color = (1,1,1,0) 

        self.icon_scatter_widget = Icon_Scatter_Override()
        self.icon_scatter_widget.size_hint = (None,None) 
        self.icon_scatter_widget.pos=self.pos 
        self.icon_scatter_widget.size=(55, 55)
        #self.icon_scatter_widget.size=(sp(55),sp(55))  
        self.icon_scatter_widget.parent_widget = self 

        self.radius_slider = Slider()
        self.radius_slider.value_track = False
        self.radius_slider.min = 50
        self.radius_slider.max = self.window_x/4
        self.radius_slider.value = self.window_x/8

        self.radius_slider.cursor_height = sp(10)
        self.radius_slider.cursor_size = (sp(12), sp(5))
        self.radius_slider.source ='../assets/images/UI/slider.png'
        self.radius_slider.cursor_image = '../assets/images/UI/slider.png'
        self.radius_slider.padding = "16sp"

        self.display_menu_button.add_widget(self.icon_image)
        self.icon_scatter_widget.add_widget(self.display_menu_button)
        self.icon_scatter_widget.add_widget(self.label)
        self.container.add_widget(self.icon_scatter_widget)
        
        self.add_widget(self.container)

        #Graph view attributes
        self.state = 'graph'
        self.graph_position = self.pos
        #

        #Mercator view attributes
        self.intial_layout = False
        self.labels = False
        self.mercator_position = self.initalize_mercator_position(kwargs['country_index'])
        if self.gui_manager.current == "mercator": self.set_mercator_layout()
        #

      
            

    def circular_display(self) -> None:

        """
        Display associated City and IP widgets in a circle.
        """   

        for i, city in enumerate(self.gui_manager.country_dictionary[self.country][1]):
  
            total_city_ip_count = len(self.gui_manager.country_dictionary[self.country][1][city]) - 1
            city_x, city_y = self.calculate_ip_positions(i, self.total_city_widgets+1, 2*pi)
            
            for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][city]):
                if n == 0: #city widget is first object in country_dictionary array[0]
                    city_widget = ip
                    angle_slice = (pi) / total_city_ip_count
                    city_widget.pos = (self.pos[0] + city_x,  self.pos[1] + city_y)  
                    city_widget.icon_scatter_widget.pos = city_widget.pos
                    continue

                draw_angle = angle_between_points(self.icon_scatter_widget.pos, city_widget.icon_scatter_widget.pos)

                #IP position: city position + radius(150) * cos/sin(angle to city + positional slice of angle - angle offset) 
                final_position = [city_widget.pos[0] + 150 * cos( draw_angle + (angle_slice)*n - (pi/2)) , city_widget.pos[1] + 150 * sin( draw_angle + angle_slice*n - (pi/2) )]
                ip.pos = final_position 
                ip.icon_scatter_widget.pos = ip.pos

  

    def circular_display_from_mycomputer(self) -> None:

        """
        Duplicate function to display associated City and IP widgets in different configuration when called from Computer widget. 
        """   

        for i, city in enumerate(self.gui_manager.country_dictionary[self.country][1]):

            total_city_ip_count = len(self.gui_manager.country_dictionary[self.country][1][city])
            city_x, city_y = self.calculate_ip_positions(i, self.total_city_widgets+1, pi)

            for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][city]):

                if n == 0: #city widget is first object in country_dictionary array[0]
                    city_widget = ip
                    angle_slice = (pi) / total_city_ip_count
                    city_widget.pos = (self.pos[0] + city_x,  self.pos[1] + city_y)  
                    city_widget.icon_scatter_widget.pos = city_widget.pos
                    continue

                draw_angle = angle_between_points(self.icon_scatter_widget.pos, city_widget.icon_scatter_widget.pos)

                #IP position: city position + radius(150) * cos/sin(angle to city + positional slice of angle - angle offset) 
                final_position = [city_widget.pos[0] + 150 * cos( draw_angle + (angle_slice)*n - (pi/2)) , city_widget.pos[1] + 150 * sin( draw_angle + angle_slice*n - (pi/2) )]
                ip.pos = final_position 
                ip.icon_scatter_widget.pos = ip.pos




    def toggle_city_widgets(self) -> None:

        """
        Toggle display of all associated City widgets.
        """

        if self.show_city_widgets == True:
            self.show_city_widgets = False

            if self.state == 'graph':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    for ip in self.gui_manager.country_dictionary[self.country][1][city]:
                        ip.show = False

            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    self.gui_manager.country_dictionary[self.country][1][city][0].mercator_show = False
                   
        else:

            self.show_city_widgets = True
            if self.state == 'graph':

                for city in self.gui_manager.country_dictionary[self.country][1]:
                   self.gui_manager.country_dictionary[self.country][1][city][0].show = True
             

            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    self.gui_manager.country_dictionary[self.country][1][city][0].mercator_show = True
                  


        

    def toggle_all_widgets(self) -> None:

        """
        Toggle display of associated City and IP widgets.
        """   

        if self.show_all_widgets == True:

            self.show_all_widgets = False
            self.show_city_widgets = False

            if self.state == 'graph':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    self.gui_manager.country_dictionary[self.country][1][city][0].show_ip_widgets = False #set display flag for city widgets

                    for ip in self.gui_manager.country_dictionary[self.country][1][city]:
                        ip.show = False
              
            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    for ip in self.gui_manager.country_dictionary[self.country][1][city]:
                        ip.mercator_show = False
        else:

            self.show_all_widgets = True
            self.show_city_widgets = True

            if self.state == 'graph':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    self.gui_manager.country_dictionary[self.country][1][city][0].show_ip_widgets = True #set display flag for city widgets

                    for ip in self.gui_manager.country_dictionary[self.country][1][city]:
                        ip.show = True

            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    total_count = len(self.gui_manager.country_dictionary[self.country][1][city])

                    for n, ip in enumerate(self.gui_manager.country_dictionary[self.country][1][city][1:]):   
                        self.x_, self.y_ = self.calculate_ip_positions(n, total_count, 2*pi)
                        ip.new_pos = (self.x_, self.y_)
                        ip.pos = (ip.longitude_x + self.x_,   ip.latitude_y + self.y_)  
                        ip.icon_scatter_widget.pos = ip.pos
                        ip.mercator_show = True



    
    def toggle_city_labels(self) -> None:

        """
        Toggles City widget labels on/off
        """
        
        if self.labels == True: 
            if self.state == 'graph':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    city_widget = self.gui_manager.country_dictionary[self.country][1][city][0]
                    city_widget.icon_scatter_widget.remove_widget(city_widget.label)
                    self.labels = False

            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    city_widget = self.gui_manager.country_dictionary[self.country][1][city][0]
                    city_widget.icon_scatter_widget.remove_widget(city_widget.label)
                    self.labels = False

        else:
            if self.state == 'graph':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    city_widget = self.gui_manager.country_dictionary[self.country][1][city][0]
                    city_widget.icon_scatter_widget.add_widget(city_widget.label)
                    self.labels = True

            elif self.state == 'mercator':
                for city in self.gui_manager.country_dictionary[self.country][1]:
                    city_widget = self.gui_manager.country_dictionary[self.country][1][city][0]
                    city_widget.icon_scatter_widget.add_widget(city_widget.label)
                    self.labels = True


   

    def attach_to_children(self) -> None:

        """
        Toggle attach/detach for City widgets to follow when Country widget is moved.
        """
    
        if self.attach == True:
            self.attach_button.text = "Attach"
            self.attach = False

        else:
            self.attach_button.text = "Detach"
            self.attach = True

    
    
    def calculate_ip_positions(self, ip_position: int, total_count: int, pi_radius: float) -> tuple[float, float]:

        """
        Determine x, y position for IP and City widgets.
        """

        pi_slice = (pi_radius)/total_count
        radius = self.radius_slider.value 

        if ip_position == 0:
            x = radius * self.city_draw_angles[0]
            y = radius * self.city_draw_angles[1]

            return x, y
        
        #BUG: issue with country draw angle being assigned after one cycle before ip widgets get displayed. requires double click
        x = radius * sin(pi_slice * ip_position + self.country_draw_angle )
        y = radius * cos(pi_slice * ip_position + self.country_draw_angle ) 

        return x, y




    def display_menu(self) -> None:

        """
        Create popup menu when user clicks on the Country widget.
        """

        if self.display_popup == False:
            self.display_popup = True

            data_from_label = Label()
            data_from_label.text = "Data From (MB): " + str(self.total_data_in/1000000.0)
            data_from_label.font_size = sp(self.scale_array[1]*15)
            data_from_label.border = (0,0,0,0)
         
         
            data_to_label = Label()
            data_to_label.text = text="Data To (MB): " + str(self.total_data_out/1000000.0)
            data_to_label.font_size = sp(self.scale_array[1]*15)
            data_to_label.border = (0,0,0,0)

            toggle_city_widgets_button = Button()
            toggle_city_widgets_button.text = "Toggle Cities"
            toggle_city_widgets_button.on_press = self.toggle_city_widgets
            toggle_city_widgets_button.background_normal = '../assets/images/buttons/teal.png'
            toggle_city_widgets_button.background_down = '../assets/images/buttons/teal_down.png'
            toggle_city_widgets_button.font_size = sp(self.scale_array[1]*15)
            toggle_city_widgets_button.border = (0,0,0,0) 


            toggle_all_widgets_button = Button()
            toggle_all_widgets_button.text = "Toggle Everything"
            toggle_all_widgets_button.on_press = self.toggle_all_widgets
            toggle_all_widgets_button.background_normal = '../assets/images/buttons/darkblue.png'
            toggle_all_widgets_button.background_down = '../assets/images/buttons/darkblue_down.png'
            toggle_all_widgets_button.font_size = sp(self.scale_array[1]*15)
            toggle_all_widgets_button.border = (0,0,0,0)


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


            circular_display_button = Button()
            circular_display_button.text = "Circular Display"
            circular_display_button.on_press=self.circular_display
            circular_display_button.background_normal='../assets/images/buttons/purple.png'
            circular_display_button.background_down='../assets/images/b uttons/purple_down.png'
            circular_display_button.font_size = sp(self.scale_array[1]*15)
            circular_display_button.border=(0,0,0,0)
             

            if self.attach:

                self.attach_button = Button()
                self.attach_button.text = "Detach"
                self.attach_button.on_press = self.attach_to_children
                self.attach_button.background_normal = '../assets/images/buttons/lightblue.png'
                self.attach_button.background_down = '../assets/images/buttons/lightblue_down.png'
                self.attach_button.font_size = sp(self.scale_array[1]*15)
                self.attach_button.border = (0,0,0,0)

            else:

                self.attach_button = Button()
                self.attach_button.text = "Attach"
                self.attach_button.on_press = self.attach_to_children
                self.attach_button.background_normal = '../assets/images/buttons/lightblue.png'
                self.attach_button.background_down = '../assets/images/buttons/lightblue_down.png'
                self.attach_button.font_size = sp(self.scale_array[1]*15)
                self.attach_button.border = (0,0,0,0)


            dismiss_button = Button() 
            dismiss_button.text="Dismiss"
            dismiss_button.background_color = [1, 1, 1,.1]
            dismiss_button.font_size = sp(self.scale_array[1]*15)
       

            grid = GridLayout(cols=1, size_hint=(None,None), pos=(sp(self.scale_array[0]*15), sp(self.scale_array[0]*15)), size= (sp(self.scale_array[0]*175), sp(self.scale_array[0]*185)))

            self.menu_popup = Scatter()

            self.menu_popup.size_hint = (None, None)
            self.menu_popup.size = (sp(self.scale_array[0]*200),sp(self.scale_array[1]*200) )
            self.menu_popup.pos = (self.icon_scatter_widget.pos[0], self.icon_scatter_widget.pos[1] + 50)
            self.menu_popup.id = self.country


            if self.menu_popup.pos[0] + sp(self.scale_array[0]*200) > self.window_x:
                self.menu_popup.pos = (self.window_x - sp(self.scale_array[0]*210) , self.menu_popup.pos[1])

            if self.menu_popup.pos[1] + sp(self.scale_array[1]*200) > self.window_y:
                self.menu_popup.pos = (self.menu_popup.pos[0] , self.window_y - sp(self.scale_array[1]*200))


            dismiss_button.bind(on_press=self.remove_popup)

            if self.state == 'graph':

                graph_label = Label()
                graph_label.text = self.country
                graph_label.font_size = sp(self.scale_array[1]*15)
                graph_label.border=(0,0,0,0)

                grid.add_widget(graph_label)
                grid.add_widget(data_from_label)
                grid.add_widget(data_to_label)
                grid.add_widget(toggle_city_widgets_button)
                grid.add_widget(toggle_all_widgets_button)
                grid.add_widget(self.radius_slider)
                grid.add_widget(circular_display_button)
                grid.add_widget(self.attach_button)
                grid.add_widget(dismiss_button)

                self.menu_popup.add_widget(grid)
                self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)


            elif self.state == 'mercator':      

                hide_labels = Button()
                hide_labels.text="Toggle Labels"
                hide_labels.on_press = self.toggle_city_labels
                hide_labels.background_normal= "../assets/images/buttons/pink.png"
                hide_labels.background_down= "../assets/images/buttons/pink_down.png"
                hide_labels.font_size = sp(self.scale_array[1]*15)
                hide_labels.border= (0,0,0,0)

                mercator_label = Label()
                mercator_label.text=self.country
                mercator_label.font_size = sp(self.scale_array[1]*15)
                mercator_label.border=(0,0,0,0)
                
                grid.add_widget(mercator_label)
                grid.add_widget(data_from_label)
                grid.add_widget(data_to_label)
                grid.add_widget(toggle_city_widgets_button)
                grid.add_widget(toggle_all_widgets_button)
                grid.add_widget(hide_labels)
                grid.add_widget(dismiss_button)

                self.menu_popup.add_widget(grid)
                self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)

            


    def remove_popup(self, button: Button) -> None:

        """
        Remove city widget display popup.  
        """

        self.gui_manager.persistent_widget_container.remove_widget(self.menu_popup)
        self.display_popup = False



  
    def set_graph_layout(self) -> None:

        """
        Called when screenmanager view is changed to graph view - changes widget size and position.
        """
        
        self.canvas.before.clear()
        
        self.pos = self.graph_position
        self.icon_scatter_widget.size = (55,55)

        self.icon_image.size = (40,40)
        self.banned_country_image.size = (40,40)

        self.display_menu_button.pos = (13,13)
        self.display_menu_button.size = (27,27)

        try:
            self.icon_scatter_widget.add_widget(self.label)
        except:
            pass

    def initalize_mercator_position(self, position: int) -> tuple[float, float]:

        """
        Initalize mercator position for countries. 
        """

        if position < 15:
            x_offset = 10
        elif position > 15 and position < 30:
            x_offset = 40
            position = position - 16 
        elif position > 30 and position < 45:
            x_offset = 70
            position = position - 30
        elif position > 45 and position < 60:
            x_offset = 100
            position = position - 45
        elif position > 60 and position < 75:
            x_offset = 130
            position = position - 60
        elif position > 75 and position < 90:
            x_offset = 160
            position = position - 75
        elif position > 90 and position < 105:
            x_offset = 190
            position = position - 90
        elif position > 105 and position < 120:
            x_offset = 220
            position = position - 105
        elif position > 120 and position < 135:
            x_offset = 250
            position = position - 120
        elif position > 135 and position < 150:
            x_offset = 280
            position = position - 135
        elif position > 150 and position < 165:
            x_offset = 320
            position = position - 150
        elif position > 165 and position < 180:
            x_offset = 350
            position = position - 165
        else: 
            x_offset = 380
            position = position - 180

        return (sp(x_offset), sp(50 + (position+1) * 30))



    def set_mercator_layout(self) -> None:

        """
        Called when screenmanager view is changed to mercator view - changes widget size and position.
        """
        

        self.icon_scatter_widget.size = (sp(30),sp(30))

        self.icon_scatter_widget.pos = self.mercator_position
     
        self.icon_image.size = (sp(20),sp(20))
        self.icon_image.pos = (sp(4),sp(4))

        self.banned_country_image.size = (sp(20),sp(20))
        self.banned_country_image.pos = (sp(4),sp(4))

        self.display_menu_button.pos = (sp(4),sp(4))
        self.display_menu_button.size = (sp(18),sp(18)) 

        self.icon_scatter_widget.remove_widget(self.label)
        



    def update(self, **kwargs) -> None:

        """
        Update GUI widget. Called every cycle. 
        """

        self.state = kwargs['state']
        
        if self.state == 'graph': #graph view

            my_computer_position = self.gui_manager.my_computer.icon_scatter_widget.pos


            # Make sure Country widget doesn't go off screen
            if self.x+50 > self.window_x:
                self.x = self.x - 150
                self.icon_scatter_widget.pos = self.pos

            if self.x < 0:
                self.x = self.x + 250
                self.icon_scatter_widget.pos = self.pos

            if self.y+50 > self.window_y:
                self.y = self.y - 150
                self.icon_scatter_widget.pos = self.pos

            if self.y < 0:
                self.y = self.y + 50
                self.icon_scatter_widget.pos = self.pos

     
            if self.do_layout == True: #only do layout if Icon_scatter_overide is not being dragged

                attach = kwargs['attach']
                if attach == True: #update position if widget is attached to parent 
             
                    distance, x_distance, y_distance = distance_between_points(my_computer_position, self.pos) #calculate time-step distance (linear interpolation)

                    if (distance > 500): #greater than 500 pixels
                        self.pos[0] += x_distance * self.spring_constant_k
                        self.pos[1] += y_distance * self.spring_constant_k
          
                    elif (distance < 200): #less than 200 pixels
                        self.pos[0] -= x_distance * self.spring_constant_k1
                        self.pos[1] -= y_distance * self.spring_constant_k1
                        
                self.icon_scatter_widget.pos = self.pos
                        
            
            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0-largest_data_from_country --> 0-50 pixels (compare data relatively)
            data_in = map_to_range(self.total_data_in, 0, self.gui_manager.country_largest_data_in, 0, 50.0 )
            data_out = map_to_range(self.total_data_out, 0, self.gui_manager.country_largest_data_out, 0, 50.0 )
            
            x, y = self.icon_scatter_widget.pos

            #draw connecting lines
            self.canvas.before.clear()
            with self.canvas.before:


                Color(rgba=self.country_color) if self.new_data else Color(1, 1, 1, .1)     
                Line(points=(my_computer_position[0]+ 35, my_computer_position[1] + 35, self.icon_scatter_widget.pos[0]+20, self.icon_scatter_widget.pos[1]+20), width=2)

                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y, x + data_in, y], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y-sp(5), x + data_out, y-sp(5)], width=1)


        elif self.state == 'mercator': #mercator update


            #map data from bytes to pixel length (green and blue lines) 
            #range is mapped from 0 - largest_data_from_country --> 0-50 pixels (compare data relatively)
            data_in = map_to_range(self.total_data_in, 0, self.gui_manager.country_largest_data_in, 0, 50.0 )
            data_out = map_to_range(self.total_data_out, 0, self.gui_manager.country_largest_data_out, 0, 50.0 )

            x, y = self.icon_scatter_widget.pos

            self.canvas.before.clear()
            with self.canvas.before: 
                
                Color(rgba = self.gui_manager.config_variables_dict['Data IN'])
                Line(points=[x, y+2, x + data_in, y+2], width=1)

                Color(rgba = self.gui_manager.config_variables_dict['Data OUT'])
                Line(points=[x, y-sp(5), x + data_out, y-sp(5)], width=1)


#End of Country_Widget