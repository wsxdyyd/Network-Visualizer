# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.

#Additional Authors:


import sys
import os
import time
import random
import webbrowser
import atexit
import zmq # Networking
import zmq.auth
from typing import Dict, Tuple
from multiprocessing import Array, Process
from network_sniffer import Sniffer

from database_config import db

from kivy.properties import ObservableReferenceList
from kivy.core.window import Window
from kivy.metrics import sp
from kivy.utils import get_color_from_hex
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.colorpicker import ColorWheel
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, Rectangle, RoundedRectangle




class Settings_Panel(AnchorLayout):

    """
    Network Visualizer settings and configuration panel.
    """ 

    def __init__(self, **kwargs) -> None:
        
        """
        Settings_Panel constructor 
        """


        super().__init__()

        self.accordion_panel = Accordion()
        self.accordion_panel.orientation = 'vertical'
        self.size_hint_x = .3
        self.size_hint_y = 1
        self.sniffer_state = True
        self.color_picker_popup_open  = False
        self.summary_data_popup_open = False
        self.gui_manager = None #placeholder until gui_manager is assigned. (BUG: when self is passed in kwargs)
        self.scale_array =  []

        self.error_label = Label()

        self.checkbox_local = CheckBox()
        self.checkbox_local.id = "checkbox_local"
        self.checkbox_local.group = "sniffer"
        self.checkbox_local.bind(active=self.on_sniffer_checkbox_active)

        self.checkbox_remote = CheckBox()
        self.checkbox_remote.id = "checkbox_remote"
        self.checkbox_remote.group = "sniffer"
        self.checkbox_remote.bind(active=self.on_sniffer_checkbox_active)




    def init_accordion(self) -> None:

        """
        Convience function to initalize the Accordion outside of constructor.  
        """

        settings_accordian_panel = AccordionItem(title="Settings")
        about_accordion_panel = AccordionItem(title="About")

        settings_accordian_panel.add_widget(self.create_settings_accordian_panel())
        about_accordion_panel.add_widget(self.create_about_panel())

        self.accordion_panel.add_widget(settings_accordian_panel) 
        self.accordion_panel.add_widget(about_accordion_panel)
        self.add_widget(self.accordion_panel)

        self.init_data_summary_labels()
        self.create_summary_data_popup()
        self.create_protocol_color_popup()



    def init_data_summary_labels(self) -> None:

        """
        Initalize data summary popup labels.
        """

        self.total_ip_label = Label(text = f"IP's: [b][color=ff1919]0[/color][/b]",  markup=True, )

        self.total_countries_label  = Label(text="Countries: [b][color=ff1919]0[/color][/b]", markup=True, )

        self.total_cities_label  = Label(text="Cities: [b][color=ff1919]0[/color][/b]", markup=True, )

        self.total_data_out_label = Label(text="Total data OUT: [b][color=ff1919]0[/color][/b]", markup=True)

        self.total_data_in_label = Label(text="Total data IN: [b][color=ff1919]0[/color][/b]", markup=True)

        auto_connect = self.gui_manager.config_variables_dict["auto_connect"]

        if self.gui_manager.config_variables_dict["auto_connect"] == True and self.gui_manager.config_variables_dict["connect_to"] == "localhost":
            
            connected_ip = "LocalHost"
            connected_port = self.gui_manager.config_variables_dict["local_port"]

            self.connected_to_ip = Label(text=f"Connected to [b][color=#4cbcffff]{connected_ip}[/color][/b] on port [b][color=#4cbcffff]{connected_port}[/color][/b]", markup = True)
            self.auto_connect_label = Label(text = f"Auto-connect on startup: [b][color=4cff32]{str(auto_connect)}[/color][/b]", markup=True)


        elif self.gui_manager.config_variables_dict["auto_connect"] == True and self.gui_manager.config_variables_dict["connect_to"] == "remotehost":
            
            connected_ip = self.gui_manager.config_variables_dict["remote_ip"][0]
            connected_port = self.gui_manager.config_variables_dict["remote_ip"][1]

            self.connected_to_ip = Label(text=f"Connected to [b][color=#4cbcffff]{connected_ip}[/color][/b] on port [b][color=#4cbcffff]{connected_port}[/color][/b]", markup = True)
            self.auto_connect_label = Label(text = f"Auto-connect on startup: [b][color=4cff32]{str(auto_connect)}[/color][/b]", markup=True)


        elif self.gui_manager.connected == False:
            
            connected_ip = None
            connected_port = None

            self.connected_to_ip = Label(text=f"Connected to [b][color=ff1919]{connected_ip}[/color][/b] on port [b][color=ff1919]{connected_port}[/color][/b]", markup = True)
            self.auto_connect_label = Label(text = f"Auto-connect on startup: [b][color=ff1919]{str(auto_connect)}[/color][/b]", markup=True)

        


    def create_settings_accordian_panel(self) -> AnchorLayout :
        
        """
        Construct Settings accordian panel and return layout
        """

        
        reset_button = Button(  text='Reset Sniffer',
                                background_color = [1, 1, 1,.7],
                                on_press = self.reset_session,
                                size_hint_x = .7,
                                size_hint_y = .02
                             )

        change_protocol_color = Button( text='Change Colors',
                                        background_color = [1, 1, 1,.7],
                                        on_press = self.color_picker_toggle,
                                        size_hint_x = .7,
                                        size_hint_y = .02
                                        )

        save_session_button = Button(   text='Save Session Data',
                                        background_color = [1, 1, 1,.7],
                                        on_press = self.save_session_popup,
                                        size_hint_x = .7,
                                        size_hint_y = .02
                                        )

        connect_sniffer_server_button = Button( text='Connect to Sniffer',
                                                background_color = [1, 1, 1,.7],
                                                on_press = self.sniffer_connect_popup,
                                                size_hint_x = .7,
                                                size_hint_y = .02
                                              )

        summary_data_button = Button(   text='Summary Data',
                                        background_color = [1, 1, 1,.7],
                                        on_press = self.summary_data_toggle,
                                        size_hint_x = .7,
                                        size_hint_y = .02
                                    )

        layout_root = AnchorLayout()
        layout_root.anchor_y = 'top'
        layout_root.anchor_x = 'left'
        
        layout_anchor = AnchorLayout()
        layout_anchor.anchor_x = 'right'
        layout_anchor.anchor_y = 'center'

        box_layout_placeholder_spacer = BoxLayout()
        box_layout_placeholder_spacer.size_hint = (1,.15)

        box_layout_buttons = BoxLayout()
        box_layout_buttons.pos_hint = (1,.2)
        box_layout_buttons.size_hint = (.8,.2)
        box_layout_buttons.orientation = 'vertical'


        box_layout_buttons.add_widget(summary_data_button)
        box_layout_buttons.add_widget(change_protocol_color)
        box_layout_buttons.add_widget(reset_button)
        box_layout_buttons.add_widget(save_session_button)
        box_layout_buttons.add_widget(connect_sniffer_server_button)
            
        layout_anchor.add_widget(box_layout_buttons)
        layout_root.add_widget(box_layout_placeholder_spacer)
        layout_root.add_widget(layout_anchor)
        
        return layout_root
        


    def create_about_panel(self) -> RelativeLayout:
        
        """
        Construct About accordian panel
        """
        
        self.web_button = Button(text='Website',size_hint=(.5, .03),  on_press=self.go_to_web)
        self.web_button.pos = ((Window.size[0]/7)/2,Window.size[1]/2-350 )
        self.web_button.pos_hint_y = .5
        self.web_button.pos_hint_x = .5
        
        label = Label()
        label.text = """This tool was built for the people. \n I would like to continue to build this into a \n machine learning intrusion detection system \n with your support. Consider supporting the project with code or funds.  \n Thank you!   \n\nTinkeringEngr """
        label.halign="center"
        label.valign="center"
        label.pos = (0,0)
        label.text_size = (Window.size[1]/2.5, None)


        layout = RelativeLayout()
        layout.add_widget(label)
        layout.add_widget(self.web_button)

        return layout



    def go_to_web(self, go_to_web_button: Button):
        """
        Function to take user to Network Visualizer website
        """

        self.web_button.text = "http://www.tinkeringengr.life/"
        webbrowser.open("http://www.tinkeringengr.life/", new=2, autoraise=True)


    
    def toggle_sniffer_transmission(self, checkbox, value) -> None :
        
        """
        Toggle On/Off Network Sniffer transmission of data
        """ 

        if self.sniffer_state == False:
            try:
                print("Turning on sniffer")
                self.gui_manager.server_socket.send(b'on')
                msg = self.gui_manager.server_socket.recv()
                if msg == 'received on': #check to make sure server (sniffer) got msg
                    self.sniffer_state = True
                    checkbox.active = True
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

        elif self.sniffer_state == True:
            try:
                print("Turning off sniffer")
                self.gui_manager.server_socket.send('off')
                msg = self.gui_manager.server_socket.recv()
                if msg == 'received off': #check to make sure server (sniffer) got msg
                    self.sniffer_state = False
                    checkbox.active = False
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)          
            


    def reset_session(self, reset_session_button: Button) -> None:

        """ 
        Reset the Network Sniffer -- Delete database entry and assosciated data structures 
        Send reset signal to network sniffer server to reset on both ends
        """

        
        try:
            self.gui_manager.server_socket.send(b'reset')
            msg = self.gui_manager.server_socket.recv()
            print(msg)

            if msg == b'received reset':
                self.gui_manager.sniffer_time = time.time()
                self.gui_manager.country_dictionary.clear()
                self.gui_manager.ip_dictionary.clear()
                self.gui_manager.sniffer_dictionary.clear()          
                self.gui_manager.widget_container.clear_widgets()
                self.gui_manager.ip_total_count = 1
                self.gui_manager.city_total_count = 1
                self.gui_manager.country_total_count = 1

                cursor = db.cursor()
                cursor.execute("DROP TABLE IF EXISTS live")
                db.commit()

        except zmq.ZMQError as e:
            pass

     
                

    
    def save_session_popup(self, save_session_popup_button: Button) -> None:

        """
        Popup message displayed when save session data button clicked. 
        """
   

        save_session_content = BoxLayout(orientation='vertical')

        save_session_content_nested = BoxLayout(orientation='vertical')

        self.session_popup_description = Label(text='Enter a name and save the session data. \n (alphanumeric characters only)', halign="center", valign="center")
        save_session_content.add_widget(self.session_popup_description)

        self.save_session_textinput = TextInput(on_text_validate=self.save_session_into_database, multiline=False )

        save_session_content_nested.add_widget(self.save_session_textinput)
        save_session_content.add_widget(save_session_content_nested)
        save_session_content_nested.add_widget(Button(text="Save", on_press = self.save_session_into_database))


        self.save_session_popup_object = Popup(
                                                title='Save Session Data',
                                                content=save_session_content,
                                                size_hint=(.35,.3),
                                                auto_dismiss=False
                                              )

        save_session_content_nested.add_widget(Button(text="Close", on_press = self.save_session_popup_object.dismiss))

        self.save_session_popup_object.open()

    


    def save_session_into_database(self, save_session_button: Button):
        
        """
        Validate and insert session data (sniffer dictionary) into sqlite database
        """

        session_to_save = self.save_session_textinput.text

        if session_to_save.isalnum(): #check alphanumeric condition
            if session_to_save[0].isnumeric(): #Can't start with a number condition
                self.session_popup_description.color = (1,0,0,1)
                self.session_popup_description.text = "Can't start with a number...sigh -- blame sqlite."
                
            else:

                json_session_data = self.gui_manager.sniffer_dictionary #JSON serialization faciliated by sqlite registration on insertion (see database_config.py for dictionary type)

                try:
                    cursor = db.cursor()
                    cursor.execute("""INSERT OR IGNORE INTO sessions (session_name, session_data) VALUES ("{session}", "{json_session_data}")""".format(session = session_to_save, json_session_data = json_session_data))
                    db.commit()
                except:
                    self.session_popup_description.color = (1,0,0,1)
                    self.session_popup_description.text = "Error saving data!"
                    return

                self.save_session_popup_object.dismiss()

        else:
            self.session_popup_description.color = (1,0,0,1)
     

    
    
    def generate_keys(self, key_dir: str) -> Dict[str, Tuple[str, str]]:
        """
        Generate new cryptographic keys
        """
        pass     
   


    def connect_to_remote_server(self, connect_to_remote_server_button: Button) -> None:

        """
        Connect to sniffer at remote location. (phone, webserver, etc)
        """
        

        if self.server_port_textinput.text == '':
                self.error_label.text = "No port selected -- specify an unused interger between 1024-49151"
                self.error_label.color = (1,0,0,1)
                print("error1")
                return

        try:
            req_port = int(self.server_port_textinput.text)
            sub_port = req_port + 1
            self.gui_manager.config_variables_dict["remote_ip"][1] = req_port
        except:
            self.error_label.text = "Error converting port to an interger. Input an unused interger between 1024-49151"
            self.error_label.color = (1,0,0,1)
            print("error2")
            return

            
        ###if 0.0.0.0 use stored config
        if self.server_ip_textinput.text == '0.0.0.0':
                self.error_label.text = "No IP selected -- specify the IP address of the remote computer"
                self.error_label.color = (1,0,0,1)
                print("error1")
                return

        remote_ip = self.server_ip_textinput.text
        self.gui_manager.config_variables_dict["remote_ip"][0] = remote_ip
        

        try:
            connect_string_req = f"tcp://{remote_ip}:{req_port}"
            connect_string_sub = f"tcp://{remote_ip}:{sub_port}"


            keys = zmq.auth.load_certificate('../configuration/keys/client.key_secret')
            server_key, _ = zmq.auth.load_certificate('../configuration/keys/server.key')
    
            context = zmq.Context()
            self.gui_manager.server_socket = context.socket(zmq.REQ) #client/server pattern for guaranteed messages
            self.gui_manager.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.gui_manager.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.gui_manager.server_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.gui_manager.server_socket.connect(connect_string_req)

            self.gui_manager.data_socket = context.socket(zmq.SUB) #PUB/SUB pattern for sniffer data
            self.gui_manager.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
            self.gui_manager.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
            self.gui_manager.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
            self.gui_manager.data_socket.connect(connect_string_sub)
    
            self.gui_manager.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")

        except Exception as e:
    
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

        print(self.gui_manager.server_socket)


        



       

    def connect_to_local_server(self, connect_to_local_server_button: Button) -> None:

        """
        Start and connect to sniffer on Localhost
        """

        if self.server_port_textinput.text == '':
            self.error_label.text = "No port selected -- specify an unused interger between 1024-49151"
            self.error_label.color = (1,0,0,1)

            print("error1")
            return

        try:
            req_port = int(self.server_port_textinput.text)
            sub_port = req_port + 1
            self.gui_manager.config_variables_dict["local_port"] = req_port
        except:
            self.error_label.text = "Error converting port to an interger. Input an unused interger between 1024-49151"
            self.error_label.color = (1,0,0,1)
            print("error2")
            return



        if self.gui_manager.sniffer_process == None:

            try:
                keywords = {'port': req_port}
                self.gui_manager.sniffer_process = Process(name= 'sniffer', target=Sniffer, kwargs=keywords)
                self.gui_manager.sniffer_process.start()
                atexit.register(self.gui_manager.sniffer_process.close) #kill sniffer

            except:
                #TODO: clean up error
                print("error3")
                return


            try:
                connect_string_req = f"tcp://localhost:{req_port}"
                connect_string_sub = f"tcp://localhost:{sub_port}"


                keys = zmq.auth.load_certificate('../configuration/keys/client.key_secret')
                server_key, _ = zmq.auth.load_certificate('../configuration/keys/server.key')
        
                context = zmq.Context()
                self.gui_manager.server_socket = context.socket(zmq.REQ) #client/server pattern for guaranteed messages
                self.gui_manager.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
                self.gui_manager.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
                self.gui_manager.server_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
                self.gui_manager.server_socket.connect(connect_string_req)

                self.gui_manager.data_socket = context.socket(zmq.SUB) #PUB/SUB pattern for sniffer data
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
                self.gui_manager.data_socket.connect(connect_string_sub)
        
                self.gui_manager.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")

            except Exception as e:
        
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)


               


          

    def on_sniffer_checkbox_active(self, checkbox, value) -> None:
        pass

    def more_info(self, moreinfo_button: Button) -> None :
        pass


    def close_sniifer_connect(self, sniffer_close_button: Button) -> None:

        """
        
        """

        self.checkbox_remote.parent = None
        self.checkbox_local.parent = None
        self.sniffer_connect_popup_object.dismiss()




    def sniffer_connect_popup(self, sniffer_connect_button: Button):
        
        """
        Popup menu for configuring and connecting to Sniffer
        """

        content_base = BoxLayout(orientation='vertical')

        self.sniffer_connect_popup_object = Popup(title='Connect to Sniffer', content=content_base, size_hint=(.5,.5), auto_dismiss=False)
        close_button = Button(text="Close", on_press = self.close_sniifer_connect)
        close_button.size_hint_y = .1

        base1 = BoxLayout(orientation='vertical')
        base1.size_hint = (1,1)




        generate_keys_button = Button(text="Generate New Cryptographic Key-Pair", on_press=self.generate_keys)
        generate_keys_button.size_hint = (1,1)

        moreinfo_button = Button(text="More Info", on_press=self.more_info)
        moreinfo_button.size_hint = (1,1)

        cryptographic_folder_label = Label(text = "Location of cryptographic keys: ../assets/keys", halign='left', valign='center')
        #cryptographic_folder_label.text_size = (600,200)

        section1_row1 = BoxLayout(orientation='horizontal')
        section1_row2 = BoxLayout(orientation='horizontal')
        section1_row3 = BoxLayout(orientation='horizontal')


        # import os
        # cwd = os.getcwd()
        # print(cwd)

        #directory_label = Label(text = '../assets/keys')
        placeholder_label2 = Label(text = "")
        placeholder_label3 = Label(text = "")

        section1_row1.add_widget(cryptographic_folder_label)
        section1_row1.add_widget(Label())

        #section1_5.add_widget(directory_label)

        section1_row2.add_widget(generate_keys_button)
        section1_row2.add_widget(placeholder_label2)

        section1_row3.add_widget(moreinfo_button)
        section1_row3.add_widget(placeholder_label3)


        base2_1 = BoxLayout(orientation='vertical')
        base3_2 = BoxLayout(orientation='horizontal')
        base3_3 = BoxLayout(orientation='horizontal')


        base2_1.add_widget(section1_row1)
        #base2_1.add_widget(directory_label)
        base2_1.add_widget(section1_row3)
        base2_1.add_widget(section1_row2)
        base2_1.size_hint = (1,1)
        

        server_ip_label = Label(text="Server IP Address --> " )
        self.server_ip_textinput = TextInput(text="0.0.0.0")
        #server_ip_label.text += server_ip_textinput.text 

        server_port_label = Label(text="Port -->" )
        self.server_port_textinput = TextInput()
        server_port_label.text += self.server_port_textinput.text 
        

        # = Label(text = "Location of cryptographic keys: ", )

        remote_connect_button = Button(text="Connect to Remote Sniffer", on_press=self.connect_to_remote_server)
        local_connect_button = Button(text="Connect to Local Sniffer", on_press=self.connect_to_local_server)

        placeholder_middle = BoxLayout(orientation='horizontal')
        placeholder_middle.size_hint = (1, .7)
        placeholder_middle.add_widget(Label())
        placeholder_middle.add_widget(Label())
        
        base3_4 = BoxLayout(orientation='horizontal')
        base3_4.add_widget(server_ip_label)
        base3_4.add_widget(self.server_ip_textinput)

        base3_5 = BoxLayout(orientation='horizontal')
        base3_5.add_widget(server_port_label)
        base3_5.add_widget(self.server_port_textinput)
   
        base2 = BoxLayout(orientation='vertical')
        base2.add_widget(base3_4)
        base2.add_widget(base3_5)
        base2.add_widget(placeholder_middle)
        
        base3_1 = BoxLayout(orientation='horizontal')
        base3_1.add_widget(Label(text=''))
        base3_1.add_widget(Label(text='Automatically Connect on Startup'))

        base3_2.add_widget(remote_connect_button)

        base3_2.add_widget(self.checkbox_remote)
        base3_3.add_widget(local_connect_button)
        base3_3.add_widget(self.checkbox_local)

        placeholder = BoxLayout(orientation='vertical')
        placeholder.size_hint = (1, .3)

        placeholder2 = BoxLayout(orientation='vertical')
        placeholder2.size_hint = (1, .2)

        base2.add_widget(base3_1)

        base2.add_widget(base3_2)
        base2.add_widget(base3_3)
        
        base1.add_widget(base2_1)
        base1.add_widget(placeholder)
        base1.add_widget(base2)
        base1.add_widget(placeholder2)


        content_base.add_widget(base1)
        #sniffer_connect_content.add_widget(placeholder2)
        content_base.add_widget(close_button)
        self.sniffer_connect_popup_object.open()



    def color_picker_toggle(self, *args):

        if self.color_picker_popup_open == False:
            self.color_picker_popup_open = True
            self.gui_manager.persistent_widget_container.add_widget(self.color_picker_layout)

        elif self.color_picker_popup_open == True:
            self.color_picker_popup_open = False
            self.gui_manager.persistent_widget_container.remove_widget(self.color_picker_layout)




    def close_color_picker(self, *args):
        self.color_picker_popup_open = False
        self.gui_manager.persistent_widget_container.remove_widget(self.color_picker_layout)
      




    def apply_color(self, apply_color_button: Button):

        try:
            color_value = get_color_from_hex(self.hex_input.text) #e.g. FFFFFFFF to [1,1,1,1] (RGBA)
        except:
            return #unable to get hex value so don't proceed

        #TODO: upgrade to python3.10 and use Match syntax?
        #many packages are not avaiable or dont compile for python3.10 including Kivy at the moment

        if self.selected_protocol_button.text == "TCP":
            for ip in self.gui_manager.ip_dictionary:
                self.gui_manager.ip_dictionary[ip].tcp_color = color_value
            self.gui_manager.config_variables_dict['tcp_color'] = color_value

        elif self.selected_protocol_button.text == "UDP":
            for ip in self.gui_manager.ip_dictionary:
                self.gui_manager.ip_dictionary[ip].udp_color = color_value
                self.gui_manager.config_variables_dict['udp_color'] = color_value
                
        elif self.selected_protocol_button.text == "City":
            for country in self.gui_manager.country_dictionary:
                for city in self.gui_manager.country_dictionary[country][1]:
                    city_widget = self.gui_manager.country_dictionary[country][1][city][0]
                    city_widget.city_color = color_value
                    self.gui_manager.config_variables_dict['city_color'] = color_value

        elif self.selected_protocol_button.text == "Country":
            for country in self.gui_manager.country_dictionary:
                country_widget = self.gui_manager.country_dictionary[country][0]  
                country_widget.country_color = color_value
                self.gui_manager.config_variables_dict['country_color'] = color_value

        elif self.selected_protocol_button.text == "Other":
            for ip in self.gui_manager.ip_dictionary:
                self.gui_manager.ip_dictionary[ip].other_color = color_value
            self.gui_manager.config_variables_dict['other_color'] = color_value

        elif self.selected_protocol_button.text == 'Data IN':
            self.gui_manager.config_variables_dict['Data IN'] = color_value

        elif self.selected_protocol_button.text == 'Data OUT':
            self.gui_manager.config_variables_dict['Data OUT'] = color_value

        elif self.selected_protocol_button.text == 'Geographic Data':
            self.gui_manager.config_variables_dict['Geographic Data'] = color_value







    def open_drop_down_menu_hack(self, call_button) -> None:

        """
        
        """

        self.features_dropdown.open(call_button)


    


    def summary_data_toggle(self, *args):

        """
        Toggle display summary data on/off
        """

        if self.summary_data_popup_open == False:
            self.summary_data_popup_open = True
            self.gui_manager.persistent_widget_container.add_widget(self.summary_data_layout)

        elif self.summary_data_popup_open == True:
            self.summary_data_popup_open = False
            self.gui_manager.persistent_widget_container.remove_widget(self.summary_data_layout)

        


    
    def create_summary_data_popup(self) -> None:

        """
        Convience function for creating summary data popup
        """
        

            
        position = self.gui_manager.config_variables_dict['summary_data_pos']


        self.summary_data_layout = FloatLayout()
        self.summary_data_layout.pos= position
        self.summary_data_layout.size_hint=(None,None)

        summary_data_scatter = Scatter()
        summary_data_scatter.size_hint = (None,None)
        summary_data_scatter.pos = position
        summary_data_scatter.size = (sp(300),sp(125))

        with summary_data_scatter.canvas:
            Color(1,1,1,.1)
            RoundedRectangle(size=(sp(300),sp(125)), pos=(0,0), radius=[(20, 20), (20, 20), (20, 20), (20, 20)] )


        all_content_container  = BoxLayout(orientation="vertical")
        all_content_container.size = (sp(300), sp(125))

        close_button = Button(text="Close", on_press = self.summary_data_toggle)

        left_box_content_container  = BoxLayout(orientation="vertical")
        right_box_content_container  = BoxLayout(orientation="vertical")
        horizontal_box_content_container  = BoxLayout(orientation="horizontal")
        lower_box_content_container  = BoxLayout(orientation="vertical")

        left_box_content_container.add_widget(Label(size_hint=(1,.1)))
        left_box_content_container.add_widget(self.total_ip_label)
        left_box_content_container.add_widget(self.total_cities_label)
        left_box_content_container.add_widget(self.total_countries_label)

        right_box_content_container.add_widget(Label(size_hint=(1,.2)))
        right_box_content_container.add_widget(self.total_data_in_label)
        right_box_content_container.add_widget(self.total_data_out_label)
        right_box_content_container.add_widget(Label(size_hint=(1,.2)))
        
        horizontal_box_content_container.add_widget(Label(size_hint = (.15,1)))
        horizontal_box_content_container.add_widget(left_box_content_container)
        horizontal_box_content_container.add_widget(Label())
        horizontal_box_content_container.add_widget(right_box_content_container)
        horizontal_box_content_container.add_widget(Label())
        
        lower_box_content_container.add_widget(Label())
        lower_box_content_container.add_widget(self.auto_connect_label)
        lower_box_content_container.add_widget(Label(size_hint = (1,.5)))
        lower_box_content_container.add_widget(self.connected_to_ip)
        lower_box_content_container.add_widget(Label())
        lower_box_content_container.add_widget(close_button)

        all_content_container.add_widget(horizontal_box_content_container)
        all_content_container.add_widget(lower_box_content_container)
        
        

        summary_data_scatter.add_widget(all_content_container)
        self.summary_data_layout.add_widget(summary_data_scatter)


         


    def create_protocol_color_popup(self, *change_protocol_color_button: Button):
            
            """
            Function to change UI widget (protocol) Line color according to user selection
            """


  

            clr_picker_pos = (0, random.uniform(.2,.8) * Window.size[1])

            
            self.color_picker_layout = FloatLayout()
            self.color_picker_layout.pos= clr_picker_pos
            self.color_picker_layout.size_hint=(None,None)

            self.icon_scatter_widget = Scatter()
            self.icon_scatter_widget.size_hint = (None,None)
            self.icon_scatter_widget.pos = (0,0)
            #self.icon_scatter_widget.pos = clr_picker_pos
            self.icon_scatter_widget.size = (sp(375),sp(150))

            with self.icon_scatter_widget.canvas:
                Color(1,1,1,.1)
                RoundedRectangle(size=(sp(375),sp(150)), pos=self.icon_scatter_widget.pos, radius=[(20, 20), (20, 20), (20, 20), (20, 20)] )
                #RoundedRectangle(size=(sp(375),sp(150)), pos=clr_picker_pos, radius=[(20, 20), (20, 20), (20, 20), (20, 20)] )


        
            all_content_container  = BoxLayout(orientation="vertical")
            all_content_container.size = (sp(375), sp(150))

            sub_content_container  = BoxLayout(orientation="horizontal")
            right_stack_container  = BoxLayout(orientation="vertical")
            button_container = BoxLayout(orientation='horizontal', spacing=10)
            hex_input_container = BoxLayout(orientation='horizontal')

            self.features_dropdown = DropDown()
            supported_features = ['City', 'Country','Data IN', 'Data OUT', 'Geographic Data', 'TCP', 'UDP', 'Other'] #extend to support more protocols

            for protocol in supported_features:
                btn = Button(text=protocol, size_hint=(None, None), width=sp(125), height=44)
                btn.bind(on_release=lambda btn: self.features_dropdown.select(btn.text))  #We use the "selected" protocol button text when widget.update() Canvas Line color
                self.features_dropdown.add_widget(btn)


            self.selected_protocol_button = Button(text='Select Feature', size_hint=(None, None), width=sp(125), height=sp(25))
            #self.selected_protocol_button.bind(on_press=self.protocol_dropdown.open)
            self.selected_protocol_button.bind(on_press=self.open_drop_down_menu_hack)

            self.features_dropdown.bind(on_select=lambda instance, x: setattr(self.selected_protocol_button, 'text', x))


            self.hex_input = TextInput()
            self.hex_input.size_hint_y = None
            self.hex_input.size_hint_x = None
            self.hex_input.size = (sp(95),sp(23))

            self.clr_picker  = ColorWheel()
            self.clr_picker.size_hint = (.5, 1)
            self.clr_picker._origin = (self.icon_scatter_widget.pos[0] + 120, self.icon_scatter_widget.pos[1] + 170)
            self.clr_picker.bind(color =  self.on_color_selection )
            self.hex_input.text = str(self.clr_picker.hex_color)

            self.color_label = Label(text = "Selected Color: {} ".format(str(self.clr_picker.hex_color)))
            apply_color_button = Button(text="Apply Color", on_press = self.apply_color, size_hint=(None, None), width=sp(100), height=sp(25))
            close_button = Button(text="Close", on_press = self.close_color_picker, size_hint_y=0.15)

            button_spacer = Label()
           
            hex_spacer = Label()
            hex_spacer.size_hint_x = 1
            hex_spacer2 = Label()
            hex_spacer2.size_hint_x = 3.3
            hex_spacer3 = Label()
            hex_spacer3.size_hint_x = 3



            button_container.add_widget(self.selected_protocol_button)
            button_container.add_widget(apply_color_button)

            hex_input_container.add_widget(hex_spacer2)
            hex_input_container.add_widget(hex_spacer3)
            hex_input_container.add_widget(self.hex_input)
            hex_input_container.add_widget(hex_spacer)

            right_stack_container.add_widget(self.color_label)
            right_stack_container.add_widget(hex_input_container)
            right_stack_container.add_widget(button_container)
            right_stack_container.add_widget(button_spacer)
            

            sub_content_container.add_widget(self.clr_picker)
            sub_content_container.add_widget(right_stack_container)

            all_content_container.add_widget(sub_content_container)
            all_content_container.add_widget(close_button)

            self.icon_scatter_widget.add_widget(all_content_container)
            self.color_picker_layout.add_widget(self.icon_scatter_widget)


    def on_color_selection(self, colorwheel: ColorWheel, value: ObservableReferenceList) -> None:
        
        """
        Called on ColorWheel selection. 
        """

        self.color_label.text = "Selected Color: {} ".format(str(self.clr_picker.hex_color))
        self.color_label.color = self.clr_picker.color
        self.hex_input.text = str(self.clr_picker.hex_color)