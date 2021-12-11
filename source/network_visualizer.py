# Jonathan Valiente.  All rights reserved. 2022

# My intention is to freely distribute the source code of Network Visualizer to planet earth as public infrastructure. (Aliens must pay)
# Additionally, I intend to lead the community organization that is the sole distributor with the goals of incentivizing its development, improving its quality, and furthering its utility.
# I stand on the shoulders of giants and desire to make contributions for the betterment of humanity.

#Additional Authors:
#comments
#2nd try


if __name__ == "__main__": #start like this to prevent a bug on microsoft OS (Something to do with multiple windows + kivy/multiprocessing)


    import sys
    import os ; os.environ["KIVY_NO_CONSOLELOG"] = "1"
    from importlib import reload

    import kivy
    from kivy.config import Config
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.widget import Widget
    from kivy.core.window import Window
    

    #make "fullscreen" without calling Window.fullscreen = True (creates resolution BUG)
    Window.size = (Window.size[0]-160, Window.size[1]) #Why does kivy miscalculate 160pixels for window x-axis (Kivy Window.size[0])?
    Window.left = 0
  
    import gui_manager
    from gui_manager import GUI_Manager # Root program class. No restart required to update code dynamically (hotkey: r)
    
  


    class Application(App):

        """
        Kivy Application base class.
        """ 

        def build(self) -> Widget:

            """
            Kivy application constructor.
            """


            super().__init__()

            self.title  = "Network Visualizer"
            self.icon = '../assets/images/UI/Network_Visualizer.png'
            
           
            
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self.root)
            self._keyboard.bind(on_key_down=self._on_keyboard_down)
            Window.bind(on_resize = self.window_resize) #useful for setting GUI widget sizes on resize

            self.rootWidget  = BoxLayout() #placeholder widget
            self.gui_manager = GUI_Manager(kivy_application = self) #Program logic found here
            self.rootWidget.add_widget(self.gui_manager)

            return self.rootWidget 


            
        def _on_keyboard_down(self, keyboard: kivy.core.window.Keyboard, keycode: tuple[int, str], text: str, modifiers: kivy.properties.ObservableList) -> None:
            
            """
            Keyboard input handler.
            """

            if keycode[1] == 'r': #reload code changes with hotkey 'r'
                
                try:
                    print("Reloading code dynamically!")
                    self.rootWidget.remove_widget(self.gui_manager)
                    self.gui_manager.close() #run closing code before continuing

                    reload(gui_manager) #Update code dynamically
                    from gui_manager import GUI_Manager

                    self.gui_manager = GUI_Manager(kivy_application = self) #restart GUI
                    self.rootWidget.add_widget(self.gui_manager)

                except Exception as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    print("Reload failed! Code is broken..")
            


        def window_resize(self, window: kivy.core.window.window_sdl2.WindowSDL, x_dimension: int, y_dimension: int) -> None: 
            
            """
            Called when program window is resized. GUI dimensions are calculated from window size. 
            """


            try:
                self.rootWidget.remove_widget(self.gui_manager)
                self.gui_manager.clear_live_database() #run closing code before continuing

                reload(gui_manager) #Update code dynamically

                from gui_manager import GUI_Manager

                self.gui_manager = GUI_Manager(kivy_application = self) #restart GUI
                self.rootWidget.add_widget(self.gui_manager)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                print("Reload failed! Code is broken..")



        def _keyboard_closed(self) -> None:
    
            """
            Keyboard cleanup function.
            """

            self._keyboard.unbind(on_key_down=self._on_keyboard_down)
            self._keyboard = None



        def on_stop(self) -> None:

            """
            Clean up application on close. 
            """
            
            try: 
                self.gui_manager.close()
            except:
                pass


    Network_Visualizer = Application().run() #Start Kivy Application