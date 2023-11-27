import asyncio
import tkinter as tk
import tkinter as tk

class LEDController:
    def __init__(self, led=None, is_virtual=False):
        self.led = led
        self.is_virtual = is_virtual
        self.current_goal_color = None
        self.update_task = None
        if self.is_virtual:
            self.root = tk.Tk()
            self.root.title("Virtual LED")
            self.canvas = tk.Canvas(self.root, width=200, height=200)
            self.canvas.pack()
            self.virtual_led = self.canvas.create_oval(50, 50, 150, 150, fill="white")
            self.emotion_label = tk.Label(self.root, text="", font=("Helvetica", 14))
            self.emotion_label.pack()

    async def update_led(self, steps=50, delay=0.1):
        while True:
            if self.current_goal_color is not None:
                if self.is_virtual:
                    self.emotion_label.config(text=self.current_emotion_name)
                    current_color = self.canvas.itemcget(self.virtual_led, "fill")
                    current_color = self.root.winfo_rgb(current_color)  # Get RGB values of current color
                    current_color = (current_color[0] // 256, current_color[1] // 256, current_color[2] // 256)
                else:
                    current_color = self.led.color

                for step in range(steps):
                    if self.current_goal_color != self.current_goal_color:
                        break  # If goal color changed, restart the loop
                    new_color = self.interpolate_color(current_color, self.current_goal_color, step, steps)
                    if self.is_virtual:
                        self.canvas.itemconfig(self.virtual_led, fill=self.rgb_to_hex(new_color))
                        self.root.update()
                    else:
                        self.led.color = new_color
                    await asyncio.sleep(delay)
                await asyncio.sleep(delay)  # Wait before checking for a new color
            else:
                await asyncio.sleep(0.1)  # No goal color set, wait before checking again

    def set_goal_color(self, color, emotion_name=""):
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
