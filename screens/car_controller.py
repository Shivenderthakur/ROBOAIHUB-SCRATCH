# screens/car_controller.py

import threading
import cv2
from kivy.uix.screenmanager import Screen
from bt_ports import list_serial_ports as list_outgoing_bt_ports
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ListProperty, DictProperty, NumericProperty, BooleanProperty
from kivy.uix.behaviors import DragBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
import serial
import time

# Global serial connection variable
serial_conn = None
bt_connected = False
class carUI:
    def UI():
        return """# kv/car_controller.kv

<Block>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000
    size_hint: None, None
    size: 160, 90
    font_size: 20
    color: 1, 1, 1, 1
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: (0, 0, 0, 0.1)
        Rectangle:
            pos: self.x + 2, self.y - 2
            size: self.size
    on_press: self.animate_press()
    on_release: self.animate_release()

<BlockWithIcon>:
    drag_rectangle: self.x, self.y, self.width, self.height
    drag_distance: 0
    drag_timeout: 1000000
    size_hint: None, None
    size: 160, 100
    icon: ''
    label: ''
    bg_color: 0.5, 0.5, 0.5, 1
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]

    # Since this is a FloatLayout, positions must be explicit
    Image:
        source: root.icon
        size_hint: None, None
        size: 48, 48
        pos_hint: {'center_x': 0.5}
        y: root.y + root.height - 60

    Label:
        text: root.label
        font_size: 16
        bold: True
        color: 1, 1, 1, 1
        size_hint: None, None
        size: self.texture_size
        pos_hint: {'center_x': 0.5}
        y: root.y + 10

<ConfigScreen>:
    name: 'config'
    canvas.before:
        Color:
            rgba: (0.98, 0.95, 0.85, 1)
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20

        Label:
            text: 'Scratch Visual Learning'
            font_name: 'ComicRelief-Bold'
            font_size: 36
            color: (0.2, 0.5, 0.7, 1)
            bold: True
            size_hint_y: None
            height: 80

        Image:
            source: 'assets/images/logo.jfif'
            allow_stretch: False
            keep_ratio: True
            size_hint_y: None
            height: 100
            pos_hint: {'center_x': 0.5}

        BoxLayout:
            orientation: 'horizontal'
            spacing: 15
            size_hint_y: None
            height: 60

            Button:
                id: bt_btn
                text: 'BLUETOOTH: DISCONNECTED'
                size_hint_x: 0.5
                font_size: 16
                bold: True
                background_color: (0.9, 0.3, 0.3, 1)  # Red when disconnected
                on_release: root.toggle_bluetooth()

            Button:
                text: 'Start Magic!'
                size_hint_x: 0.5
                font_size: 18
                background_normal: ''
                background_color: (0.3, 0.7, 0.3, 1)
                color: (1, 1, 1, 1)
                on_release: root.start_tracking()

        FloatLayout:
            Label:
                text: 'Drag the colorful blocks onto arrows'
                font_size: 20
                pos_hint: {'center_x': 0.5, 'top': 1}
                color: (0.3, 0.3, 0.3, 1)

            # Drop targets
            Button:
                id: tgt_up
                text: root.display['up']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.5, 'center_y': 0.8}
                background_normal: ''
                background_color: (1, 0.9, 0.7, 1)
                color: (0.1, 0.1, 0.1, 1)

            Button:
                id: tgt_down
                text: root.display['down']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.5, 'center_y': 0.2}
                background_normal: ''
                background_color: (1, 0.7, 0.9, 1)
                color: (0.1, 0.1, 0.1, 1)

            Button:
                id: tgt_left
                text: root.display['left']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.2, 'center_y': 0.5}
                background_normal: ''
                background_color: (0.7, 0.9, 1, 1)
                color: (0.1, 0.1, 0.1, 1)

            Button:
                id: tgt_right
                text: root.display['right']
                size_hint: None, None
                size: 160, 160
                pos_hint: {'center_x': 0.8, 'center_y': 0.5}
                background_normal: ''
                background_color: (0.9, 1, 0.7, 1)
                color: (0.1, 0.1, 0.1, 1)

            # Draggable blocks
            BlockWithIcon:
                id: block_forward
                icon: 'assets/icons/forw.png'
                label: 'Forward'
                pos: 20, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_backward
                icon: 'assets/icons/back.png'
                label: 'Back'
                pos: 180, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_left
                icon: 'assets/icons/left.png'
                label: 'Left'
                pos: 340, 20
                bg_color: (0.627,0.839,1,1)

            BlockWithIcon:
                id: block_right
                icon: 'assets/icons/right.png'
                label: 'Right'
                pos: 500, 20
                bg_color: (0.627,0.839,1,1)

        Button:
            text: '◀ Back'
            size_hint: None, None
            size: 110, 44
            pos_hint: {'x': 0.02, 'top': 0.98}
            background_normal: ''
            background_color: (0.2, 0.6, 1, 1)
            color: (1, 1, 1, 1)
            font_size: 18
            on_release: app.root.current = 'home'

<TrackScreen>:
    name: 'track'
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 20

        Label:
            id: motion_label
            text: 'Movement: NONE'
            font_size: 24
            color: (0.1, 0.3, 0.6, 1)
            size_hint_y: None
            height: 60

        Label:
            id: command_label
            text: 'Command: NONE'
            font_size: 20
            color: (0.6, 0.2, 0.2, 1)
            size_hint_y: None
            height: 50

        Button:
            text: 'Stop & Back'
            font_size: 18
            background_normal: ''
            background_color: (1, 0.5, 0.5, 1)
            color: (1, 1, 1, 1)
            size_hint_y: None
            height: 60
            on_release: root.stop_tracking()"""
