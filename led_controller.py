import asyncio
import tkinter as tk
import numpy as np
import time

class LEDController:
    def __init__(self, led=None, is_virtual=False, pulse_frequency=2):
        self.led = led
        self.is_virtual = is_virtual
        
        # Attributes for color state and transitions
        self.current_unmodulated_color = [0.0, 0.0, 0.0]  # Base color for pulsing, uses floats
        self.active_goal_color = None                     # Target color for current transition
        self.transition_start_color = [0.0, 0.0, 0.0]     # Color at the beginning of a transition
        self.transition_step = 0                          # Current step in an ongoing transition
        self.total_transition_steps = 15                  # Target steps for a full transition (~0.5s at 30fps)
        
        self.current_emotion_name = "Initializing..."     # Name of the dominant emotion

        self.phase = 0.0                                  # Current phase for the pulsing effect (0 to 1)
        self.pulse_frequency = float(pulse_frequency)
        self.frame_delay = 1.0 / 30.0                     # Target frame delay for ~30 FPS

        self.update_task = None
        self.emotion_bars_canvas_items = [] # To keep track of drawn bar items

        # Blinking state
        self.is_blinking = False
        self.blink_color_one = None
        self.blink_color_two = None
        self.blink_emotion_name_one = ""
        self.blink_emotion_name_two = ""
        self.blink_interval = 0.75  # seconds
        self.last_blink_switch_time = 0
        self.current_blink_is_one = True # True if currently targeting blink_color_one

        if self.is_virtual:
            self.root = tk.Tk()
            self.root.title("Emotion Visualizer")
            
            # Main LED canvas
            self.led_canvas_height = 200
            self.led_canvas = tk.Canvas(self.root, width=200, height=self.led_canvas_height)
            self.led_canvas.pack()
            self.virtual_led = self.led_canvas.create_oval(50, 50, 150, 150, fill=self.rgb_to_hex(self.current_unmodulated_color))
            self.emotion_label = tk.Label(self.root, text=self.current_emotion_name, font=("Helvetica", 14))
            self.emotion_label.pack(pady=5)

            # Emotion bars canvas
            self.bars_canvas_height = 330 # Increased height for better padding
            self.bars_canvas_width = 350 
            self.bars_canvas = tk.Canvas(self.root, width=self.bars_canvas_width, height=self.bars_canvas_height, bg="lightgray")
            self.bars_canvas.pack(pady=10)
            
            # Adjusted window geometry
            new_total_height = self.led_canvas_height + self.bars_canvas_height + self.emotion_label.winfo_reqheight() + 40 # Added padding
            self.root.geometry(f"{self.bars_canvas_width}x{new_total_height}")

    def start_update_task(self):
        if self.update_task is None or self.update_task.done():
            self.update_task = asyncio.create_task(self.update_led_loop())

    async def update_led_loop(self):
        """Main animation loop for the LED and UI updates."""
        pulse_period = 1.0 / self.pulse_frequency if self.pulse_frequency > 0 else float('inf')

        while True:
            loop_start_time = time.monotonic()

            # --- Blinking Logic ---
            if self.is_blinking:
                if (loop_start_time - self.last_blink_switch_time) >= self.blink_interval:
                    self.current_blink_is_one = not self.current_blink_is_one
                    if self.current_blink_is_one:
                        self.active_goal_color = list(map(float, self.blink_color_one))
                        self.current_emotion_name = self.blink_emotion_name_one
                    else:
                        self.active_goal_color = list(map(float, self.blink_color_two))
                        self.current_emotion_name = self.blink_emotion_name_two
                    
                    self.transition_start_color = list(self.current_unmodulated_color)
                    self.transition_step = 0
                    self.last_blink_switch_time = loop_start_time
            
            # --- Color Transition Logic ---
            if self.active_goal_color is not None:
                if self.transition_step < self.total_transition_steps:
                    self.transition_step += 1
                    interpolated_color = self.interpolate_color(
                        self.transition_start_color,
                        self.active_goal_color,
                        self.transition_step,
                        self.total_transition_steps
                    )
                    self.current_unmodulated_color = [max(0.0, min(255.0, c)) for c in interpolated_color]
                else: # Transition complete
                    self.current_unmodulated_color = list(self.active_goal_color)
            # If no active_goal_color, current_unmodulated_color just stays as is (e.g. initial black)

            # --- Pulsing Logic ---
            if pulse_period != float('inf'):
                self.phase = (self.phase + self.frame_delay / pulse_period) % 1.0
            else: # No pulsing if frequency is zero
                self.phase = 0.0 
            
            # Sin wave from 0 to 1, then scaled to desired intensity range (e.g., 0.5 to 1.0 for pulsing, not dimming to black)
            # Let's make it pulse between 70% and 100% intensity
            min_pulse_intensity = 0.7 
            pulse_amplitude = (1.0 - min_pulse_intensity) / 2.0
            pulse_intensity = min_pulse_intensity + pulse_amplitude * (1 + np.sin(2 * np.pi * self.phase))


            modulated_color = [max(0, min(255, int(c * pulse_intensity))) for c in self.current_unmodulated_color]

            # --- UI Update ---
            if self.is_virtual:
                self.led_canvas.itemconfig(self.virtual_led, fill=self.rgb_to_hex(modulated_color))
                
                label_text = self.current_emotion_name
                if self.is_blinking:
                    if self.current_blink_is_one:
                        other_emotion_name = self.blink_emotion_name_two
                    else:
                        other_emotion_name = self.blink_emotion_name_one
                    label_text = f"Blinking: {self.current_emotion_name} & {other_emotion_name}"
                    if self.transition_step < self.total_transition_steps:
                         label_text += f" ({(self.transition_step/self.total_transition_steps)*100:.0f}%)"

                elif self.active_goal_color is not None:
                    if self.transition_step < self.total_transition_steps:
                        label_text = f"{self.current_emotion_name} ({(self.transition_step/self.total_transition_steps)*100:.0f}%)"
                else:
                     label_text = "Idle"
                self.emotion_label.config(text=label_text)
                
                # It's crucial to update Tkinter's event loop
                self.root.update_idletasks() # Process pending operations like layout changes
                self.root.update()          # Process all other events and redraw

            # --- Physical LED Update ---
            if not self.is_virtual and self.led is not None:
                # Convert 0-255 to 0-1 for gpiozero
                scaled_color = tuple(max(0, min(1, c / 255.0)) for c in modulated_color)
                self.led.color = scaled_color

            # --- Frame Delay Management ---
            elapsed_loop_time = time.monotonic() - loop_start_time
            sleep_duration = self.frame_delay - elapsed_loop_time
            
            if sleep_duration > 0:
                await asyncio.sleep(sleep_duration)
            else:
                # If the loop took too long, yield control briefly to prevent freezing
                await asyncio.sleep(0) 

    def set_goal_color(self, color, emotion_name=""):
        # Ensure color is a list of floats
        target_color_float = list(map(float, color))

        # Disable blinking if a specific goal color is set
        if self.is_blinking:
            self.is_blinking = False
            # print("Blinking disabled due to new goal color.")

        # Check if the goal is truly new to avoid restarting transition unnecessarily
        if self.active_goal_color == target_color_float and self.current_emotion_name == emotion_name:
            # If we are already at the goal and name is same, ensure transition is marked complete
            if self.transition_step >= self.total_transition_steps:
                 self.current_unmodulated_color = list(target_color_float) # Snap to final color
            # print(f"Goal {emotion_name} {target_color_float} is already active or settled.")
            return

        print(f"New Goal: {emotion_name} ({target_color_float}). From: {self.current_unmodulated_color}")
        
        self.transition_start_color = list(self.current_unmodulated_color) # Start from current state
        self.active_goal_color = target_color_float
        self.current_emotion_name = emotion_name
        self.transition_step = 0 # Reset transition
        
        self.start_update_task() # Ensure the animation loop is running

    def set_blinking_colors(self, color_one, color_two, emotion_name_one="", emotion_name_two="", interval=0.75):
        if not self.is_blinking or \
           self.blink_color_one != list(map(float, color_one)) or \
           self.blink_color_two != list(map(float, color_two)) or \
           self.blink_interval != interval:
            
            print(f"Setting blinking between {emotion_name_one} {color_one} and {emotion_name_two} {color_two}")
            self.is_blinking = True
            self.blink_color_one = list(map(float, color_one))
            self.blink_color_two = list(map(float, color_two))
            self.blink_emotion_name_one = emotion_name_one
            self.blink_emotion_name_two = emotion_name_two
            self.blink_interval = interval
            
            # Initialize the first blink target
            self.current_blink_is_one = True
            self.active_goal_color = list(self.blink_color_one)
            self.current_emotion_name = self.blink_emotion_name_one
            self.transition_start_color = list(self.current_unmodulated_color)
            self.transition_step = 0
            self.last_blink_switch_time = time.monotonic() # Start interval timer

            self.start_update_task() # Ensure the animation loop is running
        # else:
            # print("Blinking parameters are already set.")

    def update_emotion_bars(self, emotion_data):
        if not self.is_virtual or not hasattr(self, 'bars_canvas'):
            return

        for item_id in self.emotion_bars_canvas_items:
            self.bars_canvas.delete(item_id)
        self.emotion_bars_canvas_items.clear()

        bar_max_width = self.bars_canvas_width - 40 
        bar_height = 20
        spacing_y = 55  # Increased vertical spacing
        start_y = 20    
        text_y_offset_from_bar = 8 # Increased gap between bar and text

        for i, (name, score, color_tuple) in enumerate(emotion_data):
            bar_width = score * bar_max_width
            x0 = 20 
            y0 = start_y + i * spacing_y
            x1 = x0 + bar_width
            y1 = y0 + bar_height

            try:
                bar_color_hex = self.rgb_to_hex(tuple(map(int, color_tuple)))
            except (ValueError, TypeError):
                bar_color_hex = "#808080" 

            rect_id = self.bars_canvas.create_rectangle(x0, y0, x1, y1, fill=bar_color_hex, outline="black")
            # Place text below the bar with increased offset
            text_id = self.bars_canvas.create_text(x0, y1 + text_y_offset_from_bar, anchor=tk.NW, text=f"{name}: {score:.3f}", font=("Helvetica", 10))
            
            self.emotion_bars_canvas_items.append(rect_id)
            self.emotion_bars_canvas_items.append(text_id)
        
        # No self.root.update() here; the main loop handles it.

    @staticmethod
    def interpolate_color(start_color, end_color, step, total_steps):
        # Ensure inputs are float lists
        sc = [float(c) for c in start_color]
        ec = [float(c) for c in end_color]

        if total_steps == 0:
            return list(ec) # Return end_color immediately if no steps
            
        # Calculate normalized progress (0.0 to 1.0)
        progress = 0.0
        if total_steps > 0 : # Avoid division by zero if step is 0 and total_steps is 0
             progress = float(step) / float(total_steps)
        progress = max(0.0, min(1.0, progress)) # Clamp progress

        # Linear interpolation: start + (end - start) * progress
        interpolated = [
            sc[i] + (ec[i] - sc[i]) * progress for i in range(len(sc))
        ]
        return interpolated # Returns list of floats, clamping done by caller

    @staticmethod
    def rgb_to_hex(rgb):
        try:
            r, g, b = map(int, rgb) # Ensure components are integers for hex formatting
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            return "#{:02x}{:02x}{:02x}".format(r, g, b)
        except (ValueError, TypeError) as e:
            # print(f"Error converting RGB to hex: {rgb}, Error: {e}")
            return "#000000" # Default to black if input is problematic
