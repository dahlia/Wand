# -*- coding: utf-8 -*-
from attest import assert_hook

import os
import os.path
import tempfile
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
import warnings

from attest import Tests, raises

from wand.image import ClosedImageError, Image
from wand.color import Color
from wand.exceptions import MissingDelegateError
from wand.font import Font


skip_slow_tests = bool(os.environ.get('WANDTESTS_SKIP_SLOW_TESTS'))

tests = Tests()


def asset(*path):
    return os.path.join(os.path.dirname(__file__), 'assets', *path)

@tests.test
def empty_image():
    with Image() as img:
        assert img.size == (0,0)


@tests.test
def blank_image():
    gray = Color('#ccc')
    transparent = Color('transparent')
    with raises(TypeError):
        Image(height=0, filename='/test.png')
    with raises(TypeError):
        Image(width=0, height=0)
    with Image(width=20, height=10) as img:
        assert img[10, 5] == transparent
    with Image(width=20, height=10, background=gray) as img:
        assert img.size == (20, 10)
        assert img[10, 5] == gray

@tests.test
def clear_image():
    with Image() as img:
        img.read(filename=asset('mona-lisa.jpg'))
        assert img.size == (402,599)
        img.clear()
        assert img.size == (0,0)
        img.read(filename=asset('beach.jpg'))
        assert img.size == (800,600)


@tests.test
def read_from_file():
    with Image() as img:
        img.read(filename=asset('mona-lisa.jpg'))
        assert img.width == 402
        img.clear()
        with open(asset('mona-lisa.jpg'), 'rb') as f:
            img.read(file=f)
            assert img.width == 402
            img.clear()
        with open(asset('mona-lisa.jpg'), 'rb') as f:
            blob = f.read()
            img.read(blob=blob)
            assert img.width == 402


@tests.test
def new_from_file():
    """Opens an image from the file object."""
    with open(asset('mona-lisa.jpg'), 'rb') as f:
        with Image(file=f) as img:
            assert img.width == 402
    with raises(ClosedImageError):
        img.wand
    with open(asset('mona-lisa.jpg'), 'rb') as f:
        strio = StringIO.StringIO(f.read())
    with Image(file=strio) as img:
        assert img.width == 402
    strio.close()
    with raises(ClosedImageError):
        img.wand
    with raises(TypeError):
        Image(file='not file object')


@tests.test
def new_from_filename():
    """Opens an image through its filename."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.width == 402
    with raises(ClosedImageError):
        img.wand
    with raises(IOError):
        Image(filename=asset('not-exists.jpg'))


@tests.test
def new_from_blob():
    """Opens an image from blob."""
    with open(asset('mona-lisa.jpg'), 'rb') as f:
        blob = f.read()
    with Image(blob=blob) as img:
        assert img.width == 402
    with raises(ClosedImageError):
        img.wand


@tests.test
def new_with_format():
    with open(asset('google.ico'), 'rb') as f:
        blob = f.read()
    with raises(Exception):
        Image(blob=blob)
    with Image(blob=blob, format='ico') as img:
        assert img.size == (16, 16)


@tests.test
def clone():
    """Clones the existing image."""
    funcs = (lambda img: Image(image=img),
             lambda img: img.clone())
    with Image(filename=asset('mona-lisa.jpg')) as img:
        for func in funcs:
            with func(img) as cloned:
                assert img.wand is not cloned.wand
                assert img.size == cloned.size
            with raises(ClosedImageError):
                cloned.wand
    with raises(ClosedImageError):
        img.wand


@tests.test
def save_to_filename():
    """Saves an image to the filename."""
    savefile = os.path.join(tempfile.mkdtemp(), 'savetest.jpg')
    with Image(filename=asset('mona-lisa.jpg')) as orig:
        orig.save(filename=savefile)
        with raises(IOError):
            orig.save(filename=os.path.join(savefile, 'invalid.jpg'))
        with raises(TypeError):
            orig.save(filename=1234)
    assert os.path.isfile(savefile)
    with Image(filename=savefile) as saved:
        assert saved.size == (402, 599)
    os.remove(savefile)


@tests.test
def save_to_file():
    """Saves an image to the Python file object."""
    buffer = StringIO.StringIO()
    with tempfile.TemporaryFile() as savefile:
        with Image(filename=asset('mona-lisa.jpg')) as orig:
            orig.save(file=savefile)
            orig.save(file=buffer)
            with raises(TypeError):
                orig.save(file='filename')
            with raises(TypeError):
                orig.save(file=1234)
        savefile.seek(0)
        with Image(file=savefile) as saved:
            assert saved.size == (402, 599)
        buffer.seek(0)
        with Image(file=buffer) as saved:
            assert saved.size == (402, 599)
    buffer.close()


@tests.test
def save_error():
    filename = os.path.join(tempfile.mkdtemp(), 'savetest.jpg')
    fileobj = StringIO.StringIO()
    with Image(filename=asset('mona-lisa.jpg')) as orig:
        with raises(TypeError):
            orig.save()
        with raises(TypeError):
            orig.save(filename=filename, file=fileobj)


@tests.test
def make_blob():
    """Makes a blob string."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with Image(blob=img.make_blob('png')) as img2:
            assert img2.size == (402, 599)
            assert img2.format == 'PNG'
        assert img.format == 'JPEG'
        with raises(TypeError):
            img.make_blob(123)
    svg = '''
    <svg width="100px" height="100px">
    <circle cx="100" cy="50" r="40" stroke="black" stroke-width="2" fill="red"/>
    </svg>
    '''
    with Image(blob=svg, format='svg') as img:
        assert img.size == (100, 100)
        assert img.format in ('SVG', 'MVG')
        img.format = 'PNG'
        assert img.size == (100, 100)
        assert img.format == 'PNG'
        png = img.make_blob()
    with Image(blob=png, format='png') as img:
        assert img.size == (100, 100)
        assert img.format == 'PNG'