# Bluetooth connection functions
def connect_bluetooth(port_name):
    """Connect to Bluetooth device"""
    global serial_conn, bt_connected
    try:
        # Close existing connection
        if serial_conn and serial_conn.is_open:
            serial_conn.close()
        
        # Open new connection
        print(f"Connecting to {port_name}...")
        serial_conn = serial.Serial(port_name, baudrate=9600, timeout=2)
        time.sleep(2)  # Wait for Arduino reset
        
        # Clear buffers
        serial_conn.reset_input_buffer()
        serial_conn.reset_output_buffer()
        
        # Test connection
        serial_conn.write(b"test;\n")
        serial_conn.flush()
        print("Connection test sent")
        
        bt_connected = True
        print("Connected successfully!")
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        bt_connected = False
        return False

def disconnect_bluetooth():
    """Disconnect Bluetooth device"""
    global serial_conn, bt_connected
    try:
        if serial_conn and serial_conn.is_open:
            # Close connection
            serial_conn.close()
            print("Disconnected")
    except Exception as e:
        print(f"Error disconnecting: {str(e)}")
    
    serial_conn = None
    bt_connected = False

def send_command(command):
    """Send a command through Bluetooth"""
    global serial_conn, bt_connected
    
    if not command.endswith('\n'):
        command += '\n'
    
    if not bt_connected or not serial_conn or not serial_conn.is_open:
        print(f"Cannot send '{command.strip()}': Not connected")
        return False
    
    try:
        # Send command
        serial_conn.write(command.encode())
        serial_conn.flush()
        print(f"Sent: {command.strip()}")
        return True
    except Exception as e:
        print(f"Send failed: {str(e)}")
        # Reset connection status
        bt_connected = False
        return False

# Bluetooth Popup implementation
class BluetoothPopup(Popup):
    ports = ListProperty([])
    selected_port = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Schedule the port listing to happen after the popup is fully initialized
        Clock.schedule_once(self._finish_init)
    
    def _finish_init(self, dt):
        self.ports = list_outgoing_bt_ports()
        if self.ports:
            # Set the spinner values to the port descriptions
            self.ids.port_spinner.values = [desc for port, desc in self.ports]
            self.ids.port_spinner.text = self.ids.port_spinner.values[0] if self.ids.port_spinner.values else 'No devices found'
            self.selected_port = self.ports[0][0] if self.ports else ""  # Set to first port
        else:
            self.ids.port_spinner.text = 'No devices found'
            self.ids.port_spinner.disabled = True
            self.ids.connect_btn.disabled = True
    
    def on_text(self, instance, value):
        """Handle port selection from spinner"""
        for port, desc in self.ports:
            if desc == value:
                self.selected_port = port
                break
    
    def connect(self):
        if connect_bluetooth(self.selected_port):
            app = App.get_running_app()
            app.bt_connected = bt_connected
            self.dismiss()
        else:
            self.ids.status_label.text = "Connection failed!"
            self.ids.status_label.color = (1, 0, 0, 1)

class BlockWithIcon(DragBehavior, FloatLayout):
    icon = StringProperty('')
    label = StringProperty('')
    bg_color = ListProperty([0.5, 0.5, 0.5, 1])

class Block(Button):
    bg_color = ListProperty([0.5, 0.5, 0.5, 1])

    def animate_press(self):
        self.bg_color = [0.4, 0.4, 0.4, 1]

    def animate_release(self):
        self.bg_color = [0.5, 0.5, 0.5, 1]

