import asyncio

class LEDController:
    def __init__(self, led, is_virtual=False, virtual_led=None):
        self.led = led
        self.is_virtual = is_virtual
        self.virtual_led = virtual_led

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