@tests.test
def size():
    """Gets the image size."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.size == (402, 599)
        assert img.width == 402
        assert img.height == 599
        assert len(img) == 599


@tests.test
def get_resolution():
    """Gets image resolution."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.resolution == (72, 72)


@tests.test
def set_resolution_01():
    """Sets image resolution."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.resolution = (100, 100)
        assert img.resolution == (100, 100)


@tests.test
def set_resolution_02():
    """Sets image resolution with integer as parameter."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.resolution = 100
        assert img.resolution == (100, 100)


@tests.test
def set_resolution_03():
    """Sets image resolution on constructor"""
    with Image(filename=asset('sample.pdf'), resolution=(100,100)) as img:
        assert img.resolution == (100, 100)


@tests.test
def set_resolution_04():
    """Sets image resolution on constructor with integer as parameter."""
    with Image(filename=asset('sample.pdf'), resolution=100) as img:
        assert img.resolution == (100, 100)


@tests.test
def get_units():
    """Gets the image resolution units."""
    with Image(filename=asset('beach.jpg')) as img:
        assert img.units == "pixelsperinch"
    with Image(filename=asset('sasha.jpg')) as img:
        assert img.units == "undefined"


@tests.test
def set_units():
    """Sets the image resolution units."""
    with Image(filename=asset('watermark.png')) as img:
        img.units="pixelspercentimeter"
        assert img.units == "pixelspercentimeter"


@tests.test
def get_depth():
    """Gets the image depth"""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.depth == 8


@tests.test
def set_depth():
    """Sets the image depth"""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.depth = 16
        assert img.depth == 16


@tests.test
def get_format():
    """Gets the image format."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.format == 'JPEG'
    with Image(filename=asset('croptest.png')) as img:
        assert img.format == 'PNG'


@tests.test
def set_format():
    """Sets the image format."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.format = 'png'
        assert img.format == 'PNG'
        strio = StringIO.StringIO()
        img.save(file=strio)
        strio.seek(0)
        with Image(file=strio) as png:
            assert png.format == 'PNG'
        with raises(ValueError):
            img.format = 'HONG'
        with raises(TypeError):
            img.format = 123


@tests.test
def get_type():
    """Gets the image type."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.type == "truecolor"
        img.alpha_channel = True
        assert img.type == "truecolormatte"


@tests.test
def set_type():
    """Sets the image type."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.type = "grayscale"
        assert img.type == "grayscale"


