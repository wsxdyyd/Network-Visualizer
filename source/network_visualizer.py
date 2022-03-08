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


if __name__ == "__main__":  # start like this to prevent a bug with microsoft OS multithreading

    # Standard Library
    import multiprocessing
    multiprocessing.freeze_support()  # required by pyinstaller to be called ASAP

    from importlib import reload
    import os
    from requests import get
    import sys
    import webbrowser

    # Kivy Library
    import kivy
    from kivy.app import App
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.metrics import sp
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.label import Label
    from kivy.uix.popup import Popup
    from kivy.uix.widget import Widget

    # Network Visualizer
    import gui_manager
    from gui_manager import GUI_Manager # Root program class. No restart required to update code dynamically (hotkey: r)


    os.environ["KIVY_NO_ARGS"] = "1"
    #os.environ["KIVY_NO_CONSOLELOG"] = "1"  # Comment out when packaging with pyinstaller

    class Application(App):

        """
        Kivy Application base class.
        """

        def animate_widget(self, speed, key) -> None:

            """
            Testing widget animations
            """

            if key == 'e':
      
                self.gui_manager.my_computer.phase_slider.value += speed
        
            elif key == 'd':

           
                self.gui_manager.my_computer.phase_slider.value += speed
            
                self.gui_manager.country_dictionary['United States'][0].phase_slider.value -= speed

            elif key == 'f':

                self.gui_manager.my_computer.phase_slider.value += speed
            
                self.gui_manager.country_dictionary['United States'][0].phase_slider.value -= speed
            
                self.gui_manager.country_dictionary['Unresolved'][0].phase_slider.value += speed*2

           

        def build(self) -> Widget:

            """
            Kivy application constructor.
            """

            super().__init__()

            if getattr(sys, "frozen", False):

                # If the application is run as a bundle, the PyInstaller bootloader
                # extends the sys module by a flag frozen=True and sets the app
                # path into variable _MEIPASS'.
                self.resource_path = sys._MEIPASS

            else:  # otherwise get the directory where the python file is executed

                self.resource_path = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )

            Window.maximize()  # start fullscreen
            self.title = "Network Visualizer"

            self.icon = os.path.join(
                self.resource_path, "assets/images/UI/Network_Visualizer.png"
            )
            self.scheduled_animations = []

            self.keyboard = Window.request_keyboard(self.on_keyboard_closed, self.root)
            self.keyboard.bind(on_key_down=self.on_keyboard_down)

            self.rootWidget = BoxLayout()  # placeholder root widget
            self.gui_manager = GUI_Manager(
                kivy_application=self,
                resource_path=self.resource_path,
                switch_sniffer_info=None,
            )  # Program logic found here
            self.rootWidget.add_widget(self.gui_manager)

            return self.rootWidget

        def go_to_github(self, calling_button:Button) -> None:

            """
            On click go to latest Network Visualizer github repositiory
            """

            self.goto_github_button.text = (
                "https://github.com/TinkeringEngr/Network-Visualizer"
            )
            webbrowser.open(
                "https://github.com/TinkeringEngr/Network-Visualizer",
                new=2,
                autoraise=True,
            )

        def on_keyboard_closed(self) -> None:

            """
            Keyboard cleanup
            """

            self.keyboard.unbind(on_key_down=self.on_keyboard_down)
            self.keyboard = None


        

        def on_keyboard_down(
            self,
            keyboard: kivy.core.window.Keyboard,
            keycode: tuple[int, str],
            text: str,
            modifiers: kivy.properties.ObservableList,
        ) -> None:

            """
            Keyboard input handler
            """

            if keycode[1] == "r":  # reload code changes with hotkey 'r'

                try:
                    print("Reloading code dynamically!")
                    self.rootWidget.remove_widget(self.gui_manager)
                    self.gui_manager.close()  # run closing code before continuing

                    reload(gui_manager)  # Update code dynamically
                    from gui_manager import GUI_Manager

                    self.gui_manager = GUI_Manager(
                        kivy_application=self,
                        resource_path=self.resource_path,
                        switch_sniffer_info=None,
                    )  # restart GUI
                    self.rootWidget.add_widget(self.gui_manager)

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print("Reload failed! Code is broken..")

            #animation code for video
            elif keycode[1] == 'c':

                for animation in self.scheduled_animations:
                    Clock.unschedule(animation)

            elif keycode[1] == 'd':

                scheduled_function = lambda delta_time : self.animate_widget(0.1, 'd')

                self.scheduled_animations.append(scheduled_function)
                Clock.schedule_interval(scheduled_function, 1/60)

            elif keycode[1] == 'e':
            
                scheduled_function = lambda delta_time : self.animate_widget(0.2, 'e')

                self.scheduled_animations.append(scheduled_function)
                Clock.schedule_interval(scheduled_function, 1/60)

            elif keycode[1] == 'f':

                scheduled_function = lambda delta_time : self.animate_widget(0.2, 'f')

                self.scheduled_animations.append(scheduled_function)
                Clock.schedule_interval(scheduled_function, 1/60)
               

        def on_start(self) -> None:

            """
            Called on application start
            """

            self.version = "Beta"
            response = get(
                "https://api.github.com/repos/TinkeringEngr/Network-Visualizer/releases/latest"
            )

            self.latest_release = response.json()["name"]

            if self.version != self.latest_release:
                self.open_update_popup()

        def on_stop(self) -> None:

            """
            Called on application close
            """

            self.gui_manager.close()

        def open_update_popup(self) -> None:

            """
            Popup to inform user to update to latest version
            """

            # Create Widgets

            grid_layout = GridLayout(cols=1)

            self.popup = Popup(
                title="",
                content=grid_layout,
                size_hint=(None, None),
                size=(sp(700), sp(150)),
                auto_dismiss=True,
            )

            text_description = Label(halign="center", valign="middle", markup=True)
            text_description.text = f"This version of Network Visualizer ([b][color=FF0000]{self.version}[/color][/b]) is out of date.\n Please update to version [b][color=00FF00]{self.latest_release}[/color][/b] for the latest improvements. \nEventually, Network Visualizer will have an auto-update option.\n[color=19a8ffff]This program uses administrator privileges -- please use the trusted offical version.[/color]"

            self.goto_github_button = Button(
                text="Get latest version", on_press=self.go_to_github, size_hint_y=0.5
            )

            # Layout Widgets

            grid_layout.add_widget(Label(size_hint_y=0.5))
            grid_layout.add_widget(text_description)
            grid_layout.add_widget(Label(size_hint_y=0.5))
            grid_layout.add_widget(self.goto_github_button)
            self.popup.open()

        def switch_sniffer(self, sniffer_info: tuple) -> None:

            """
            Callable to reset or change network connection
            """

            self.rootWidget.remove_widget(self.gui_manager)
            self.gui_manager.close()  # run closing code before continuing

            reload(gui_manager)  # Update code dynamically
            from gui_manager import GUI_Manager

            self.gui_manager = GUI_Manager(
                kivy_application=self,
                resource_path=self.resource_path,
                switch_sniffer_info=sniffer_info,
            )  # restart GUI with sniffer connection information (ip, port)
            self.rootWidget.add_widget(self.gui_manager)

    Network_Visualizer = Application().run()  # Start Kivy Application
