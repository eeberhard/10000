from PIL import Image, ImageDraw, ImageFont
import numpy as np
import colorsys


class FrameDrawer:
    """
    FrameDrawer is a utility class for creating image frames using PIL.
    The main methods are to draw centered text and to draw circles
    (or other objects) on an evenly spaced grid.
    :param font: The path to a TrueType font file to use for text rendering.
    :param font_size: The font size.
    """
    def __init__(self, font="resources/Go-Mono-Bold.ttf", font_size=64):
        self.font = ImageFont.truetype(font, font_size)
        self._layer = None
        self._draw = None
        self._accents = []

    @staticmethod
    def generate_base(resolution=(1280, 720)):
        """
        Create a default base image.
        :param resolution: Tuple of image width and height in pixels (default 1280x720).
        :return: PIL Image.
        """
        return Image.new(mode='RGBA', size=resolution, color=(0, 0, 0, 255))

    @staticmethod
    def get_coordinate(index, width, height, cols=125, rows=82, padding=(4, 4)):
        """
        Get the X, Y pixel coordinate of a point based on its index and the desired grid spacing.
        :param index: The point index (0 indexed).
        :param width: Image width in pixels.
        :param height: Image height in pixels.
        :param cols: Horizontal grid size.
        :param rows: Vertical grid size.
        :param padding: Tuple of (columns, rows) spaces to add to left / right and top / bottom respectively.
        :return: Tuple of (x, y) pixel coordinate.
        """
        row = np.floor(index / cols)
        col = index % cols

        x = (col + padding[0] + 0.5) * (width / (cols + 2 * padding[0]))
        y = (row + padding[1] + 0.5) * (height / (rows + 2 * padding[1]))
        return x, y

    @staticmethod
    def remap_index(index):
        """
        Remapping function to distribute the 10000 points of 125x80 grid onto
        a 125x82 grid, wherein the center 25x10 points are skipped.
        :param index: The original point index.
        :return: Modified index.
        """
        skipstart = 36 * 125 + 50

        if index >= skipstart:
            skip = np.floor((index - skipstart) / 100) + 1
            if skip > 10:
                skip = 10
            index = index + skip * 25

        return index

    def add_accent_note(self, index, hue, value, fade_frames=60):
        """
        Specify an "accent note", which is a specially colored circle at a given index.
        The accent note gets appended to a private class list attribute.
        :param index: Positional index (0 - 9999).
        :param hue: The HSV hue of the accent (0 - 1).
        :param value: The HSV value (brightness) of the accent (0 - 1).
        :param fade_frames: The number of frames over which to linearly fade the transparency of the accent
        """
        r, g, b = colorsys.hsv_to_rgb(hue, 1, value)
        accent = {'index': index, 'r': round(r * 255), 'g': round(g * 255), 'b': round(b * 255),
                  'alpha': 255, 'fade': 255 / fade_frames, 'sides': 0}
        self._accents.append(accent)

    def draw_accents(self, base):
        """
        Render all the accent notes in the private class list attribute and advance their fade values.
        Remove any fully faded accents from the list.
        :param base: Base PIL Image to draw accents onto.
        :return: A new composite PIL Image (base + accents).
        """
        im = base.copy()
        for accent in self._accents:
            if accent['alpha'] <= 0:
                self._accents.remove(accent)
                continue

            fill = (accent['r'], accent['g'], accent['b'], round(accent['alpha']))
            if accent['sides'] <= 0:
                im = self.add_circle(im, accent['index'], radius=4, fill=fill)
            elif accent['sides'] == 1:
                im = self.add_line(im, accent['index'], length=2, fill=fill)
            elif accent['sides'] == 2:
                im = self.add_line(im, accent['index'], fill=fill)
            else:
                im = self.add_polygon(im, accent['index'], sides=accent['sides'], radius=4, fill=fill)
            accent['alpha'] = accent['alpha'] - accent['fade']

        return Image.alpha_composite(base, im)

    def make_layer(self, base):
        """
        Helper function to create a transparent drawing layer and ImageDraw object
        and store these as class attributes.
        :param base: PIL Image base, from which the size is used.
        """
        self._layer = Image.new("RGBA", base.size, (255, 255, 255, 0))
        self._draw = ImageDraw.Draw(self._layer)

    def add_centered_text(self, base, text, alpha=255):
        """
        Draw center-aligned text onto a given base image.
        Text size and font are defined by class attributes.
        :param base: Base PIL Image to draw text onto.
        :param text: String text to draw.
        :param alpha: Optional text opacity (0-255, default 255 opaque).
        :return: A new composite PIL Image (base + text).
        """
        self.make_layer(base)

        position = (round(base.width/2), round(base.height/2))
        self._draw.text(position, text, anchor="mm", font=self.font, fill=(255, 255, 255, alpha))

        return Image.alpha_composite(base, self._layer)

    def add_circle(self, base, index, radius=1, fill=(128, 128, 128, 255)):
        """
        Draw a circle at a specified grid index.
        Additional arguments specify circle size, color and opacity.
        :param base: Base PIL Image.
        :param index: Positional index (0 - 9999).
        :param radius: Pixel radius of circle.
        :param fill: 4-tuple of RGBA for circle.
        :return: A new composite PIL Image (base + circle).
        """
        self.make_layer(base)
        x, y = self.get_coordinate(self.remap_index(index), base.width, base.height)

        box = [x - radius, y - radius, x + radius, y + radius]
        self._draw.ellipse(box, fill=fill)

        return Image.alpha_composite(base, self._layer)

    def add_polygon(self, base, index, sides=3, radius=2, fill=(128, 128, 128, 255)):
        """
        Draw a polygon at a specified grid index.
        Additional arguments specify polygon side count, size, color and opacity.
        :param base: Base PIL Image.
        :param index: Positional index (0 - 9999).
        :param sides: Number of sides (minimum 3).
        :param radius: Pixel radius of exterior bounding circle of polygon.
        :param fill: 4-tuple of RGBA for polygon.
        :return: A new composite PIL Image (base + polygon).
        """
        self.make_layer(base)
        x, y = self.get_coordinate(self.remap_index(index), base.width, base.height)

        bounding_circle = (x, y, radius)
        self._draw.regular_polygon(bounding_circle, sides, fill=fill)

        return Image.alpha_composite(base, self._layer)

    def add_line(self, base, index, length=8, width=4, fill=(128, 128, 128, 255)):
        """
        Draw a (horizontal) line at a specified grid index.
        Additional arguments specify line length, width, color and opacity.
        :param base: Base PIL Image.
        :param index: Positional index (0 - 9999).
        :param length: Pixel length of line (horizontal).
        :param width: Pixel width (half-height) of line (vertical).
        :param fill: 4-tuple of RGBA for polygon.
        :return: A new composite PIL Image (base + line).
        """
        self.make_layer(base)
        x, y = self.get_coordinate(self.remap_index(index), base.width, base.height)

        xy = [x - length / 2, y, x + length / 2, y]
        self._draw.line(xy, width=width, fill=fill)

        return Image.alpha_composite(base, self._layer)


if __name__ == "__main__":
    draw = FrameDrawer()
    base = draw.generate_base()
    frame = draw.add_centered_text(base, "test")
    for val in np.random.randint(0, 10000, 100):
        rgba = np.random.randint(0, 255, 4)
        rad = np.random.randint(10)
        frame = draw.add_circle(frame, index=val, radius=rad, fill=tuple(rgba))

    frame.show()