@tests.test
def get_compression():
    """Gets the image compression quality."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.compression_quality == 80


@tests.test
def set_compression():
    """Sets the image compression quality."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        img.compression_quality = 50
        assert img.compression_quality == 50
        strio = StringIO.StringIO()
        img.save(file=strio)
        strio.seek(0)
        with Image(file=strio) as jpg:
            assert jpg.compression_quality == 50
        with raises(TypeError):
            img.compression_quality = 'high'


@tests.test
def strip():
    """Strips the image of all profiles and comments."""
    with Image(filename=asset('beach.jpg')) as img:
        strio = StringIO.StringIO()
        img.save(file=strio)
        len_unstripped = strio.tell()
        strio.truncate(0)
        img.strip()
        img.save(file=strio)
        len_stripped = strio.tell()
        assert len_unstripped > len_stripped


@tests.test
def trim():
    """Remove transparent area around image."""
    with Image(filename=asset('trimtest.png')) as img:
        oldx, oldy = img.size
        img.trim()
        newx, newy = img.size
        assert newx < oldx
        assert newy < oldy
    with Image(filename=asset('trimtest.png')) as img:
        img.trim()
        trimx, trimy = img.size
        img.trim(fuzz=10000)
        fuzzx, fuzzy = img.size
        assert fuzzx < trimx
        assert fuzzy < trimy
    with Image(filename=asset('trim-color-test.png')) as img:
        assert img.size == (100, 100)
        with Color('blue') as blue:
            img.trim(blue)
            assert img.size == (50, 100)
        with Color('srgb(0,255,0)') as green:
            assert (img[0, 0] == img[0, -1] == img[-1, 0] == img[-1, -1] ==
                    green)


@tests.test
def get_mimetype():
    """Gets mimetypes of the image."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.mimetype in ('image/jpeg', 'image/x-jpeg')
    with Image(filename=asset('croptest.png')) as img:
        assert img.mimetype in ('image/png', 'image/x-png')


@tests.test
def convert():
    """Converts the image format."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with img.convert('png') as converted:
            assert converted.format == 'PNG'
            strio = StringIO.StringIO()
            converted.save(file=strio)
            strio.seek(0)
            with Image(file=strio) as png:
                assert png.format == 'PNG'
        with raises(ValueError):
            img.convert('HONG')
        with raises(TypeError):
            img.convert(123)


@tests.test_if(not skip_slow_tests)
def iterate():
    """Uses iterator."""
    with Color('#000') as black:
        with Color('transparent') as transparent:
            with Image(filename=asset('croptest.png')) as img:
                for i, row in enumerate(img):
                    assert len(row) == 300
                    if i % 3:
                        continue # avoid slowness
                    if 100 <= i < 200:
                        for x, color in enumerate(row):
                            if x % 3:
                                continue # avoid slowness
                            if 100 <= x < 200:
                                assert color == black
                            else:
                                assert color == transparent
                    else:
                        for color in row:
                            assert color == transparent
                assert i == 299


@tests.test
def slice_clone():
    """Clones using slicing."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with img[:,:] as cloned:
            assert img.size == cloned.size


@tests.test
def slice_invalid_types():
    """Slicing with invalid types should throw exceptions."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with raises(TypeError):
            img['12']
        with raises(TypeError):
            img[1.23]
        with raises(ValueError):
            img[()]
        with raises(ValueError):
            img[:, :, :]
        with raises(ValueError):
            img[::2, :]
        with raises(IndexError):
            img[1:1, :]
        with raises(IndexError):
            img[:, 2:2]
        with raises(TypeError):
            img[100.0:, 100.0]
        with raises(TypeError):
            img['100':, '100']
        with raises(IndexError):
            img[500:, 900]
        with raises(TypeError):
            img['1', 0]
        with raises(TypeError):
            img[1, '0']
    with Image(filename=asset('croptest.png')) as img:
        with raises(IndexError):
            img[300, 300]
        with raises(IndexError):
            img[-301, -301]


@tests.test
def index_pixel():
    """Gets a pixel."""
    with Image(filename=asset('croptest.png')) as img:
        assert img[0, 0] == Color('transparent')
        assert img[99, 99] == Color('transparent')
        assert img[100, 100] == Color('black')
        assert img[150, 150] == Color('black')
        assert img[-200, -200] == Color('black')
        assert img[-201, -201] == Color('transparent')


