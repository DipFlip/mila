import asyncio
import tkinter as tk
import numpy as np
import time
class LEDController:
    def __init__(self, led=None, is_virtual=False, pulse_frequency=2):
        self.led = led
        self.is_virtual = is_virtual
        self.current_goal_color = None
        self.current_color = (0, 0, 0)
        self.phase = 0
        self.pulse_frequency = pulse_frequency
        self.update_task = None
        if self.is_virtual:
            self.root = tk.Tk()
            self.root.title("Virtual LED")
            self.canvas = tk.Canvas(self.root, width=200, height=200)
            self.canvas.pack()
            self.virtual_led = self.canvas.create_oval(50, 50, 150, 150, fill="white")
            self.emotion_label = tk.Label(self.root, text="", font=("Helvetica", 14))
            self.emotion_label.pack()

    def start_update_task(self):
        if self.update_task is None or self.update_task.done():
            self.update_task = asyncio.create_task(self.update_led())

    async def update_led(self, steps=20, delay=0.05):
        pulse_period = 1 / self.pulse_frequency
        while True:
            if self.current_goal_color is not None:

                for step in range(steps):
                    self.phase = (self.phase + delay) % pulse_period
                    pulse_intensity = (1 + np.sin(2 * np.pi * self.pulse_frequency * self.phase)) / 2
                    if self.current_goal_color != self.current_goal_color:
                        break  # If goal color changed, restart the loop
                    new_color = self.interpolate_color(self.current_color, self.current_goal_color, step, steps)
                    modulated_color = [int(c * pulse_intensity) for c in new_color]
                    if self.is_virtual:
                        last_3_current_ms_time = str(time.time() % 1)[-3:]
                        self.emotion_label.config(text=f"{self.current_emotion_name} {last_3_current_ms_time}")
                        self.canvas.itemconfig(self.virtual_led, fill=self.rgb_to_hex(modulated_color))
                        self.root.update()
                    else:
                        normalized_color = [c / 255 for c in modulated_color]
                        self.led.color = normalized_color
                    self.current_color = modulated_color
                    print(f"Goal color: {self.current_goal_color}")
                    await asyncio.sleep(delay)
            await asyncio.sleep(delay)  # Always continue the loop

    def set_goal_color(self, color, emotion_name=""):
        self.current_color = self.current_goal_color
        self.current_goal_color = color
        self.current_emotion_name = emotion_name
        if self.update_task is None or self.update_task.done():
            self.update_task = asyncio.create_task(self.update_led())

    @staticmethod
    def interpolate_color(start_color, end_color, step, total_steps):
        delta = [(ec - sc) / total_steps for sc, ec in zip(start_color, end_color)]
        return [sc + delta[i] * step for i, sc in enumerate(start_color)]

    @staticmethod
    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
