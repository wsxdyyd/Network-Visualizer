# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.

# Additional Authors:

from cProfile import label
from cgitb import reset
from distutils.archive_util import make_archive
import sys
import os
import time
import random
import webbrowser
import atexit
import zmq  # Networking
import zmq.auth
from typing import Dict, Tuple
from multiprocessing import Array, Process
from network_sniffer import Sniffer
import netifaces as ni
import socket


from pyperclip import copy


from utilities.database_config import db

from kivy.properties import ObservableReferenceList
from kivy.core.window import Window
from kivy.metrics import sp, dp
from kivy.utils import get_color_from_hex
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.gridlayout import GridLayout

from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.dropdown import DropDown
from kivy.graphics import Color, Rectangle, RoundedRectangle

from utilities.colorwheel import ColorWheel

from utilities.iconfonts import register, icon


class Settings_Panel(AnchorLayout):

    """
    Network Visualizer settings and configuration panel.
    """

    def __init__(self, **kwargs) -> None:

        """
        Settings_Panel constructor
        """

        super().__init__()

        self.resource_path = kwargs["resource_path"]
        self.accordion = Accordion(min_space=dp(35))

        register(
            "default_font",
            os.path.join(self.resource_path, "assets/fonts/fontawesome-webfont"),
            os.path.join(self.resource_path, "assets/fonts/font-awesome.fontd"),
        )

        self.accordion.orientation = "vertical"

        size = (dp(390), dp(450))
        self.accordion.size = size
        self.size_hint_x = 1
        self.size_hint_y = 1
        self.sniffer_state = True

        self.settings_panel_scatter = Scatter()
        self.settings_panel_scatter.size_hint = (None, None)
        self.settings_panel_scatter.size = size

        self.settings_panel_scatter.add_widget(self.accordion)

        self.color_picker_popup_open = False
        self.sniffer_connect_popup = False

        self.gui_manager = None  # placeholder until gui_manager is assigned. (BUG: when self is passed in kwargs)

        self.error_label = Label()

        self.auto_connect_checkbox = CheckBox()
        self.auto_connect_checkbox.id = "auto_connect"
        self.auto_connect_checkbox.group = "auto_connect"
        self.auto_connect_checkbox.bind(active=self.on_sniffer_checkbox_active)
        self.auto_connect_checkbox.background_radio_normal = os.path.join(
            self.resource_path, "assets/images/UI/white_circle.png"
        )
        self.auto_connect_checkbox.size_hint_x = 0.15

        # TODO: the construction of settings panel is wack, need to do it better
        # init_accordion()
        # init summary data

    def create_colors_panel(self):

        grid_layout = GridLayout(cols=1, size=(sp(325), sp(125)))

        bottom_stack_container = BoxLayout(orientation="vertical")
        button_container = BoxLayout(orientation="horizontal", spacing=10)
        label_container = BoxLayout(orientation="horizontal", spacing=5)

        self.features_dropdown = DropDown()
        # TODO:which features do we actually support?
        supported_features = [
            "TCP Protocol",
            "UDP Protocol",
            "OTHER Protocol",
            "Data IN",
            "Data OUT",
            "Summary Data",
        ]  # extend to support more features

        self.colored_buttons = {}
        for feature in supported_features:

            btn = Button(
                text=feature,
                size_hint=(None, None),
                width=sp(125),
                height=44,
                background_color=(0, 0, 0, 1),
            )
            btn.id = feature
            btn.bind(on_release=self.features_dropdown_color_text_change)
            btn.color = self.gui_manager.config_variables_dict[f"{feature} Color"]
            self.features_dropdown.add_widget(btn)
            self.colored_buttons[feature] = btn

        self.selected_protocol_button = Button(
            text="Select Feature",
            size_hint=(None, None),
            width=sp(125),
            height=sp(25),
            background_color=(0.1, 0.1, 0.1, 0.8),
        )

        self.selected_protocol_button.bind(on_press=self.open_features_dropdown)

        self.features_dropdown.bind(
            on_select=lambda instance, x: setattr(
                self.selected_protocol_button, "text", x
            )
        )

        self.hex_input = TextInput()
        self.hex_input.bind(text=self.validate_color_textinput)
        self.hex_input.size_hint_y = None
        self.hex_input.size_hint_x = None
        self.hex_input.size = (sp(80), sp(23))

        self.clr_picker = ColorWheel()
        self.clr_picker.size_hint = (0.5, 1)
        self.clr_picker.bind(color=self.on_color_selection)
        self.hex_input.text = str(self.clr_picker.hex_color)

        # self.color_label = Label(text = f"Selected Color: ")
        self.apply_color_button = Button(
            text="Apply Color",
            on_press=self.apply_color,
            size_hint=(None, None),
            width=sp(100),
            height=sp(25),
            background_color=(0, 0, 0, 1),
        )

        label_container.add_widget(Label(size_hint_x=1))
        label_container.add_widget(self.hex_input)
        label_container.add_widget(Label(size_hint_x=1))

        button_container.add_widget(Label(size_hint_x=1))
        button_container.add_widget(self.selected_protocol_button)
        button_container.add_widget(self.apply_color_button)
        button_container.add_widget(Label(size_hint_x=1))

        bottom_stack_container.add_widget(Label(size_hint_y=0.5))
        bottom_stack_container.add_widget(label_container)
        bottom_stack_container.add_widget(Label(size_hint_y=0.5))
        bottom_stack_container.add_widget(button_container)
        bottom_stack_container.add_widget(Label(size_hint_y=1))

        grid_layout.add_widget(Label(size_hint_y=0.1))
        grid_layout.add_widget(self.clr_picker)
        grid_layout.add_widget(bottom_stack_container)

        return grid_layout

    def collapse_settings_panel(self, accordion_panel: AccordionItem, value: bool):
        if value == False:
            self.gui_manager.settings_panel_toggle()
            self.about_accordion_panel.collapse = False

    def init_accordion(self) -> None:

        """
        Convience function to initalize the Accordion outside of constructor.
        """

        self.about_accordion_panel = AccordionItem(title="About")
        self.about_accordion_panel.id = "about"

        change_colors_panel = AccordionItem(title="Colors")
        change_colors_panel.id = "colors"

        sniffer_settings_panel = AccordionItem(title="Connection Settings")
        sniffer_settings_panel.id = "sniffer"

        save_session_panel = AccordionItem(title="Save Session")
        save_session_panel.id = "save"

        dismiss_panel = AccordionItem(title="Dismiss")
        dismiss_panel.id = "dismiss"
        dismiss_panel.bind(collapse=self.collapse_settings_panel)
        dismiss_panel.background_normal = os.path.join(
            self.gui_manager.resource_path, "assets/images/buttons/black.png"
        )

        self.about_accordion_panel.add_widget(self.create_about_panel())
        change_colors_panel.add_widget(self.create_colors_panel())
        sniffer_settings_panel.add_widget(self.create_sniffer_settings_panel())
        save_session_panel.add_widget(self.create_save_session_panel())

        self.accordion.add_widget(self.about_accordion_panel)
        self.accordion.add_widget(change_colors_panel)
        self.accordion.add_widget(save_session_panel)
        self.accordion.add_widget(sniffer_settings_panel)

        self.accordion.add_widget(dismiss_panel)

        if self.gui_manager.first_time_starting == True:
            self.settings_panel_scatter.pos = (0, 100)
        else:
            self.settings_panel_scatter.pos = self.gui_manager.config_variables_dict[
                "settings_panel_pos"
            ]

        with self.settings_panel_scatter.canvas.before:
            Color(0.1, 0.1, 0.1, 0.8)
            RoundedRectangle(
                size=self.settings_panel_scatter.size,
                pos=(0, 0),
                radius=[(20, 20), (20, 20), (20, 20), (20, 20)],
            )

        # settings_accordian_panel.collapse = False
        self.about_accordion_panel.collapse = False

        # self.gui_manager.graph_view.add_widget(self.settings_popup)
        # self.add_widget(self.accordion_panel)

        self.init_data_summary_labels()
        # self.create_protocol_color_popup()

    def init_data_summary_labels(self) -> None:

        """
        Initalize data summary popup labels.
        """

        self.total_ip_label = Label(
            text=f"IP's: [b][color=ff1919]0[/color][/b]",
            markup=True,
        )

        self.total_countries_label = Label(
            text="Countries: [b][color=ff1919]0[/color][/b]",
            markup=True,
        )

        self.total_cities_label = Label(
            text="Cities: [b][color=ff1919]0[/color][/b]",
            markup=True,
        )

        self.total_data_out_label = Label(
            text="Total data OUT: [b][color=ff1919]0[/color][/b]", markup=True
        )

        self.total_data_in_label = Label(
            text="Total data IN: [b][color=ff1919]0[/color][/b]", markup=True
        )

        cursor = db.cursor()
        cursor.execute("SELECT * from malicious_ips")
        malicious_ips = cursor.fetchall()
        self.malicious_ip_count = Label(
            text=f"[color=FF0000] Malicious IP's: [b]{str(len(malicious_ips))}[/b]",
            markup=True,
        )

        self.connection_label = Label(text="", pos=(250, -27), markup=True)

        self.connection_label_scatter = Scatter()
        self.connection_label_scatter.size = (dp(300), dp(25))

        if self.gui_manager.first_time_starting == True:
            self.connection_label_scatter.pos = (
                self.gui_manager.window_x - dp(320),
                dp(20),
            )
        else:
            self.connection_label_scatter.pos = self.gui_manager.config_variables_dict[
                "connection_label_pos"
            ]

        self.connection_label_scatter.add_widget(self.connection_label)

        self.connection_label_layout = FloatLayout()
        self.connection_label_layout.size_hint = (None, None)
        self.connection_label_layout.size = (dp(300), dp(25))

        self.connection_label_layout.add_widget(self.connection_label_scatter)

        with self.connection_label_scatter.canvas:
            Color(1, 1, 1, 0.1)
            RoundedRectangle(
                size=self.connection_label_scatter.size,
                pos=(0, 0),
                radius=[(20, 20), (20, 20), (20, 20), (20, 20)],
            )

        if self.gui_manager.connected_to_sniffer == True:

            connected_ip = self.gui_manager.config_variables_dict[
                "last_connected_sniffer"
            ][0]
            connected_port = self.gui_manager.config_variables_dict[
                "last_connected_sniffer"
            ][1]
            print(
                "in settings_panel = if self.gui_manager.connected_to_sniffer == True"
            )
            self.connection_label.text = f"[color=#00ff00][b]Connected[/b][/color] to [color=#00ff00][b]{connected_ip}[/color][/b] on port [color=#00ff00][b]{connected_port}[/color][/b]"

        else:  # self.gui_manager.connected_to_sniffer == False

            print("in settings_panel #self.gui_manager.connected_to_sniffer == False")
            self.connection_label.text = "[color=FF0000][b]Not Connected[/color][/b]"

        # BUG:LOL! created here because the dependency chain needs to be re-done
        # self.make_sniffer_connect_popup()

    def create_settings_accordian_panel(self) -> AnchorLayout:

        """
        Construct Settings accordian panel and return layout
        """

        dismiss_settings_panel = Button(
            text="Dismiss",
            background_color=[0, 0, 0, 0.5],
            on_press=self.gui_manager.settings_panel_toggle,
            size_hint_x=0.2,
            # size_hint_y = .02
        )

        box_layout_buttons = BoxLayout()
        box_layout_buttons.size_hint = (1, 1)
        box_layout_buttons.orientation = "vertical"

        box_layout_buttons.add_widget(Label())

        box_layout_buttons.add_widget(Label())

        box_layout_buttons.add_widget(Label())

        container_6 = BoxLayout(orientation="horizontal")
        container_6.add_widget(Label(size_hint_x=0.3))
        container_6.add_widget(dismiss_settings_panel)
        container_6.add_widget(Label(size_hint_x=0.3))
        box_layout_buttons.add_widget(container_6)

        box_layout_buttons.add_widget(Label())

        return box_layout_buttons

    def create_about_panel(self) -> RelativeLayout:

        """
        Construct About accordian panel
        """

        self.web_button = Button(
            text="Website",
            size_hint=(1, 0.08),
            on_press=self.go_to_web,
            background_color=[0, 0, 0, 0.5],
        )

        label = Label()
        label.text = """This tool is built for the people. \n I would like to continue to build this into a \n machine learning intrusion detection system \n with your support. Consider supporting this open-source project with donations, code, feedback, or showing others.  \n Thank you!!   \n\nTinkeringEngr \n TinkeringEngr@protonmail.com"""
        label.halign = "center"
        label.valign = "center"

        label.text_size = (dp(320), None)

        layout = RelativeLayout()
        # layout = BoxLayout(orientation='vertical')
        layout.add_widget(label)
        webbutton_container = BoxLayout(orientation="horizontal")

        webbutton_container.add_widget(Label(size_hint_x=0.5))
        webbutton_container.add_widget(self.web_button)
        webbutton_container.add_widget(Label(size_hint_x=0.5))
        webbutton_container.pos = (dp(0), dp(15))
        layout.add_widget(webbutton_container)

        return layout

    def go_to_web(self, go_to_web_button: Button):
        """
        Function to take user to Network Visualizer website
        """

        self.web_button.text = "http://www.tinkeringengr.life/"
        webbrowser.open("http://www.tinkeringengr.life/", new=2, autoraise=True)

    def toggle_sniffer_transmission(self, checkbox, value) -> None:

        """
        Toggle On/Off Network Sniffer transmission of data
        """

        if self.sniffer_state == False:
            try:
                print("Turning on sniffer")
                self.gui_manager.server_socket.send(b"on")
                msg = self.gui_manager.server_socket.recv()
                if msg == "received on":  # check to make sure server (sniffer) got msg
                    self.sniffer_state = True
                    checkbox.active = True
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

        elif self.sniffer_state == True:
            try:
                print("Turning off sniffer")
                self.gui_manager.server_socket.send("off")
                msg = self.gui_manager.server_socket.recv()
                if msg == "received off":  # check to make sure server (sniffer) got msg
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
            self.gui_manager.server_socket.send(b"reset")
            msg = self.gui_manager.server_socket.recv()

            if msg == b"received reset":
                self.gui_manager.kivy_application.switch_sniffer(
                    self.gui_manager.config_variables_dict["last_connected_sniffer"]
                )

        except zmq.ZMQError as e:
            pass

    def create_save_session_panel(self):

        """
        Popup message displayed when save session data button clicked.
        """

        save_session_content = BoxLayout(orientation="vertical")

        # self.session_popup_description = Label(text=f'Enter a name and then save the session data \n (alphanumeric characters only) \n\n Stored in sqlite database: \n {database_location}', halign="center", valign="center", text_size = (self.accordion.width-sp(50), None))

        self.session_popup_description = Label(
            text=f"Enter a name and then save the session data \n (alphanumeric characters only)",
            halign="center",
            valign="center",
            text_size=(self.accordion.width - sp(50), None),
        )

        self.save_session_textinput = TextInput(
            on_text_validate=self.save_session_into_database, multiline=False
        )

        save_button = Button(text="Save", on_press=self.save_session_into_database)

        save_session_content.add_widget(Label(size_hint_y=1))

        save_session_content.add_widget(self.session_popup_description)

        save_session_content.add_widget(Label(size_hint_y=0.2))

        horizontal_container = BoxLayout(orientation="horizontal", size_hint_y=0.4)
        horizontal_container.add_widget(Label(size_hint_x=0.3))
        horizontal_container.add_widget(self.save_session_textinput)
        horizontal_container.add_widget(Label(size_hint_x=0.3))

        save_session_content.add_widget(horizontal_container)

        save_session_content.add_widget(Label(size_hint_y=0.2))

        horizontal_container2 = BoxLayout(orientation="horizontal", size_hint_y=0.4)
        horizontal_container2.add_widget(Label(size_hint_x=0.1))
        horizontal_container2.add_widget(save_button)
        horizontal_container2.add_widget(
            Button(text="Copy Save Location", on_press=self.copy_database_location)
        )
        horizontal_container2.add_widget(Label(size_hint_x=0.1))

        save_session_content.add_widget(horizontal_container2)

        save_session_content.add_widget(Label(size_hint_y=1))

        return save_session_content

    def copy_database_location(self, calling_button: Button) -> None:

        """
        Copy database location to clipboard using pyperclip
        """

        database_location = os.path.join(
            self.gui_manager.resource_path, "assets/database/sessions.sqlite"
        )
        copy(database_location)

    def save_session_into_database(self, save_session_button: Button):

        """
        Validate and insert session data (sniffer dictionary) into sqlite database
        """

        session_to_save = self.save_session_textinput.text

        if session_to_save.isalnum():  # check alphanumeric condition
            if session_to_save[0].isnumeric():  # Can't start with a number condition
                self.session_popup_description.color = (1, 0, 0, 1)
                self.session_popup_description.text = (
                    "Can't start with a number.. -- blame sqlite."
                )

            else:

                json_session_data = (
                    self.gui_manager.sniffer_dictionary
                )  # JSON serialization faciliated by sqlite registration on insertion (see database_config.py for dictionary type)

                try:
                    cursor = db.cursor()
                    cursor.execute(
                        """INSERT OR IGNORE INTO sessions (session_name, session_data) VALUES ("{session}", "{json_session_data}")""".format(
                            session=session_to_save, json_session_data=json_session_data
                        )
                    )
                    db.commit()
                except:
                    self.session_popup_description.color = (1, 0, 0, 1)
                    self.session_popup_description.text = "Error saving data!"
                    return

                self.save_session_popup_object.dismiss()

        else:
            self.session_popup_description.color = (1, 0, 0, 1)

    def generate_keys(self, key_dir: str) -> Dict[str, Tuple[str, str]]:
        """
        Generate new cryptographic keys
        """
        pass

    def connect_to_remote_server(self, connect_to_remote_server_button: Button) -> None:

        """
        Connect to sniffer at remote location. (phone, webserver, etc)
        """

        if self.gui_manager.server_socket == None:

            req_port = connect_to_remote_server_button.port
            sub_port = req_port + 1
            remote_ip = connect_to_remote_server_button.text

            try:
                connect_string_req = f"tcp://{remote_ip}:{req_port}"
                connect_string_sub = f"tcp://{remote_ip}:{sub_port}"

                keys = zmq.auth.load_certificate(
                    os.path.join(
                        self.resource_path, "configuration/keys/client.key_secret"
                    )
                )
                server_key, _ = zmq.auth.load_certificate(
                    os.path.join(self.resource_path, "configuration/keys/server.key")
                )

                context = zmq.Context()
                self.gui_manager.server_socket = context.socket(
                    zmq.REQ
                )  # client/server pattern for guaranteed messages
                self.gui_manager.server_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
                self.gui_manager.server_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
                self.gui_manager.server_socket.setsockopt(
                    zmq.CURVE_SERVERKEY, server_key
                )
                self.gui_manager.server_socket.connect(connect_string_req)

                self.gui_manager.data_socket = context.socket(
                    zmq.SUB
                )  # PUB/SUB pattern for sniffer data
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_PUBLICKEY, keys[0])
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_SECRETKEY, keys[1])
                self.gui_manager.data_socket.setsockopt(zmq.CURVE_SERVERKEY, server_key)
                self.gui_manager.data_socket.connect(connect_string_sub)

                self.gui_manager.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")

                self.config_variables_dict["last_connected_sniffer"][0] = remote_ip
                self.config_variables_dict["last_connected_sniffer"][1] = req_port

            except Exception as e:

                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)

            self.connection_label.text = f"[color=#00ff00][b]Connected[/b][/color] to [color=#00ff00][b]{remote_ip}[/color][/b] on port [color=#00ff00][b]{req_port}[/color][/b]"

            self.remote_connect_dropdown.dismiss()

        else:
            # self.toggle_sniffer_connect_popup()
            self.gui_manager.kivy_application.switch_sniffer(
                [
                    connect_to_remote_server_button.text,
                    connect_to_remote_server_button.port,
                ]
            )

            self.remote_connect_dropdown.dismiss()

    def connect_to_local_server(self, connect_to_local_server_button: Button) -> None:

        """
        Connect visualizer to Localhost
        """

        if self.gui_manager.server_socket == None:

            try:
                req_port = int(self.server_port_textinput.text)
                sub_port = req_port + 1

                if req_port > 65534 or req_port < 1023:
                    raise Exception

            except:

                req_port = 12345
                sub_port = req_port + 1

            if self.gui_manager.sniffer_process == None:

                try:
                    keywords = {"port": req_port}
                    self.gui_manager.sniffer_process = Process(
                        name="sniffer", target=Sniffer, kwargs=keywords
                    )
                    self.gui_manager.sniffer_process.start()
                    atexit.register(
                        self.gui_manager.sniffer_process.terminate
                    )  # kill sniffer

                except:
                    # TODO:what types of error handling is required?
                    self.gui_manager.sniffer_process == None

                try:
                    connect_string_req = f"tcp://localhost:{req_port}"
                    connect_string_sub = f"tcp://localhost:{sub_port}"

                    keys = zmq.auth.load_certificate(
                        os.path.join(
                            self.resource_path, "configuration/keys/client.key_secret"
                        )
                    )
                    server_key, _ = zmq.auth.load_certificate(
                        os.path.join(
                            self.resource_path, "configuration/keys/server.key"
                        )
                    )

                    context = zmq.Context()
                    self.gui_manager.server_socket = context.socket(
                        zmq.REQ
                    )  # client/server pattern for guaranteed messages
                    self.gui_manager.server_socket.setsockopt(
                        zmq.CURVE_PUBLICKEY, keys[0]
                    )
                    self.gui_manager.server_socket.setsockopt(
                        zmq.CURVE_SECRETKEY, keys[1]
                    )
                    self.gui_manager.server_socket.setsockopt(
                        zmq.CURVE_SERVERKEY, server_key
                    )
                    self.gui_manager.server_socket.connect(connect_string_req)

                    self.gui_manager.data_socket = context.socket(
                        zmq.SUB
                    )  # PUB/SUB pattern for sniffer data
                    self.gui_manager.data_socket.setsockopt(
                        zmq.CURVE_PUBLICKEY, keys[0]
                    )
                    self.gui_manager.data_socket.setsockopt(
                        zmq.CURVE_SECRETKEY, keys[1]
                    )
                    self.gui_manager.data_socket.setsockopt(
                        zmq.CURVE_SERVERKEY, server_key
                    )
                    self.gui_manager.data_socket.connect(connect_string_sub)

                    self.gui_manager.data_socket.setsockopt_string(zmq.SUBSCRIBE, "")

                    self.config_variables_dict["last_connected_sniffer"][
                        0
                    ] = "localhost"
                    self.config_variables_dict["last_connected_sniffer"][1] = req_port

                except Exception as e:

                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)

            self.connection_label.text = f"[color=#00ff00][b]Connected[/b][/color] to [color=#00ff00][b]LocalHost[/color][/b] on port [color=#00ff00][b]{req_port}[/color][/b]"

        else:
            # self.toggle_sniffer_connect_popup()
            self.gui_manager.kivy_application.switch_sniffer(["localhost", 12345])

    def on_sniffer_checkbox_active(self, checkbox, value) -> None:
        pass

    def more_info(self, moreinfo_button: Button) -> None:
        pass

    def add_remote_connection(self, calling_button: Button) -> None:

        """ """

        ip = self.server_ip_textinput.text.strip()
        port_input = self.server_port_textinput.text.strip()

        try:
            var = socket.inet_aton(ip)  # validate IP address
        except:
            self.server_ip_textinput.text = "Error"
            self.server_ip_textinput.foreground_color = (1, 0, 0, 1)
            return

        try:
            port = int(port_input)
            if port > 65534 or port < 1023:
                raise Exception

        except:
            self.server_port_textinput.text = "Error"
            self.server_port_textinput.foreground_color = (1, 0, 0, 1)
            return

        self.server_ip_textinput.text = "Sucess!"
        self.server_ip_textinput.foreground_color = (0, 0, 0, 1)

        self.server_port_textinput.text = ""

        if not self.gui_manager.config_variables_dict["remote_connections"]:
            self.remote_connect_dropdown.children[0].clear_widgets()

        self.gui_manager.config_variables_dict["remote_connections"][ip] = port

        for connection in self.gui_manager.config_variables_dict[
            "remote_connections"
        ].keys():

            btn = Button(text=connection)
            btn.port = self.gui_manager.config_variables_dict["remote_connections"][
                connection
            ]
            btn.size_hint = (None, None)
            btn.width = dp(190)
            btn.height = dp(20)
            btn.background_color = (0, 0, 0, 1)

            btn.bind(on_press=self.connect_to_remote_server)

            self.remote_connect_dropdown.add_widget(btn)

    def create_sniffer_settings_panel(self) -> Popup:

        """
        Popup menu for configuring and connecting to Sniffer
        """

        size = (dp(390), dp(290))
        crypto_key_location = os.path.join(self.resource_path, "configuration/keys/")

        # Create Widgets

        base = BoxLayout(orientation="vertical", size=size)
        section = BoxLayout(orientation="horizontal")

        generate_keys_button = Button(
            text="Generate New Encryption Key-Pair",
            on_press=self.generate_keys,
            size_hint=(1, 1),
        )
        moreinfo_button = Button(
            text="Information", on_press=self.more_info, size_hint=(1, 1)
        )

        cryptographic_folder_label = Label(
            text=f"Location of cryptographic keys: {crypto_key_location}",
            halign="left",
            valign="center",
        )

        self.remote_connect_dropdown = DropDown()

        if not self.gui_manager.config_variables_dict["remote_connections"]:

            btn = Button(
                text="No Remote Connections",
                size_hint=(None, None),
                width=dp(190),
                height=45,
                background_color=(0, 0, 0, 1),
            )
            self.remote_connect_dropdown.add_widget(btn)

        else:

            for connection in self.gui_manager.config_variables_dict[
                "remote_connections"
            ].keys():

                btn = Button(text=connection)
                btn.port = self.gui_manager.config_variables_dict["remote_connections"][
                    connection
                ]
                btn.size_hint = (None, None)
                btn.width = dp(190)
                btn.height = dp(20)
                btn.background_color = (0, 0, 0, 1)
                btn.bind(on_press=self.connect_to_remote_server)

                self.remote_connect_dropdown.add_widget(btn)

        reset_button = Button(
            text="Reset",
            on_press=self.reset_session,
            size_hint_x=0.5,
        )

        remote_connect_button = Button(
            text="Connect to Remote Traffic", size_hint_x=1.7
        )
        remote_connect_button.bind(on_press=self.open_remote_connect_dropdown)

        local_connect_button = Button(
            text="Connect to Local Traffic",
            on_press=self.connect_to_local_server,
            size_hint_x=1.7,
        )

        add_remote_connection_button = Button(
            text="Add Remote Connection", on_press=self.add_remote_connection
        )

        self.server_name_textinput = TextInput(text="Name")
        self.server_ip_textinput = TextInput(text="IP Address")
        self.server_port_textinput = TextInput(text="Port")

        # Layout Widgets

        base.add_widget(Label(size_hint_y=1.5))

        section.add_widget(Label(size_hint_x=0.3))
        section.add_widget(Label(text="Automatically Connect on Startup"))
        section.add_widget(Label(size_hint_x=0.2))
        section.add_widget(self.auto_connect_checkbox)
        section.add_widget(Label(size_hint_x=0.1))
        section.add_widget(reset_button)
        section.add_widget(Label(size_hint_x=0.1))
        base.add_widget(section)

        base.add_widget(Label(size_hint_y=0.5))

        remote_connect_button_content = BoxLayout(orientation="horizontal")
        remote_connect_button_content.add_widget(Label(size_hint_x=0.1))
        remote_connect_button_content.add_widget(local_connect_button)
        remote_connect_button_content.add_widget(Label(size_hint_x=0.1))
        remote_connect_button_content.add_widget(remote_connect_button)
        remote_connect_button_content.add_widget(Label(size_hint_x=0.1))
        base.add_widget(remote_connect_button_content)

        base.add_widget(Label())
        base.add_widget(Label())

        server_ip_textinput_content = BoxLayout(orientation="horizontal")
        server_ip_textinput_content.add_widget(Label(size_hint_x=0.1))
        server_ip_textinput_content.add_widget(self.server_name_textinput)
        server_ip_textinput_content.add_widget(Label(size_hint_x=0.1))
        server_ip_textinput_content.add_widget(self.server_ip_textinput)
        server_ip_textinput_content.add_widget(Label(size_hint_x=0.1))
        server_ip_textinput_content.add_widget(self.server_port_textinput)
        server_ip_textinput_content.add_widget(Label(size_hint_x=0.1))
        base.add_widget(server_ip_textinput_content)

        base.add_widget(Label(size_hint_y=0.2))

        store_remote_sniffer_content = BoxLayout(orientation="horizontal")
        store_remote_sniffer_content.add_widget(Label(size_hint_x=0.5))
        store_remote_sniffer_content.add_widget(add_remote_connection_button)
        store_remote_sniffer_content.add_widget(Label(size_hint_x=0.5))
        base.add_widget(store_remote_sniffer_content)

        base.add_widget(Label())
        base.add_widget(Label())

        moreinfo_button_content = BoxLayout(orientation="horizontal")
        moreinfo_button_content.add_widget(Label(size_hint_x=1))
        moreinfo_button_content.add_widget(moreinfo_button)
        moreinfo_button_content.add_widget(Label(size_hint_x=1))
        base.add_widget(moreinfo_button_content)

        base.add_widget(Label(size_hint_y=0.2))

        moreinfo_button_content2 = BoxLayout(orientation="horizontal")
        moreinfo_button_content2.add_widget(Label(size_hint_x=0.25))
        moreinfo_button_content2.add_widget(generate_keys_button)
        moreinfo_button_content2.add_widget(Label(size_hint_x=0.25))
        base.add_widget(moreinfo_button_content2)

        base.add_widget(Label())

        return base

    def apply_color(self, apply_color_button: Button):

        try:
            color_value = get_color_from_hex(
                self.hex_input.text
            )  # e.g. FFFFFFFF to [1,1,1,1] (RGBA)
            if len(color_value) == 4 or len(color_value) == 3:
                pass
            else:
                return
        except:
            return  # unable to get hex value so don't proceed

        for child in self.features_dropdown.children[0].children:
            if child.id == self.selected_protocol_button.text:
                child.color = color_value


        if self.selected_protocol_button.text == "TCP Protocol":
            self.gui_manager.config_variables_dict["TCP Protocol Color"] = color_value

        elif self.selected_protocol_button.text == "UDP Protocol":
            self.gui_manager.config_variables_dict["UDP Protocol Color"] = color_value


        elif self.selected_protocol_button.text == "Other Protocol":
            self.gui_manager.config_variables_dict["OTHER Protocol Color"] = color_value

        elif self.selected_protocol_button.text == "Data IN":
            self.gui_manager.config_variables_dict["Data IN Color"] = color_value

        elif self.selected_protocol_button.text == "Data OUT":
            self.gui_manager.config_variables_dict["Data OUT Color"] = color_value

        elif self.selected_protocol_button.text == "Summary Data":
            self.gui_manager.config_variables_dict["Summary Data Color"] = color_value


        self.selected_protocol_button.text = "Select Feature"
        self.selected_protocol_button.color = (1, 1, 1, 1)



    def open_remote_connect_dropdown(self, call_button) -> None:

        """
        Kivy dropdown bug hack
        """

        self.remote_connect_dropdown.open(call_button)

    def open_features_dropdown(self, call_button) -> None:

        """
        Kivy dropdown bug hack
        """

        self.features_dropdown.open(call_button)

    def features_dropdown_color_text_change(self, *btn) -> None:

        """ """

        self.features_dropdown.select(btn[0].text)

        # BUG: color must not be getting saved in config_variables_dict after selection
        self.selected_protocol_button.color = self.gui_manager.config_variables_dict[
            f"{btn[0].text} Color"
        ]

    def validate_color_textinput(self, text_input: TextInput, text: str):

        """
        Validate input color from user
        """

        try:
            self.apply_color_button.color = get_color_from_hex(text)
            # self.color_label.color = get_color_from_hex(text)

            self.gui_manager.my_computer.exempt_button.background_color = get_color_from_hex(text)

        except:
            pass


    def on_color_selection(
        self, colorwheel: ColorWheel, value: ObservableReferenceList
    ) -> None:

        """
        Called on ColorWheel selection.
        """

        # self.color_label.color = self.clr_picker.color
        self.hex_input.text = str(self.clr_picker.hex_color)
        self.apply_color_button.color = self.clr_picker.color


    