@tests.test
def index_row():
    """Gets a row."""
    with Color('transparent') as transparent:
        with Color('black') as black:
            with Image(filename=asset('croptest.png')) as img:
                for c in img[0]:
                    assert c == transparent
                for c in img[99]:
                    assert c == transparent
                for i, c in enumerate(img[100]):
                    if 100 <= i < 200:
                        assert c == black
                    else:
                        assert c == transparent
                for i, c in enumerate(img[150]):
                    if 100 <= i < 200:
                        assert c == black
                    else:
                        assert c == transparent
                for i, c in enumerate(img[-200]):
                    if 100 <= i < 200:
                        assert c == black
                    else:
                        assert c == transparent
                for c in img[-201]:
                    assert c == transparent


@tests.test
def slice_crop():
    """Crops using slicing."""
    with Image(filename=asset('croptest.png')) as img:
        with img[100:200, 100:200] as cropped:
            assert cropped.size == (100, 100)
            with Color('#000') as black:
                for row in cropped:
                    for col in row:
                        assert col == black
        with img[150:, :150] as cropped:
            assert cropped.size == (150, 150)
        with img[-200:-100, -200:-100] as cropped:
            assert cropped.size == (100, 100)
        with img[100:200] as cropped:
            assert cropped.size == (300, 100)
        assert img.size == (300, 300)
        with raises(IndexError):
            img[:500, :500]
        with raises(IndexError):
            img[290:310, 290:310]


@tests.test_if(not skip_slow_tests)
def crop():
    """Crops in-place."""
    with Image(filename=asset('croptest.png')) as img:
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(100, 100, 200, 200)
            assert cropped.size == (100, 100)
            with Color('#000') as black:
                for row in cropped:
                    for col in row:
                        assert col == black
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(100, 100, width=100, height=100)
            assert cropped.size == (100, 100)
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(left=150, bottom=150)
            assert cropped.size == (150, 150)
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(left=150, height=150)
            assert cropped.size == (150, 150)
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(-200, -200, -100, -100)
            assert cropped.size == (100, 100)
        with img.clone() as cropped:
            assert cropped.size == img.size
            cropped.crop(top=100, bottom=200)
            assert cropped.size == (300, 100)
        with raises(ValueError):
            img.crop(0, 0, 500, 500)
        with raises(ValueError):
            img.crop(290, 290, 50, 50)
        with raises(ValueError):
            img.crop(290, 290, width=0, height=0)


@tests.test
def crop_error():
    """Crop errors."""
    with Image(filename=asset('croptest.png')) as img:
        with raises(TypeError):
            img.crop(right=1, width=2)
        with raises(TypeError):
            img.crop(bottom=1, height=2)


@tests.test
def resize():
    """Resizes the image."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with img.clone() as a:
            assert a.size == (402, 599)
            a.resize(100, 100)
            assert a.size == (100, 100)
        with img.clone() as b:
            assert b.size == (402, 599)
            b.resize(height=100)
            assert b.size == (402, 100)
        with img.clone() as c:
            assert c.size == (402, 599)
            c.resize(width=100)
            assert c.size == (100, 599)

@tests.test
def test_gif():
    """Test the gif image resize/crop/rotate"""
    with Image(filename=asset('nocomments.gif')) as img:
        assert img.frame_num == 46
        with img.clone() as a:
            assert a.size == (350, 197)
            a.resize(175, 98)
            a.save(filename="175_98.gif")
            assert a.frame_num == 46
            assert a.size == (175, 98)
        with img.clone() as b:
            assert b.size == (350, 197)
            b.resize(height=100)
            b.save(filename="350_100.gif")
            assert b.frame_num == 46
            assert b.size == (350, 100)
        with img.clone() as c:
            assert c.size == (350, 197)
            c.resize(width=100)
            c.save(filename="100_197.gif")
            assert c.frame_num == 46
            assert c.size == (100, 197)
        with img.clone() as d:
            assert d.size == (350, 197)
            d.crop(50, 50, 200, 150)
            d.save(filename="50_50_200_150.gif")
            assert d.frame_num == 46
            assert d.size == (150, 100)
        with img.clone() as e:
            assert e.size == (350, 197)
            e.rotate(90)
            e.save(filename="rotate_90.gif")
            assert e.size == (197, 350)
            assert e.frame_num == 46

@tests.test
def resize_errors():
    """Resizing errors."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with raises(TypeError):
            img.resize(width='100')
        with raises(TypeError):
            img.resize(height='100')
        with raises(ValueError):
            img.resize(width=0)
        with raises(ValueError):
            img.resize(height=0)
        with raises(ValueError):
            img.resize(width=-5)
        with raises(ValueError):
            img.resize(height=-5)

