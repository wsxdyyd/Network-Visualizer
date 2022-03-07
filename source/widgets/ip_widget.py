# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.


import os
import time
from typing import Protocol

from kivy.uix.boxlayout import BoxLayout
from utilities.utils import map_to_range, distance_between_points, remove_inline_quotes
from math import sin, cos, pi
from random import random, randrange
import datetime


from pyperclip import copy

from utilities.database_config import db


from kivy.metrics import sp, dp
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.dropdown import DropDown
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
        self.id = kwargs["ip"]  # ip address used as unique idenifier
        self.window_x = kwargs["window_x"]
        self.window_y = kwargs["window_y"]
        self.center_X = self.window_x / 2
        self.center_Y = self.window_y / 2
        self.latitude = kwargs["ip_latitude"]
        self.longitude = kwargs["ip_longitude"]
        self.longitude_x = kwargs["ip_longitude_x"]
        self.latitude_y = kwargs["ip_latitude_y"]
        self.ip_data = kwargs["ip_data"]
        self.resource_path = kwargs["resource_path"]
        self.gui_manager = kwargs["gui_manager"]

        self.country = kwargs["country"]  # issue with Nonetype
        self.country_label = "Unresolved" if self.country == None else self.country

        self.city = kwargs["city"]  # issue with Nonetype
        self.city_label = "Unresolved" if self.city == None else self.city

        # self.country = "Unresolved" if kwargs['country'] == None else kwargs['country']
        # self.city = 'Unresolved' if kwargs['city'] == None else kwargs['city']
        self.whois_description = Label()
        self.whois_description.text = "Waiting on update"
        self.size = ("50sp", "50sp")
        self.x_position = self.pos[0]
        self.y_position = self.pos[1]

        self.random_radius = randrange(sp(100), sp(200))
        self.pos = (random() * self.window_x, random() * self.window_y)
        self.old_pos = self.pos

        self.spring_constant_1 = 0.04
        self.spring_constant_2 = 0.08
        self.colision = 0
        self.delta_new_packet = 0
        self.new_pos = (0, 0)
        self.banlist_count = 0
        self.connection_opacity = 0

        #self.protocol_color_dict = kwargs["protocol_dict"]

        self.data_in_delta = 0
        self.data_out_delta = 0
        self.new_data = True
        self.show = False
        self.data = True
        self.menu_boolean = False
        self.do_layout = False
        self.malicious_ip = False
        self.attach = True
        self.init_position = False

        if self.gui_manager.ip_labels == True:
            self.mylabel_bool = True
        else:
            self.mylabel_bool = False
        self.exempt = False

        self.menu_popup = None
        self.whois_popup = None
        self.whois_information = None
        self.city_widget = None
        self.country_widget = None

        # Graph view
        self.graph_position = self.pos
        self.initial_graph_position = self.graph_position
        #

        # Mercator view
        self.mercator_position = None
        self.initial_mercator_position = None
        self.resize = False
        self.packet_display = False
        #

        # GUI

        self.label = Label()
        self.label.text = self.id
        self.label.font_size = sp(15)
        self.label.font_blended = False
        self.label.font_hinting = "normal"
        self.label.pos = (dp(-18), dp(1))
        self.label.color = [1, 1, 1, 1]

        self.container = FloatLayout()
        self.container.pos = self.pos
        self.container.size_hint = (None, None)
        self.container.size = (dp(50), dp(50))

        self.icon_image = Image()
        self.icon_image.source = os.path.join(
            self.resource_path, "assets/images/UI/ip.png"
        )
        self.icon_image.size_hint = (None, None)
        self.icon_image.size = (dp(10), dp(10))
        self.icon_image.pos = (dp(4), dp(4))

        self.display_menu_button = Button()
        self.display_menu_button.size_hint = (None, None)
        self.display_menu_button.pos_hint = (None, None)
        self.display_menu_button.pos = (dp(5), dp(5))
        self.display_menu_button.size = (dp(8), dp(8))
        self.display_menu_button.background_color = (0, 0, 1, 0)
        self.display_menu_button.on_press = self.toggle_menu

        self.icon_scatter_widget = Scatter()
        self.icon_scatter_widget.size_hint = (None, None)
        self.icon_scatter_widget.pos = self.pos
        self.icon_scatter_widget.size = (dp(18), dp(18))

        self.features_dropdown = DropDown()

        # supported_features = ['Tag Malicious', 'Untag Malicious',] #extend to support more features
        # #self.colored_buttons = {}
        # for feature in supported_features:

        btn = Button(
            text="Display on Graph",
            size_hint=(None, None),
            width=sp(125),
            height=44,
            color=(1, 1, 1, 1),
            background_color=(0, 0, 0, 1),
        )

        self.features_dropdown.add_widget(btn)

        btn = Button(
            text="Tag Malicious",
            size_hint=(None, None),
            width=sp(125),
            height=44,
            color=(1, 0, 0, 1),
            background_color=(0, 0, 0, 1),
        )

        # btn.bind(on_release=lambda btn: self.features_dropdown.select(btn.text))

        btn.bind(
            on_release=self.tag_malicious
        )  # We use the "selected" protocol button text when widget.update() Canvas Line color
        # btn.color = self.gui_manager.config_variables_dict[f"{feature} Color"]

        self.features_dropdown.add_widget(btn)

        btn = Button(
            text="Tag Benign",
            size_hint=(None, None),
            width=sp(125),
            height=44,
            color=(0, 1, 0, 1),
            background_color=(0, 0, 0, 1),
        )

        btn.bind(on_release=self.untag_malicious)

        self.features_dropdown.add_widget(btn)

        # self.colored_buttons[feature] = btn

        # self.icon_scatter_widget.environmental_manager = self

        # with self.icon_scatter_widget.canvas.before:
        #     Color(1,1,1,.2)
        #     RoundedRectangle(size=self.icon_scatter_widget.size,
        #                      pos=(0,0),
        #                      radius=[(50, 50), (50, 50), (50, 50), (50, 50)]
        #                      )

        # self.packet_stream = Scatter()
        # self.packet_stream.size_hint = (None,None)
        # self.packet_stream.pos = self.icon_scatter_widget.pos
        # self.packet_stream.size = ("200sp","200sp")
        # self.packet_stream.gui_manager = self

        # self.packet_stream_scrollview = ScrollView()
        # self.packet_stream_scrollview.scroll_distance = 50
        # self.packet_stream_scrollview.size = ("500sp", "500sp")
        # self.packet_stream_scrollview.pos = (0,"75sp")

        self.display_menu_button.add_widget(self.icon_image)
        self.icon_scatter_widget.add_widget(self.display_menu_button)

        if self.mylabel_bool == True:
            self.icon_scatter_widget.add_widget(self.label)
        self.container.add_widget(self.icon_scatter_widget)
        self.add_widget(self.container)

        self.icon_scatter_widget.pos = self.pos

        # Enter into sql database
        cursor = db.cursor()

        # TODO: OR IGNORE....acceptable logic?
        cursor.execute(
            f"""INSERT OR IGNORE INTO Live (ip, location_city, location_country,  longitude, latitude, description, total_packets, data_in, data_out, blocked) VALUES ( '{self.id}', '{self.city}', '{self.country}', '{self.longitude}', '{self.latitude}', "{self.whois_description}", '{self.gui_manager.sniffer_dictionary[self.id]['packet_count']}', '{self.gui_manager.sniffer_dictionary[self.id]['data_in']}', '{self.gui_manager.sniffer_dictionary[self.id]['data_out']}', '{self.malicious_ip}' )"""
        )

        db.commit()

        table_row = self.generate_table_row()
        self.gui_manager.live_table_dictionary[self.id] = table_row
        self.gui_manager.table.add_widget(table_row)

        self.menu_popup = self.make_display_menu()

        # if self.gui_manager.country_dictionary[self.country][1][self.city][0].labels == True:
        #     self.icon_scatter_widget.add_widget(self.label)

    def generate_table_row(self) -> BoxLayout:

        """
        Construct a row for Table view
        """

        length_per_label = self.gui_manager.window_x / 6

        box_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            pos=(0, 0),
            padding=1,
            size=(self.gui_manager.window_x, dp(17)),
        )

        ip_button = Button()
        ip_button.text = self.id
        ip_button.id = self.id
        ip_button.bind(on_press=self.live_table_menu)

        if self.malicious_ip == True:

            text_color = (1, 0, 0, 1)
            ip_button.background_color = (0.3, 0.3, 0.3, 1)
            ip_button.color = (1, 0, 0, 1)

        else:

            if self.gui_manager.table_count % 2 == 0:
                ip_button.background_color = (0, 1, 0, 0.8)
                ip_button.border = (0,0,0,0)
                ip_button.color = (1, 1, 1, 1)
                text_color = (1, 1, 1, 1)

            else:
                ip_button.background_color = (0, 1, 0, 0.3)
                ip_button.color = (1, 1, 1, 1)
                ip_button.border = (0,0,0,0)
                text_color = (1, 1, 1, 0.7)

            self.gui_manager.table_count += 1

        description_label = self.make_label(
            self.whois_description.text, length_per_label
        )
        description_label.color = text_color

        city_label = self.make_label(self.city_label, length_per_label)
        city_label.color = text_color

        country_label = self.make_label(self.country_label, length_per_label)
        country_label.color = text_color

        packet_label = self.make_label(
            str(self.ip_data["packet_count"]), length_per_label
        )
        packet_label.color = text_color

        data_in_label = self.make_label(
            f"{self.ip_data['data_in']/1000000:.6f}", length_per_label
        )
        data_in_label.color = text_color

        data_out_label = self.make_label(
            f"{self.ip_data['data_out']/1000000:.6f}", length_per_label
        )
        data_out_label.color = text_color

        ip_button_container = BoxLayout(orientation="horizontal")
        ip_button_container.add_widget(Label(size_hint_x=0.1))
        ip_button_container.add_widget(ip_button)
        ip_button_container.add_widget(Label(size_hint_x=0.1))

        box_layout.add_widget(ip_button_container)
        box_layout.add_widget(description_label)
        box_layout.add_widget(city_label)
        box_layout.add_widget(country_label)
        box_layout.add_widget(packet_label)
        box_layout.add_widget(data_in_label)
        box_layout.add_widget(data_out_label)

        return box_layout

    def generate_malicious_table_row(self) -> BoxLayout:

        """
        Construct a row for Malicious view
        """

        length_per_label = self.gui_manager.window_x / 6

        box_layout = BoxLayout(
            orientation="horizontal",
            size_hint=(None, None),
            pos=(0, 0),
            padding=1,
            size=(self.gui_manager.window_x, dp(20)),
        )

        ip_button = Button()
        ip_button.text = self.id
        ip_button.id = self.id
        # ip_button.on_press = self.display_menu
        ip_button.bind(on_press=self.live_table_menu)

        if self.gui_manager.malicious_table_count % 2 == 0:
            ip_button.background_color = (0.3, 0.3, 0.3, 1)
            ip_button.color = (1, 0, 0, 1)
            text_color = (1, 1, 1, 1)

        else:
            ip_button.background_color = (0.15, 0.15, 0.15, 1)
            ip_button.color = (1, 0, 0, 1)
            text_color = (1, 1, 1, 0.7)

        self.gui_manager.malicious_table_count += 1

        description_label = self.make_label(
            self.whois_description.text, length_per_label
        )
        description_label.color = text_color

        banlist_count_label = self.make_label(str(self.banlist_count), length_per_label)
        banlist_count_label.color = text_color

        timestamp_label = self.make_label(self.malicious_timestamp, length_per_label)
        timestamp_label.color = text_color

        country_label = self.make_label(self.country_label, length_per_label)
        country_label.color = text_color

        packet_label = self.make_label(
            str(self.ip_data["packet_count"]), length_per_label
        )
        packet_label.color = text_color

        data_in_label = self.make_label(
            f"{self.ip_data['data_in']/1000000:.6f}", length_per_label
        )
        data_in_label.color = text_color

        data_out_label = self.make_label(
            f"{self.ip_data['data_out']/1000000:.6f}", length_per_label
        )
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

    def tag_malicious(self, *button: Button) -> None:

        """
        Block IP -- firewall functionality not implmented
        """

        if self.malicious_ip == False:  # check to see if already malciious

            time_stamp = time.time()
            self.malicious_timestamp = datetime.datetime.fromtimestamp(
                time_stamp
            ).strftime("%d-%m-%Y")

            self.icon_image.source = os.path.join(
                self.resource_path, "assets/images/UI/malicious.png"
            )

            if self.id in self.gui_manager.malicious_ips_dictionary:
                self.banlist_count = self.gui_manager.malicious_ips_dictionary[self.id]

            if self.id not in self.gui_manager.malicious_ips_local_database:

                cursor = db.cursor()
                sql = f"""INSERT OR IGNORE INTO malicious_ips (ip, description, ban_lists, time_stamp, location_country,  packet_count, data_in, data_out) VALUES ( "{self.id}", "{self.whois_description.text}", {self.banlist_count}, "{self.malicious_timestamp}", "{self.country}", {self.ip_data['packet_count']}, {self.ip_data['data_in']}, {self.ip_data['data_out']}) """
                cursor.execute(sql)

                db.commit()

            for child_widget in self.gui_manager.live_table_dictionary[
                self.id
            ].children:
                if isinstance(child_widget, Button):
                    child_widget.background_color = (0.3, 0.3, 0.3, 1)
                    child_widget.color = (1, 0, 0, 1)

                else:
                    child_widget.color = text_color = (1, 0, 0, 1)

            if self.id not in self.gui_manager.malicious_table_dictionary:
                malicous_row = self.generate_malicious_table_row()
                self.gui_manager.malicious_table_dictionary[self.id] = malicous_row
                self.gui_manager.malicious_table.add_widget(malicous_row)

            self.malicious_ip = True

            try:
                self.features_dropdown.dismiss()
            except:
                pass

    def untag_malicious(self, *button: Button) -> None:

        """
        Untag malicious IP -- firewall functionality not implmented
        """

        if (
            self.malicious_ip == True
            and self.id not in self.gui_manager.malicious_ips_dictionary
        ):  # make sure ip has already been malicious and not in curated ban list from Internet

            self.icon_image.source = os.path.join(
                self.resource_path, "assets/images/UI/ip.png"
            )

            malicious_row = self.gui_manager.malicious_table_dictionary[self.id]
            self.gui_manager.malicious_table.remove_widget(malicious_row)
            del self.gui_manager.malicious_table_dictionary[self.id]

            for child_widget in self.gui_manager.live_table_dictionary[
                self.id
            ].children:

                if isinstance(child_widget, Button):
                    child_widget.background_color = (0, 1, 0, 1)
                    child_widget.color = (1, 1, 1, 1)
                else:
                    child_widget.color = (1, 1, 1, 1)

            if self.id in self.gui_manager.malicious_ips_local_database:
                del self.gui_manager.malicious_ips_local_database[self.id]

            cursor = db.cursor()
            sql = f"""DELETE FROM malicious_ips WHERE ip="{self.id}" """
            cursor.execute(sql)
            db.commit()

            self.malicious_ip = False

            try:
                self.features_dropdown.dismiss()
            except:
                pass




    def remove_whois_popup(self, button: Button) -> None:

        """
        Remove whois popup for associated IP
        """

        self.gui_manager.persistent_widget_container.remove_widget(self.whois_popup)
        self.whois_popup = None
        self.display_whois_popup = False


    def copy_abuse_emails(self, calling_button:Button) -> None:
        
        """
        Copy whois abuse email to clipboard
        """

        abuse_email = self.gui_manager.ip_whois_info_dict[self.id]["nets"][0]["emails"]
        copy(str(abuse_email))



    def toggle_my_label(self) -> None:

        """
        Toggles My_Computer widget label on/off
        """

        if self.mylabel_bool == True:
            try:
                self.icon_scatter_widget.remove_widget(self.label)
            except:
                pass

            self.mylabel_bool = False

        else:
            try:
                self.icon_scatter_widget.add_widget(self.label)
            except:
                pass

            self.mylabel_bool = True

    def live_table_menu(self, button) -> None:

        self.features_dropdown.open(button)

    def toggle_menu(self, *args) -> None:

        """
        Toggle menu when user clicks on IP Widget.
        """

        if self.menu_boolean == False:
            self.menu_boolean = True

            self.gui_manager.persistent_widget_container.add_widget(self.menu_popup)
            self.gui_manager.misc_update_dictionary["ip"][f"{self.id}"] = self

        elif self.menu_boolean == True:
            self.menu_boolean = False

            self.gui_manager.persistent_widget_container.remove_widget(self.menu_popup)
            del self.gui_manager.misc_update_dictionary["ip"][f"{self.id}"]

    def make_exempt(self) -> None:

        """
        Toggle exempt status for Widget to be affected by graph display.
        """

        if self.exempt == True:
            self.exempt_button.text = "Exempt"
            self.exempt = False

        else:
            self.exempt_button.text = "Non-Exempt"
            self.exempt = True

    def make_display_menu(self) -> Scatter:

        """
        Create popup menu when user clicks on IP widget.
        """

        packet_count = self.ip_data["packet_count"]
        data_in = self.ip_data["data_in"]
        data_out = self.ip_data["data_out"]

        size = (dp(155), dp(180))

        menu_popup = Scatter()
        menu_popup.size_hint = (None, None)
        menu_popup.size = size
        menu_popup.pos = (
            self.icon_scatter_widget.pos[0] + 25,
            self.icon_scatter_widget.pos[1] + 25,
        )
        menu_popup.id = self.id + "p"

        with menu_popup.canvas.before:
            Color(1, 1, 1, 0.1)
            RoundedRectangle(
                size=menu_popup.size,
                pos=(0, 0),
                radius=[(20, 20), (20, 20), (20, 20), (20, 20)],
            )

        if menu_popup.pos[0] + sp(350) > self.window_x:
            menu_popup.pos = (self.window_x - sp(375), menu_popup.pos[1])

        if menu_popup.pos[1] + sp(155) > self.window_y:
            menu_popup.pos = (menu_popup.pos[0], self.window_y - sp(150))

        grid_layout = BoxLayout(orientation="vertical")
        grid_layout.size_hint = (None, None)
        #grid_layout.size = (sp(150), sp(125))
        grid_layout.size = (size[0], size[1]-dp(10))
        grid_layout.pos = (sp(3), sp(5))

        ip_label = Label()
        ip_label.text = self.id

        self.packet_label = Label()
        self.packet_label.text = "Packet Count: " + str(packet_count)
        self.packet_label.markup = True
        self.packet_label.font_size = sp(12)

        self.data_IN_label = Label()
        self.data_IN_label.text = f"Data IN (MB): {data_in/1000000.0:.6f}"
        self.data_IN_label.markup = True
        self.data_IN_label.font_size = sp(12)

        self.data_OUT_label = Label()
        self.data_OUT_label.text = f"Data OUT (MB): {data_out/1000000.0:.6f}"
        self.data_OUT_label.markup = True
        self.data_OUT_label.font_size = sp(12)

        tag_malicoous_button = Button()
        tag_malicoous_button.text = "Tag Malicious"
        tag_malicoous_button.background_normal = os.path.join(
            self.resource_path, "assets/images/buttons/red.png"
        )
        tag_malicoous_button.background_down = os.path.join(
            self.resource_path, "assets/images/buttons/red_down.png"
        )
        tag_malicoous_button.bind(on_press=self.tag_malicious)
        tag_malicoous_button.font_size = sp(12)
        tag_malicoous_button.border = (0, 0, 0, 0)

        self.exempt_button = Button()
        self.exempt_button.on_press = self.make_exempt
        self.exempt_button.background_normal = os.path.join(
            self.resource_path, "assets/images/buttons/kivy-teal-4.png"
        )
        self.exempt_button.background_down = os.path.join(
            self.resource_path, "assets/images/buttons/teal_down.png"
        )
        self.exempt_button.border = (0, 0, 0, 0)
        self.exempt_button.font_size = sp(12)

        if self.exempt:
            self.exempt_button.text = "Non-Exempt"
        else:
            self.exempt_button.text = "Exempt"

        whois_button = Button()
        whois_button.text = "Copy Abuse Email"
        whois_button.background_color = (.5,.5,.5,0.8)
        whois_button.bind(on_press=self.copy_abuse_emails)
        whois_button.font_size = sp(12)
        whois_button.border = (1, 1, 1, 1)

        untag_malicious_button = Button()
        untag_malicious_button.text = "Untag Malicious"
        untag_malicious_button.background_normal = os.path.join(
            self.resource_path, "assets/images/buttons/green.png"
        )
        untag_malicious_button.background_down = os.path.join(
            self.resource_path, "assets/images/buttons/green_down.png"
        )
        untag_malicious_button.bind(on_press=self.untag_malicious)
        untag_malicious_button.font_size = sp(12)
        untag_malicious_button.border = (0, 0, 0, 0)

        dismiss_button = Button()
        dismiss_button.text = "Dismiss"
        dismiss_button.background_color = [1, 1, 1, 0.1]
        dismiss_button.on_press = self.toggle_menu
        dismiss_button.font_size = sp(12)
        dismiss_button.border = (0, 0, 0, 0)

        toggle_label = Button()
        toggle_label.on_press = self.toggle_my_label
        toggle_label.font_size = sp(15)
        toggle_label.text = self.id
        toggle_label.background_color = (0.3, 0.3, 0.3, 0.9)
        toggle_label.background_down = os.path.join(
            self.resource_path, "assets/images/buttons/black.png"
        )

        label_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )

        label_container.add_widget(Label(size_hint_x=0.25))
        label_container.add_widget(toggle_label)
        label_container.add_widget(Label(size_hint_x=0.25))
        grid_layout.add_widget(label_container)
        grid_layout.add_widget(Label(size_hint_y=1))

        grid_layout.add_widget(self.whois_description)
        grid_layout.add_widget(Label(size_hint_y=1))
        grid_layout.add_widget(self.packet_label)
        grid_layout.add_widget(Label(size_hint_y=0.5))
        grid_layout.add_widget(self.data_IN_label)
        grid_layout.add_widget(Label(size_hint_y=0.25))
        grid_layout.add_widget(self.data_OUT_label)
        grid_layout.add_widget(Label(size_hint_y=1))

        excempt_button_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )
        excempt_button_container.add_widget(Label(size_hint_x=0.2))
        excempt_button_container.add_widget(self.exempt_button)
        excempt_button_container.add_widget(Label(size_hint_x=0.2))
        grid_layout.add_widget(excempt_button_container)

        grid_layout.add_widget(Label(size_hint_y=0.2))

        whois_button_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )
        whois_button_container.add_widget(Label(size_hint_x=0.2))
        whois_button_container.add_widget(whois_button)
        whois_button_container.add_widget(Label(size_hint_x=0.2))
        grid_layout.add_widget(whois_button_container)

        grid_layout.add_widget(Label(size_hint_y=0.2))

        tag_malicious_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )
        tag_malicious_container.add_widget(Label(size_hint_x=0.2))
        tag_malicious_container.add_widget(tag_malicoous_button)
        tag_malicious_container.add_widget(Label(size_hint_x=0.2))
        grid_layout.add_widget(tag_malicious_container)

        grid_layout.add_widget(Label(size_hint_y=0.2))

        untag_malicious_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )
        untag_malicious_container.add_widget(Label(size_hint_x=0.2))
        untag_malicious_container.add_widget(untag_malicious_button)
        untag_malicious_container.add_widget(Label(size_hint_x=0.2))
        grid_layout.add_widget(untag_malicious_container)

        grid_layout.add_widget(Label(size_hint_y=0.3))

        dismiss_container = BoxLayout(
            orientation="horizontal", size_hint_x=1, size_hint_y=1
        )
        dismiss_container.add_widget(Label(size_hint_x=1))
        dismiss_container.add_widget(dismiss_button)
        dismiss_container.add_widget(Label(size_hint_x=1))
        grid_layout.add_widget(dismiss_container)

        grid_layout.add_widget(Label(size_hint_y=0.1))

        menu_popup.add_widget(grid_layout)

        return menu_popup

    def set_position(self) -> tuple[float, float]:

        """
        Calculate x and y screen position for IP widget.
        """

        if self.gui_manager.current == "graph":

            x = self.gui_manager.country_dictionary[self.country][1][self.city][0].pos[
                0
            ] + dp(150) * sin(2 * pi * random())
            y = self.gui_manager.country_dictionary[self.country][1][self.city][0].pos[
                1
            ] + dp(150) * cos(2 * pi * random())

            self.pos = [x, y]
            self.icon_scatter_widget.pos = self.pos
            self.menu_popup.pos = self.pos

    def set_mercator_layout(self) -> None:

        """
        Called when screenmanager view is changed to mercator view.
        """

        self.graph_position = self.icon_scatter_widget.pos
        self.pos = self.mercator_position
        self.icon_scatter_widget.pos = self.mercator_position

    def set_graph_layout(self) -> None:

        """
        Called when screenmanager view is changed to graph view.
        """

        self.mercator_position = self.icon_scatter_widget.pos
        self.pos = self.graph_position
        self.icon_scatter_widget.pos = self.graph_position

    def update(self, **kwargs) -> None:

        """
        Update GUI widget. Called every cycle.
        """

        self.state = kwargs["state"]
        graph = self.state
        last_packet = kwargs["last_packet"]
        city_position = kwargs["city_widget"].icon_scatter_widget.pos

        # Ensure ip widget stays on screen
        # if self.x+50 > self.window_x:
        #     self.x = self.window_x - 25
        #     self.icon_scatter_widget.pos = self.pos
        # elif self.x < 0:
        #     self.x = 25
        #     self.icon_scatter_widget.pos = self.pos
        # elif self.y+50 > self.window_y:
        #     self.y = self.window_y - 25
        #     self.icon_scatter_widget.pos = self.pos
        # elif self.y < 0:
        #     self.y = 25
        #     self.icon_scatter_widget.pos = self.pos
        ######

        if self.attach == True:  # check to see if we are attached to city

            distance_to_city, x_distance, y_distance = distance_between_points(
                city_position, self.pos
            )

            if distance_to_city > 200:  # if more than 200 pixels away from city

                self.pos[0] += x_distance * self.spring_constant_1
                self.pos[1] += y_distance * self.spring_constant_1
                self.icon_scatter_widget.pos = self.pos

            else:
                self.attach = False

        # map data from bytes to pixel length (green and blue lines)
        # range is mapped from 0-largest_data_from/to_IP --> 0-50 pixels (compares data relatively)
        data_in = map_to_range(
            self.ip_data["data_in"], 0, self.gui_manager.ip_largest_data_in, 0, 50
        )
        data_out = map_to_range(
            self.ip_data["data_out"], 0, self.gui_manager.ip_largest_data_out, 0, 50
        )

        # draw ip widget lines
        self.canvas.before.clear()
        with self.canvas.before:

            if self.connection_opacity > 0:  # packet delta less than 20 seconds

                self.gui_manager.country_dictionary[self.country][1][self.city][
                    0
                ].new_data_counter = time.time()

                if self.malicious_ip == True:
                    Color(1, 0, 0, self.connection_opacity)

                else:  # select appropriate color according to the protocol of the last packet

                    protocol_color = self.gui_manager.config_variables_dict[last_packet +" Protocol Color"]
                    protocol_color[3] = self.connection_opacity
                    Color(rgba=protocol_color)

            else:  # new packet delta greater than 20 seconds use grey color
                Color(1, 1, 1, 0.3)

            # BUG
            # IF self.city_widget.show  == False:
            #   comtinue
            Line(
                points=(
                    city_position[0] + dp(8),
                    city_position[1] + dp(8),
                    self.icon_scatter_widget.pos[0] + dp(8),
                    self.icon_scatter_widget.pos[1] + dp(8),
                ),
                width=1,
            )

            RoundedRectangle(
                size=self.icon_scatter_widget.size,
                pos=self.icon_scatter_widget.pos,
                radius=[(50, 50), (50, 50), (50, 50), (50, 50)],
            )

            x, y = self.icon_scatter_widget.pos

            Color(rgba=self.gui_manager.config_variables_dict["Data IN Color"])
            Line(points=[x, y, x + data_in, y], width=1)

            Color(rgba=self.gui_manager.config_variables_dict["Data OUT Color"])
            Line(points=[x, y - sp(5), x + data_out, y - sp(5)], width=1)

            if self.menu_boolean and self.mylabel_bool == False:
                Color(1, 1, 1, 0.3)
                Line(
                    points=[
                        self.icon_scatter_widget.pos[0] + sp(10),
                        self.icon_scatter_widget.pos[1] + sp(10),
                        self.menu_popup.pos[0] + sp(77),
                        self.menu_popup.pos[1],
                    ],
                    width=sp(1),
                )