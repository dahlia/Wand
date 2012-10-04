""":mod:`wand.drawing` --- Drawings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import ctypes
import numbers

from .color import Color
from .api import library, MagickPixelPacket
from .resource import Resource

TEXT_ALIGN_TYPES = ('undefined', 'left', 'center', 'right')
TEXT_DECORATION_TYPES = ('undefined', 'no', 'underline', 'overline',
                         'line_through')
TEXT_GRAVITY_TYPE = ('forget', 'north_west', 'north',
                     'north_east', 'west', 'center', 'east', 'south_west',
                     'south', 'south_east', 'static')

__all__ = "Drawing",

class Drawing(Resource):
    """Drawing"""

    c_is_resource = library.IsDrawingWand
    c_destroy_resource = library.DestroyDrawingWand
    c_get_exception = library.DrawGetException
    c_clear_exception = library.DrawClearException

    __slots__ = 'c_resource'

    def __init__(self, drawing_wand=None):
        with self.allocate():
            if not drawing_wand:
                self.drawing_wand = library.NewDrawingWand()
            else:
                self.drawing_wand = library.CloneDrawingWand(drawing_wand.drawing_wand)

    def clone(self):
        return type(self)(drawing_wand=self)

    @property
    def drawing_wand(self):
        return self.resource

    @drawing_wand.setter
    def drawing_wand(self, drawing_wand):
        self.resource = drawing_wand

    @drawing_wand.deleter
    def drawing_wand(self):
        del self.resource

    @property
    def font(self):
        return library.DrawGetFont(self.drawing_wand)

    @font.setter
    def font(self, font):
        if not isinstance(font, basestring):
            raise TypeError('font must be a basestring object, not ' +
                            repr(font))
        library.DrawSetFont(self.drawing_wand, font)

    @property
    def font_size(self):
        return library.DrawGetFontSize(self.drawing_wand)

    @font_size.setter
    def font_size(self, size):
        if not isinstance(size, numbers.Number):
            raise TypeError('expected a number, but got ' + repr(size))
        elif size < 0.0:
            raise ValueError('cannot be less then 0.0, but got ' + repr(size))

        library.DrawSetFontSize(self.drawing_wand, size)

    @property
    def fill_color(self):
        pixel = library.NewPixelWand()
        library.DrawGetFillColor(self.drawing_wand, pixel)

        size = ctypes.sizeof(MagickPixelPacket)
        buffer = ctypes.create_string_buffer(size)
        library.PixelGetMagickColor(pixel, buffer)

        return Color(raw=buffer)

    @fill_color.setter
    def fill_color(self, color):
        if not isinstance(color, Color):
            raise TypeError('color must be a wand.color.Color object, not ' +
                            repr(color))
        with color:
            library.DrawSetFillColor(self.drawing_wand, color.resource)

    @property
    def text_alignment(self):
        text_alignment_index = library.DrawGetTextAlignment(self.drawing_wand)
        if not text_alignment_index:
            self.raise_exception()
        return TEXT_ALIGN_TYPES[text_alignment_index]

    @text_alignment.setter
    def text_alignment(self, align):
        if not isinstance(align, basestring) \
            or align not in TEXT_ALIGN_TYPES:
            raise TypeError('Align value must be a string from ' +
                            'TEXT_ALIGN_TYPES, not ' + repr(align))

        library.DrawSetTextAlignment(self.drawing_wand,
                                     TEXT_ALIGN_TYPES.index(align))

    @property
    def text_antialias(self):
        result = library.DrawGetTextAntialias(self.drawing_wand)
        return True if result == 1 else False

    @text_antialias.setter
    def text_antialias(self, value):
        if not isinstance(value, bool):
            raise TypeError('value must be a boolean, not ' +
                            repr(value))
        library.DrawSetTextAntialias(self.drawing_wand,
                                     1 if value is True else 0)

    @property
    def text_decoration(self):
        text_decoration_index = library.DrawGetTextDecoration(self.drawing_wand)
        if not text_decoration_index:
            self.raise_exception()
        return TEXT_DECORATION_TYPES[text_decoration_index]

    @text_decoration.setter
    def text_decoration(self, decoration):
        if not isinstance(decoration, basestring) \
            or decoration not in TEXT_DECORATION_TYPES:
            raise TypeError('Decoration value must be a string from ' +
                            'TEXT_DECORATION_TYPES, not ' + repr(decoration))

        library.DrawSetTextDecoration(self.drawing_wand,
                                      TEXT_DECORATION_TYPES.index(decoration))

    @property
    def text_encoding(self):
        return library.DrawGetTextEncoding(self.drawing_wand)

    @text_encoding.setter
    def text_encoding(self, encoding):
        if encoding is not None \
            and not isinstance(encoding, basestring):
            raise TypeError('encoding must be a basestring object, not ' + 
                            repr(encoding))
        elif encoding is None:
            # encoding specify an empty string to set text encoding
            # to system's default.
            encoding = ''

        library.DrawSetTextEncoding(self.drawing_wand, encoding)

    @property
    def text_interline_spacing(self):
        return library.DrawGetTextInterlineSpacing(self.drawing_wand)

    @text_interline_spacing.setter
    def text_interline_spacing(self, spacing):
        if not isinstance(spacing, numbers.Number):
            raise TypeError('expeted a number, but got ' + repr(spacing))
        library.DrawSetTextInterlineSpacing(self.drawing_wand, spacing)

    @property
    def text_interword_spacing(self):
        return library.DrawGetTextInterwordSpacing(self.drawing_wand)

    @text_interword_spacing.setter
    def text_interword_spacing(self, spacing):
        if not isinstance(spacing, numbers.Number):
            raise TypeError('expeted a number, but got ' + repr(spacing))
        library.DrawSetTextInterwordSpacing(self.drawing_wand, spacing)

    @property
    def text_kerning(self):
        return library.DrawGetTextKerning(self.drawing_wand)

    @text_kerning.setter
    def text_kerning(self, kerning):
        if not isinstance(kerning, numbers.Number):
            raise TypeError('expeted a number, but got ' + repr(kerning))
        library.DrawSetTextKerning(self.drawing_wand, kerning)

    @property
    def text_under_color(self):
        pixel = library.NewPixelWand()
        library.DrawGetTextUnderColor(self.drawing_wand, pixel)

        size = ctypes.sizeof(MagickPixelPacket)
        buffer = ctypes.create_string_buffer(size)
        library.PixelGetMagickColor(pixel, buffer)

        return Color(raw=buffer)

    @text_under_color.setter
    def text_under_color(self, color):
        if not isinstance(color, Color):
            raise TypeError('color must be a wand.color.Color object, not ' +
                            repr(color))
        with color:
            library.DrawSetTextUnderColor(self.drawing_wand, color.resource)

    @property
    def gravity(self):
        gravity_index = library.DrawGetGravity(self.drawing_wand)
        if not gravity_index:
            self.raise_exception()

        return TEXT_GRAVITY_TYPE[gravity_index]

    @gravity.setter
    def gravity(self, value):
        if not isinstance(value, basestring) \
            or value not in TEXT_GRAVITY_TYPE:
            raise TypeError('Gravity value must be a string from ' +
                            'TEXT_GRAVITY_TYPE, not ' + repr(value))

        library.DrawSetGravity(self.drawing_wand,
                               TEXT_GRAVITY_TYPE.index(value))


    def clear(self):
        library.ClearDrawingWand(self.drawing_wand)

    def draw(self, image):
        res = library.MagickDrawImage(image.wand, self.drawing_wand)
        if not res:
            self.raise_exception()

    def line(self, start, end):
        if not isinstance(start, tuple) or len(start) != 2:
            raise TypeError('start must be a 2-dimensional tuple')
        if not isinstance(end, tuple) or len(end) != 2:
            raise TypeError('end must be a 2-dimensional tuple')

        library.DrawLine(self.drawing_wand,
                         start[0],
                         start[1],
                         end[0],
                         end[1])

    def text(self, x, y, body):
        if not isinstance(x, numbers.Integral) or x < 0:
            raise TypeError('x must be a natural number, not ' + repr(x))

        if not isinstance(y, numbers.Integral) or y < 0:
            raise TypeError('y must be a natural number, not ' + repr(x))

        if not isinstance(body, basestring) or len(body) < 1:
            raise TypeError('body must be a string, not ' + repr(body))

        body_p = None
        if self.text_encoding:
            body_p = ctypes.create_string_buffer(body.encode(self.text_encoding))
        else:
            body_p = ctypes.create_string_buffer(body)

        library.DrawAnnotation(self.drawing_wand,
                               x,
                               y,
                               ctypes.cast(body_p,ctypes.POINTER(ctypes.c_ubyte)))