@tests.test
def transform():
    """Transforms (crops and resizes with geometry strings) the image."""
    with Image(filename=asset('beach.jpg')) as img:
        with img.clone() as a:
            assert a.size == (800, 600)
            a.transform(resize='200%')
            assert a.size == (1600, 1200)
        with img.clone() as b:
            assert b.size == (800, 600)
            b.transform(resize='200%x100%')
            assert b.size == (1600, 600)
        with img.clone() as c:
            assert c.size == (800, 600)
            c.transform(resize='1200')
            assert c.size == (1200, 900)
        with img.clone() as d:
            assert d.size == (800, 600)
            d.transform(resize='x300')
            assert d.size == (400, 300)
        with img.clone() as e:
            assert e.size == (800, 600)
            e.transform(resize='400x600')
            assert e.size == (400, 300)
        with img.clone() as f:
            assert f.size == (800, 600)
            f.transform(resize='1000x1200^')
            assert f.size == (1600, 1200)
        with img.clone() as g:
            assert g.size == (800, 600)
            g.transform(resize='100x100!')
            assert g.size == (100, 100)
        with img.clone() as h:
            assert h.size == (800, 600)
            h.transform(resize='400x500>')
            assert h.size == (400, 300)
        with img.clone() as i:
            assert i.size == (800, 600)
            i.transform(resize='1200x3000<')
            assert i.size == (1200, 900)
        with img.clone() as j:
            assert j.size == (800, 600)
            j.transform(resize='120000@')
            assert j.size == (400, 300)
        with img.clone() as k:
            assert k.size == (800, 600)
            k.transform(crop='300x300')
            assert k.size == (300, 300)
        with img.clone() as l:
            assert l.size == (800, 600)
            l.transform(crop='300x300+100+100')
            assert l.size == (300, 300)
        with img.clone() as m:
            assert m.size == (800, 600)
            m.transform(crop='300x300-150-150')
            assert m.size == (150, 150)
        with img.clone() as n:
            assert n.size == (800, 600)
            n.transform('300x300', '200%')
            assert n.size == (600, 600)

@tests.test
def transform_errors():
    """Tests errors raised by invalid parameters for transform."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with raises(TypeError):
            img.transform(crop=500)
        with raises(TypeError):
            img.transform(resize=500)
        with raises(TypeError):
            img.transform(500, 500)
        with raises(ValueError):
            img.transform(crop=u'⚠ ')
        with raises(ValueError):
            img.transform(resize=u'⚠ ')

@tests.test_if(not skip_slow_tests)
def rotate():
    """Rotates an image."""
    with Image(filename=asset('rotatetest.gif')) as img:
        assert 150 == img.width
        assert 100 == img.height
        with img.clone() as cloned:
            cloned.rotate(360)
            assert img.size == cloned.size
            with Color('black') as black:
                assert black == cloned[0, 50] == cloned[74, 50]
                assert black == cloned[0, 99] == cloned[74, 99]
            with Color('white') as white:
                assert white == cloned[75, 50] == cloned[75, 99]
        with img.clone() as cloned:
            cloned.rotate(90)
            assert 100 == cloned.width
            assert 150 == cloned.height
            with Color('black') as black:
                with Color('white') as white:
                    for y, row in enumerate(cloned):
                        for x, col in enumerate(row):
                            if y < 75 and x < 50:
                                assert col == black
                            else:
                                assert col == white
        with Color('red') as bg:
            with img.clone() as cloned:
                cloned.rotate(45, bg)
                assert 176 <= cloned.width == cloned.height <= 178
                assert bg == cloned[0, 0] == cloned[0, -1]
                assert bg == cloned[-1, 0] == cloned[-1, -1]
                with Color('black') as black:
                    assert black == cloned[2, 70] == cloned[35, 37]
                    assert black == cloned[85, 88] == cloned[52, 120]


@tests.test
def transparent_color():
    """TransparentPaint test"""
    with Image(filename=asset('rotatetest.gif')) as img:
        img.alpha_channel = True
        with Color('white') as white:
            img.transparent_color(white, 0.0, 2, 0)
            assert img[75, 50].alpha == 0
            assert img[0, 50].alpha == 1.0


@tests.test
def signature():
    """Gets the image signature."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        with open(asset('mona-lisa.jpg'), 'rb') as f:
            with Image(file=f) as same:
                assert img.signature == same.signature
        with img.convert('png') as same:
            assert img.signature == same.signature
        with Image(filename=asset('beach.jpg')) as diff:
            assert img.signature != diff.signature


