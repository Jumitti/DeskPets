import ctypes

from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

class GifHelper:
    @staticmethod
    def load_gif_frames(path):
        img = Image.open(path)
        frames = []
        try:
            while True:
                frame = img.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
                frames.append(frame)
                img.seek(img.tell() + 1)
        except EOFError:
            pass
        return frames

    @staticmethod
    def pil_to_hbitmap(frame: Image.Image):
        frame = frame.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
        width, height = frame.size
        pixels = frame.load()

        raw_data = bytearray()
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                r = r * a // 255
                g = g * a // 255
                b = b * a // 255
                raw_data += bytes([b, g, r, a])  # BGRA

        raw_buffer = (ctypes.c_ubyte * len(raw_data))(*raw_data)

        hdc = user32.GetDC(None)
        hdc_mem = gdi32.CreateCompatibleDC(hdc)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.c_uint32),
                ("biWidth", ctypes.c_int32),
                ("biHeight", ctypes.c_int32),
                ("biPlanes", ctypes.c_uint16),
                ("biBitCount", ctypes.c_uint16),
                ("biCompression", ctypes.c_uint32),
                ("biSizeImage", ctypes.c_uint32),
                ("biXPelsPerMeter", ctypes.c_int32),
                ("biYPelsPerMeter", ctypes.c_int32),
                ("biClrUsed", ctypes.c_uint32),
                ("biClrImportant", ctypes.c_uint32),
            ]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = width
        bmi.biHeight = -height
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        ppvBits = ctypes.c_void_p()
        hbitmap = gdi32.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(ppvBits), None, 0)
        ctypes.memmove(ppvBits, raw_buffer, len(raw_buffer))

        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(None, hdc)
        return hbitmap