class ConfigScreen(Screen):
    display = DictProperty({
        'up': 'None',
        'down': 'None',
        'left': 'None',
        'right': 'None'
    })
    current_gear = NumericProperty(0)
    bt_connected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.last_hand_pos = None
        Clock.schedule_interval(self.check_block_overlaps, 0.1)

    def check_block_overlaps(self, dt):
        blocks = {
            'Forward': self.ids.block_forward,
            'Back': self.ids.block_backward,
            'Left': self.ids.block_left,
            'Right': self.ids.block_right
        }
        targets = {
            'up': self.ids.tgt_up,
            'down': self.ids.tgt_down,
            'left': self.ids.tgt_left,
            'right': self.ids.tgt_right
        }

        for key in self.display:
            self.display[key] = 'None'

        for cmd, block in blocks.items():
            for direction, target in targets.items():
                if self._is_overlapping(block, target):
                    self.display[direction] = cmd

    def _is_overlapping(self, w1, w2):
        x1, y1 = w1.pos
        w1_right = x1 + w1.width
        w1_top = y1 + w1.height

        x2, y2 = w2.pos
        w2_right = x2 + w2.width
        w2_top = y2 + w2.height

        return not (w1_right < x2 or x1 > w2_right or w1_top < y2 or y1 > w2_top)

    def on_pre_enter(self):
        self.update_bt_button()

    def update_bt_button(self):
        """Update Bluetooth button appearance"""
        if bt_connected:
            self.ids.bt_btn.text = "BLUETOOTH: CONNECTED"
            self.ids.bt_btn.background_color = (0.4, 0.85, 0.4, 1)  # Green
        else:
            self.ids.bt_btn.text = "BLUETOOTH: DISCONNECTED"
            self.ids.bt_btn.background_color = (0.9, 0.3, 0.3, 1)  # Red

    def show_bluetooth_popup(self):
        """Show Bluetooth selection popup"""
        popup = BluetoothPopup()
        popup.open()

    def toggle_bluetooth(self):
        """Toggle Bluetooth connection"""
        global bt_connected
        if bt_connected:
            disconnect_bluetooth()
            app = App.get_running_app()
            app.bt_connected = False
        else:
            self.show_bluetooth_popup()
        self.update_bt_button()

    def start_tracking(self):
        if not bt_connected:
            self.show_bluetooth_popup()
            return
            
        app = App.get_running_app()
        self.manager.current = 'track'
        app.tracking_active = True
        app.tracking_thread = threading.Thread(target=self.track_hand)
        app.tracking_thread.start()

    def track_hand(self):
        app = App.get_running_app()
        cap = cv2.VideoCapture(0)
        
        # Import mediapipe here to avoid early import
        from mediapipe.python.solutions.hands import Hands
        from mediapipe.python.solutions.drawing_utils import draw_landmarks
        
        mp_hands = Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.5)

        while app.tracking_active:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = mp_hands.process(rgb)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    draw_landmarks(frame, hand_landmarks)

                    # --- Gear Selection ---
                    finger_count = self.count_fingers_up(hand_landmarks.landmark)
                    gear = self.map_fingers_to_gear(finger_count)

                    # --- Movement Detection ---
                    cx = int(hand_landmarks.landmark[9].x * w)
                    cy = int(hand_landmarks.landmark[9].y * h)

                    direction = self.detect_direction(cx, cy, w, h)
                    command = self.display.get(direction, 'None')

                    if direction and command and gear != "stop":
                        full_command = f"robocar,{gear}_{command};"
                        
                        # Send command directly instead of scheduling
                        send_command(full_command)
                        
                        cv2.putText(frame, f"Gear: {gear} | Dir: {direction} | Sent: {command}", (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        # Send stop command when no movement detected
                        send_command("robocar,stop;")

            else:
                # Send stop command when no hand detected
                send_command("robocar,stop;")

            cv2.imshow("Tracking", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        mp_hands.close()

    def map_fingers_to_gear(self, count):
        return {
            1: "gear1",
            2: "gear2",
            3: "gear3",
            4: "gear4"
        }.get(count, "stop")

    def detect_direction(self, cx, cy, w, h):
        margin = 100  # pixels from edges
        if cy < margin:
            return 'up'
        elif cy > h - margin:
            return 'down'
        elif cx < margin:
            return 'left'
        elif cx > w - margin:
            return 'right'
        else:
            return None
            
    def count_fingers_up(self, landmarks):
        tips = [8, 12, 16, 20]  # Index to Pinky
        return sum(landmarks[tip].y < landmarks[tip - 2].y for tip in tips)

class TrackScreen(Screen):
    def stop_tracking(self):
        app = App.get_running_app()
        app.tracking_active = False
        # Send stop command when tracking stops
        send_command("robocar,stop;")
        self.manager.current = 'car'