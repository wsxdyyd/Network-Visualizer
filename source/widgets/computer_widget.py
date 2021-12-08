# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity. 

import sys
sys.path.append("..") # Adds higher directory to python modules path.
from utils import map_to_range
from math import sin, cos, pi

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import sp
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout






class My_Computer(Widget):

    """
    GUI Widget for representing the users computer with member functions for displaying Country, City, and IP widgets. 
    """

    def __init__(self, **kwargs) -> None:

        """
        Construct GUI widget and associated state.
        """
    
        super().__init__()

        self.pos = kwargs['center_position']
        self.window_x = kwargs['window_x']
        self.window_y = kwargs['window_y']
        self.scale_array = kwargs['scale_array']
        self.gui_manager = kwargs['gui_manager']
        
       
        self.interface_dictionary = self.gui_manager.interface_dictionary
        self.my_mac_address = self.gui_manager.my_mac_address
        
        self.display_popup = False
        self.toggle_all = False
        self.attach = False
        self.mercator_layout_finished = False
        self.toggle_countries_boolean = True
        self.toggle_cities_boolean = True
        self.graph_layout_finished = True

        self.total_data_out = 1
        self.total_data_in = 1
        self.graph_position = self.pos
        self.mercator_position = (self.center_x-100, 80) #default value in case IP is not in geoIP database



        ##Create GUI widgets
        self.label = Label()
        self.label.text = "My Computer"
        self.label.font_size = sp(self.scale_array[1]*15)
        
        self.container = FloatLayout()
        self.container.pos= self.pos
        self.container.size_hint=(None,None)
        self.container.size = (sp(self.scale_array[0]*50), sp(self.scale_array[1]*50))
        
        self.icon_image = Image()
        self.icon_image.source='../assets/images/UI/computer_icon.png'
        self.icon_image.size_hint=(None, None)
        self.icon_image.size=(sp(self.scale_array[0]*40), sp(self.scale_array[1]*40))
        self.icon_image.pos = (sp(10),sp(10))

        self.display_menu_button = Button()
        self.display_menu_button.on_press=self.display_menu
        self.display_menu_button.size_hint=(None, None)
        self.display_menu_button.size=(sp(self.scale_array[0]*30), sp(self.scale_array[1]*30))
        self.display_menu_button.pos=(sp(15),sp(13))
        self.display_menu_button.background_color=(0,0,0,0)

        self.icon_scatter_widget = Scatter()
        self.icon_scatter_widget.size_hint = (None,None)
        self.icon_scatter_widget.pos = self.pos
        self.icon_scatter_widget.size = (sp(self.scale_array[0]*60), sp(self.scale_array[1]*60))
        self.icon_scatter_widget.gui_manager = self


        self.display_menu_button.add_widget(self.icon_image)
        self.icon_scatter_widget.add_widget(self.display_menu_button)
        self.icon_scatter_widget.add_widget(self.label)
        self.container.add_widget(self.icon_scatter_widget)

        self.add_widget(self.container)



    def circular_display(self) -> None:

        """
        Display Country, City and IP widgets in a circle using slider.
        """  

        angle_slice = 2*pi / self.gui_manager.country_total_count

        for n, country in enumerate(self.gui_manager.country_dictionary):

            country_widget = self.gui_manager.country_dictionary[country][0]

            country_angle_x, country_angle_y = cos(angle_slice*n) , sin(angle_slice*n)
            country_widget.city_draw_angles = [country_angle_x, country_angle_y]
            
            new_pos = [self.icon_scatter_widget.pos[0] + self.radius_slider.value * country_angle_x, self.icon_scatter_widget.pos[1] + self.radius_slider.value * country_angle_y]
            country_widget.pos = new_pos
            country_widget.icon_scatter_widget.pos = new_pos
            country_widget.circular_display_from_mycomputer()



  
    def attach_to_children(self) -> None:

        """
        Toggle attach/detach for Country widgets to follow when moved.
        """

        if self.attach == True:
            self.attach_button.text = "Attach"
            self.attach = False
        else:
            self.attach_button.text = "Detach"
            self.attach = True




    def toggle_display_countries(self) -> None:
        
        """
        Toggle display of all Country widgets.
        """

        if self.toggle_countries_boolean == True:
            self.toggle_countries_boolean = False

            if self.state == 'graph':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].show = False #set toggle for country
                    for city in self.gui_manager.country_dictionary[country][1]:
                        self.gui_manager.country_dictionary[country][1][city][0].show_ip_widgets = False #set toggle for citys
                        for ip in self.gui_manager.country_dictionary[country][1][city]:
                            ip.show = False

            elif self.state == 'mercator':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].mercator_show = False

        else:
            self.toggle_countries_boolean = True

            if self.state == 'graph':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].show = True

            elif self.state == 'mercator':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].mercator_show = True


 
    def toggle_display_cities(self) -> None:

        """
        Toggle display of all City widgets.
        """

        if self.toggle_cities_boolean == True:
            self.toggle_cities_boolean = False

            if self.state == 'graph':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].show = True
                    self.gui_manager.country_dictionary[country][0].show_city_widgets = True #set toggle for country
                    for city in self.gui_manager.country_dictionary[country][1]:
                        self.gui_manager.country_dictionary[country][1][city][0].show = True

            elif self.state == 'mercator':
                for country in self.gui_manager.country_dictionary:
                    for city in self.gui_manager.country_dictionary[country][1]:
                        self.gui_manager.country_dictionary[country][1][city][0].mercator_show = True


        else:
            self.toggle_cities_boolean = True

            if self.state == 'graph':
                for country in self.gui_manager.country_dictionary:
                    self.gui_manager.country_dictionary[country][0].show_city_widgets = False #set toggle for country
                    for city in self.gui_manager.country_dictionary[country][1]:
                        for ip in self.gui_manager.country_dictionary[country][1][city]:
                            ip.show = False

            elif self.state == 'mercator':
                    for country in self.gui_manager.country_dictionary:
                        for city in self.gui_manager.country_dictionary[country][1]:
                            self.gui_manager.country_dictionary[country][1][city][0].mercator_show = False

            

            


    def toggle_all_widgets(self) -> None:

        """
        Toggle display of Country, City and IP widgets.
        """

        if self.toggle_all == True:

            self.toggle_all = False
            for country in self.gui_manager.country_dictionary:
                self.gui_manager.country_dictionary[country][0].show_all_widgets = False #set toggle for country
                

                for city in self.gui_manager.country_dictionary[country][1]:
                    self.gui_manager.country_dictionary[country][1][city][0].show_ip_widgets = False #set toggle for city
                    for ip in self.gui_manager.country_dictionary[country][1][city][1:]:
                        ip.show = False
        else:
            self.toggle_all = True
            for country in self.gui_manager.country_dictionary:
                self.gui_manager.country_dictionary[country][0].show = True
                self.gui_manager.country_dictionary[country][0].show_city_widgets = True #set toggle for country
                self.gui_manager.country_dictionary[country][0].show_all_widgets = True #set toggle for country

                for city in self.gui_manager.country_dictionary[country][1]:
                    self.gui_manager.country_dictionary[country][1][city][0].show_ip_widgets = True #set toggle for city
                    for ip in self.gui_manager.country_dictionary[country][1][city]:
                        ip.show = True
                        


    def remove_popup(self, button: Button) -> None:
        
        """
        Remove computer widget display popup.  
        """

        self.gui_manager.persistent_widget_container.remove_widget(self.menu_popup)
        self.display_popup = False
 
    

 
    def display_menu(self) -> False:

        """
        Create popup menu when user clicks on the computer widget.
        """

        if self.display_popup == False:

            self.menu_popup = Scatter()
            self.menu_popup.size_hint= (None, None) 
            self.menu_popup.size= (sp(self.scale_array[0]*325), sp(self.scale_array[1]*275))
            self.menu_popup.pos=(self.icon_scatter_widget.pos[0], self.icon_scatter_widget.pos[1] + 50) 
            self.menu_popup.id = "myComputer" 

            

            # with self.menu_popup.canvas.after:
            #     Color(1,1,1,.1)
            #     RoundedRectangle(size=self.menu_popup.size, pos=self.menu_popup.pos, radius=[(20, 20), (20, 20), (20, 20), (20, 20)] )

            

            if self.menu_popup.pos[0] + sp(self.scale_array[0]*300) > self.window_x:
                self.menu_popup.pos = (self.window_x - sp(self.scale_array[0]*350), self.menu_popup.pos[1])

            if self.menu_popup.pos[1] + sp(self.scale_array[1]*250) > self.window_y:
                self.menu_popup.pos = (self.menu_popup.pos[0], self.window_y - sp(self.scale_array[1]*280))

            
            grid_layout = GridLayout(cols=1, size_hint=(None,None), size= (sp(self.scale_array[0]*300), sp(self.scale_array[1]*200)), pos = (sp(self.scale_array[0]*15), sp(self.scale_array[1]*15)))

        
            self.radius_slider = Slider()
            self.radius_slider.value_track = False        
            self.radius_slider.min = 30
            self.radius_slider.max = self.window_x/2
            self.radius_slider.value = self.window_x/4
            self.radius_slider.cursor_height = sp(10)
            self.radius_slider.cursor_size = (sp(12), sp(5))
            self.radius_slider.source = '../assets/images/UI/slider.png'
            self.radius_slider.cursor_image = '../assets/images/UI/slider.png'
            self.radius_slider.padding = "16sp"

          
            toggle_countries = Button()
            toggle_countries.on_press = self.toggle_display_countries
            toggle_countries.text = "Toggle Countries"
            toggle_countries.background_normal = '../assets/images/buttons/green.png'
            toggle_countries.background_down = '../assets/images/buttons/green_down.png'
            toggle_countries.font_size = sp(self.scale_array[1]*15)
            toggle_countries.border = (0,0,0,0)

            toggle_cities = Button()
            toggle_cities.on_press = self.toggle_display_cities
            toggle_cities.text = "Toggle Cities"
            toggle_cities.background_normal = '../assets/images/buttons/teal.png'
            toggle_cities.background_down = '../assets/images/buttons/teal_down.png'
            toggle_cities.font_size = sp(self.scale_array[1]*15)
            toggle_cities.border = (0,0,0,0) 

            toggle_all = Button()
            toggle_all.on_press = self.toggle_all_widgets
            toggle_all.text = "Toggle All IP's"
            toggle_all.background_down = '../assets/images/buttons/darkblue_down.png'
            toggle_all.background_normal = '../assets/images/buttons/darkblue.png'
            toggle_all.font_size = sp(self.scale_array[1]*15)
            toggle_all.border = (0,0,0,0)

            
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
                self.attach_button.text = 'Attach'
                self.attach_button.on_press = self.attach_to_children
                self.attach_button.background_normal = '../assets/images/buttons/lightblue.png'
                self.attach_button.background_down = "../assets/images/buttons/lightblue_down.png"
                self.attach_button.font_size = sp(self.scale_array[1]*15)
                self.attach_button.border = (0,0,0,0)
          

            circular_display_button = Button()
            circular_display_button.on_press = self.circular_display
            circular_display_button.text = "Circular Display"
            circular_display_button.background_normal = '../assets/images/buttons/purple.png'
            circular_display_button.background_down = '../assets/images/buttons/purple_down.png'
            circular_display_button.font_size = sp(self.scale_array[1]*15)
            circular_display_button.border = (0,0,0,0)

        
            dismiss_button = Button()
            dismiss_button.text="Dismiss"
            dismiss_button.background_color=[1,1,1,.1]
            dismiss_button.font_size = sp(self.scale_array[1]*15) 


            dismiss_button.bind(on_press=self.remove_popup)

            if self.state == 'graph':

                graph_label = Label()
                graph_label.text="My Computer"
                graph_label.font_size = sp(self.scale_array[1]*15)

                grid_layout.add_widget(graph_label)
                grid_layout.add_widget(toggle_countries)
                grid_layout.add_widget(toggle_cities)
                grid_layout.add_widget(toggle_all)
                grid_layout.add_widget(self.radius_slider)
                grid_layout.add_widget(circular_display_button)
                grid_layout.add_widget(self.attach_button)
                grid_layout.add_widget(dismiss_button)

            elif self.state == 'mercator':

                self.menu_popup.size= (sp(self.scale_array[0]*325), sp(self.scale_array[1]*150))
                grid_layout = GridLayout(cols=1, size_hint=(None,None), size= (sp(self.scale_array[0]*300), sp(self.scale_array[1]*125)), pos = (sp(self.scale_array[0]*15), sp(self.scale_array[1]*15)))


                mercator_label = Label()
                mercator_label.text="My Computer"
                mercator_label.font_size = sp(self.scale_array[1]*15)

                grid_layout.add_widget(mercator_label)
                grid_layout.add_widget(toggle_countries)
                grid_layout.add_widget(toggle_cities)
                grid_layout.add_widget(dismiss_button)

            self.menu_popup.add_widget(grid_layout)

            self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)
            self.display_popup = True
    


    def set_mercator_layout(self) -> None:

        """
        Called when screenmanager view is changed to mercator view - changes widget sizes and position
        """

        self.label.color = [1,1,1,0]
        self.label.pos = (sp(-30), sp(-20))

        self.icon_scatter_widget.pos = self.mercator_position
        self.icon_scatter_widget.size = (sp(28),sp(self.scale_array[1]*30))

        self.icon_image.size = (sp(self.scale_array[0]*15),sp(self.scale_array[1]*15))
        self.icon_image.pos = (sp(self.scale_array[0]*7), sp(self.scale_array[1]*7))

        self.display_menu_button.size = (sp(self.scale_array[0]*12),sp(self.scale_array[1]*12)) 
        self.display_menu_button.pos = (sp(self.scale_array[0]*7),sp(self.scale_array[1]*7))

        
        

   
    def set_graph_layout(self) -> None:

        """
        Called once when screenmanager view is changed to graph view - changes widget size and city image
        """

        self.label.color = [1,1,1,1]
        self.label.pos = (sp(-15), sp(20))

        self.icon_scatter_widget.pos = self.graph_position
        self.icon_scatter_widget.size = (60,60)

        self.icon_image.size = (40, 40)
        self.icon_image.pos = (10,10)

        self.display_menu_button.size = (30, 30)
        self.display_menu_button.pos = (15, 13)

        


    def update(self, **kwargs) -> None: 

        """
        Update GUI widget. Called every cycle. 
        """

        self.state = kwargs['state'] 
      

        if self.state == 'graph': #start graph loop
            pass

            # if self.graph_layout_finished == False: #call once for graph layout
            #     self.set_graph_layout()
            #     self.graph_layout_finished = True

        

        # End of graph loop

        elif self.state == 'mercator': #start mercator loop
            pass
            # if self.mercator_layout_finished == False:
            #     self.canvas.before.clear()
            #     self.set_mercator_layout()
            #     self.mercator_layout_finished = True

        # End of mercator loop