import asyncio
import tkinter as tk

class LEDController:
    def __init__(self, led, is_virtual=False):
        self.led = led
        self.is_virtual = is_virtual
        if self.is_virtual:
            self.root = tk.Tk()
            self.root.title("Virtual LED")
            self.canvas = tk.Canvas(self.root, width=200, height=200)
            self.canvas.pack()
            self.virtual_led = self.canvas.create_oval(50, 50, 150, 150, fill="white")
            self.emotion_label = tk.Label(self.root, text="", font=("Helvetica", 14))
            self.emotion_label.pack()
            self.loop = asyncio.get_event_loop()
            self.root.after(100, self.run_asyncio_tasks)
            self.root.mainloop()

    def run_asyncio_tasks(self):
        try:
            self.loop.call_soon(asyncio.ensure_future, self.main())
            self.loop.run_forever()
        except RuntimeError as e:
            print("Asyncio loop stopped: ", e)

    async def update_led(self, target_color, steps=50, delay=0.1):
        if self.is_virtual:
            current_color = self.led.itemcget(self.led.virtual_led, "fill")
            current_color = self.led.winfo_rgb(current_color)  # Get RGB values of current color
            current_color = (current_color[0] // 256, current_color[1] // 256, current_color[2] // 256)
        else:
            current_color = self.led.color

        for step in range(steps):
            new_color = self.interpolate_color(current_color, target_color, step, steps)
            if self.is_virtual:
                self.led.itemconfig(self.led.virtual_led, fill=self.rgb_to_hex(new_color))
                self.led.update()
            else:
                self.led.color = new_color
            await asyncio.sleep(delay)

    @staticmethod
    def interpolate_color(start_color, end_color, step, total_steps):
        delta = [(ec - sc) / total_steps for sc, ec in zip(start_color, end_color)]
        return [sc + delta[i] * step for i, sc in enumerate(start_color)]

    @staticmethod
    def rgb_to_hex(rgb):
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