@tests.test
def equal():
    """Equals (``==``) and not equals (``!=``) operators."""
    with Image(filename=asset('mona-lisa.jpg')) as a:
        with Image(filename=asset('mona-lisa.jpg')) as a2:
            assert a == a2
            assert not (a != a2)
        with Image(filename=asset('sasha.jpg')) as b:
            assert a != b
            assert not (a == b)
        with a.convert('png') as a3:
            assert a == a3
            assert not (a != a3)


@tests.test
def object_hash():
    """Gets :func:`hash()` of the image."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        a = hash(img)
        img.format = 'png'
        b = hash(img)
        assert a == b


@tests.test
def get_alpha_channel():
    """Checks if image has alpha channel."""
    with Image(filename=asset('watermark.png')) as img:
        assert img.alpha_channel == True
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert img.alpha_channel == False


@tests.test
def set_alpha_channel():
    """Sets alpha channel to off."""
    with Image(filename=asset('watermark.png')) as img:
        assert img.alpha_channel == True
        img.alpha_channel = False
        assert img.alpha_channel == False


@tests.test
def get_background_color():
    """Gets the background color."""
    with Image(filename=asset('mona-lisa.jpg')) as img:
        assert Color('white') == img.background_color


@tests.test
def set_background_color():
    """Sets the background color."""
    with Image(filename=asset('croptest.png')) as img:
        with Color('transparent') as color:
            img.background_color = color
            assert img.background_color == color


@tests.test
def transparentize():
    with Image(filename=asset('croptest.png')) as im:
        with Color('transparent') as transparent:
            with Color('black') as black:
                assert im[99, 100] == transparent
                assert im[100, 100] == black
                im.transparentize(0.3)
                assert im[99, 100] == transparent
                with im[100, 100] as c:
                    assert c.red == c.green == c.blue == 0
                    assert 0.69 < c.alpha < 0.71


@tests.test
def watermark():
    """Adds  watermark to an image."""
    with Image(filename=asset('beach.jpg')) as img:
        with Image(filename=asset('watermark.png')) as wm:
            a = img[70, 83]
            b = img[70, 84]
            c = img[623, 282]
            d = img[622, 281]
            img.watermark(wm, 0.3)
            assert img[70, 83] == a
            assert img[70, 84] != b
            assert img[623, 282] == c
            assert img[622, 281] != d


@tests.test
def reset_coords():
    """Reset the coordinate frame so to the upper-left corner of
    the image is (0, 0) again.

    """
    with Image(filename=asset('sasha.jpg')) as img:
            img.rotate(45, reset_coords=True)
            img.crop(0, 0, 170, 170)
            assert img[85, 85] == Color('transparent')


@tests.test
def metadata():
    """Test metadata api"""
    with Image(filename=asset('beach.jpg')) as img:
        assert len(img.metadata) == 52
        assert 'exif:ApertureValue' in img.metadata
        assert 'exif:UnknownValue' not in img.metadata
        assert img.metadata['exif:ApertureValue'] == '192/32'
        assert img.metadata.get('exif:UnknownValue', "IDK") == "IDK"


@tests.test
def channel_depths():
    with Image(filename=asset('beach.jpg')) as i:
        assert dict(i.channel_depths) == {
            'blue': 8, 'gray': 8, 'true_alpha': 1, 'opacity': 1,
            'undefined': 1, 'composite_channels': 8, 'index': 1,
            'rgb_channels': 1, 'alpha': 1, 'yellow': 8, 'sync_channels': 1,
            'default_channels': 8, 'black': 1, 'cyan': 8,
            'all_channels': 8, 'green': 8, 'magenta': 8, 'red': 8,
            'gray_channels': 1
        }
    with Image(filename=asset('google.ico')) as i:
        assert dict(i.channel_depths) == {
            'blue': 8, 'gray': 8, 'true_alpha': 1, 'opacity': 1,
            'undefined': 1, 'composite_channels': 8, 'index': 1,
            'rgb_channels': 1, 'alpha': 1, 'yellow': 8, 'sync_channels': 1,
            'default_channels': 8, 'black': 1, 'cyan': 8, 'all_channels': 8,
            'green': 8, 'magenta': 8, 'red': 8, 'gray_channels': 1
        }


@tests.test
def channel_images():
    with Image(filename=asset('sasha.jpg')) as i:
        i.format = 'png'
        for name in 'opacity', 'alpha', 'true_alpha':
            expected_path = asset('channel_images', name + '.png')
            with Image(filename=expected_path) as expected:
                assert i.channel_images[name] == expected


@tests.test
def composite():
    with Image(filename=asset('beach.jpg')) as orig:
        with orig.clone() as img:
            with Image(filename=asset('watermark.png')) as fg:
                img.composite(fg, 5, 10)
            # These pixels should not be changed:
            assert img[0, 0] == orig[0, 0]
            assert img[0, img.height - 1] == orig[0, orig.height - 1]
            assert img[img.width - 1, 0] == orig[orig.width - 1, 0]
            assert (img[img.width - 1, img.height - 1] == 
                    orig[orig.width - 1, img.height - 1])
            # These pixels should be the almost black:
            assert img[70, 100].red <= 1
            assert img[70, 100].green <= 1
            assert img[70, 100].blue <= 1
            assert img[130, 100].red <= 1
            assert img[130, 100].green <= 1
            assert img[130, 100].blue <= 1


@tests.test
def composite_channel():
    with Image(filename=asset('beach.jpg')) as orig:
        w, h = orig.size
        left = w / 4
        top = h / 4
        right = left * 3 - 1
        bottom = h / 4 * 3 - 1
        # List of (x, y) points that shouldn't be changed:
        outer_points = [
            (0, 0), (0, h - 1), (w - 1, 0), (w - 1, h - 1),
            (left, top - 1), (left - 1, top), (left - 1, top - 1),
            (right, top - 1), (right + 1, top), (right + 1, top - 1),
            (left, bottom + 1), (left - 1, bottom), (left - 1, bottom + 1),
            (right, bottom + 1), (right + 1, bottom), (right + 1, bottom + 1)
        ]
        with orig.clone() as img:
            with Color('black') as color:
                with Image(width=w / 2, height=h / 2, background=color) as cimg:
                    img.composite_channel('red', cimg, 'copy_red',
                                          w / 4, h / 4)
            # These points should be not changed:
            for point in outer_points:
                assert orig[point] == img[point]
            # Inner pixels should lost its red color (red becomes 0)
            for point in zip([left, right], [top, bottom]):
                with orig[point] as oc:
                    with img[point] as ic:
                        assert not ic.red
                        assert ic.green == oc.green
                        assert ic.blue == oc.blue


@tests.test
def liquid_rescale():
    def assert_equal_except_alpha(a, b):
        with a:
            with b:
                assert (a.red == b.red and
                        a.green == b.green and
                        a.blue == b.blue)
    with Image(filename=asset('beach.jpg')) as orig:
        with orig.clone() as img:
            try:
                img.liquid_rescale(600, 600)
            except MissingDelegateError:
                warnings.warn('skip liquid_rescale test; has no LQR delegate')
            else:
                assert img.size == (600, 600)
                for x in 0, -1:
                    for y in 0, -1:
                        assert_equal_except_alpha(img[x, y], img[x, y])


@tests.test
def border():
    with Image(filename=asset('sasha.jpg')) as img:
        left_top = img[0, 0]
        left_bottom = img[0, -1]
        right_top = img[-1, 0]
        right_bottom = img[-1, -1]
        with Color('red') as color:
            img.border(color, 2, 5)
            assert (img[0, 0] == img[0, -1] == img[-1, 0] == img[-1, -1] ==
                    img[1, 4] == img[1, -5] == img[-2, 4] == img[-2, -5] ==
                    color)
            assert img[2, 5] == left_top
            assert img[2, -6] == left_bottom
            assert img[-3, 5] == right_top
            assert img[-3, -6] == right_bottom


@tests.test
def caption():
    with Image(width=144, height=192, background=Color('#1e50a2')) as img:
        font = Font(
            path=asset('League_Gothic.otf'),
            color=Color("gold"),
            size=12,
            antialias=False
        )
        img.caption(
            'Test message',
            font=font,
            left=5, top=144,
            width=134, height=20,
            gravity='center'
        )


@tests.test
def setfont():
    with Image(width=144, height=192, background=Color('#1e50a2')) as img:
        font = Font(
            path=asset('League_Gothic.otf'),
            color=Color('gold'),
            size=12,
            antialias=False
        )
        img.font = font
        assert img.font_path == font.path
        assert img.font_size == font.size
        assert img.font_color == font.color
        assert img.font_antialias == font.antialias
        assert img.font == font


@tests.test
def setgravity():
    with Image(width=144, height=192, background=Color('#1e50a2')) as img:
        img.gravity = 'center'
        assert img.gravity == 'center'


@tests.test
def normalize_default():
    with Image(filename=asset('gray_range.jpg')) as img:
        left_top = img[0, 0]
        left_bottom = img[0, -1]
        right_top = img[-1, 0]
        right_bottom = img[-1, -1]
        img.normalize()
        assert img[0, 0] != left_top
        assert img[0, -1] != left_bottom
        assert img[-1, 0] != right_top
        assert img[-1, -1] != right_bottom
        black = Color('#000')
        white = Color('#FFFFFF')
        assert img[0, 0] == white
        assert img[-1, -1] == black


@tests.test
def normalize_channel():
    with Image(filename=asset('gray_range.jpg')) as img:
        left_top = img[0, 0]
        left_bottom = img[0, -1]
        right_top = img[-1, 0]
        right_bottom = img[-1, -1]
        img.normalize('red')
        assert img[0, 0] != left_top
        assert img[0, -1] != left_bottom
        assert img[-1, 0] != right_top
        assert img[-1, -1] != right_bottom
        # Normalizing the 'red' channel of gray_range.jpg should result in
        # top,left red channel == 255, and lower left red channel == 0
        assert img[0, 0].red_int8 == 255
        assert img[0, -1].red_int8 == 0
        # Just for fun, make sure we haven't altered any other color channels.
        for chan in ('blue', 'green'):
            c = chan + '_int8'
            assert getattr(img[0, 0], c) == getattr(left_top, c)
            assert getattr(img[0, -1], c) == getattr(left_bottom, c)
            assert getattr(img[-1, 0], c) == getattr(right_top, c)
            assert getattr(img[-1, -1], c) == getattr(right_bottom, c)


@tests.test
def flip():
    with Image(filename=asset('beach.jpg')) as img:
        with img.clone() as flipped:
            flipped.flip()
            assert flipped[0, 0] == img[0, -1]
            assert flipped[0, -1] == img[0, 0]
            assert flipped[-1, 0] == img[-1, -1]
            assert flipped[-1, -1] == img[-1, 0]


@tests.test
def flop():
    with Image(filename=asset('beach.jpg')) as img:
        with img.clone() as flopped:
            flopped.flop()
            assert flopped[0, 0] == img[-1, 0]
            assert flopped[-1, 0] == img[0, 0]
            assert flopped[0, -1] == img[-1, -1]
            assert flopped[-1, -1] == img[0, -1]


@tests.test
def get_orientation():
    with Image(filename=asset('sasha.jpg')) as img:
        assert img.orientation == 'undefined'

    with Image(filename=asset('beach.jpg')) as img:
        assert img.orientation == 'top_left'


@tests.test
def set_orientation():
    with Image(filename=asset('beach.jpg')) as img:
        img.orientation = 'bottom_right'
        assert img.orientation == 'bottom_right'
