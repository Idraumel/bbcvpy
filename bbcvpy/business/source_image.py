from PIL import Image, PngImagePlugin
import json

METADATA_KEYS = [
    "active_area_points"
]

class SourceImage:
    def __init__(self, path):
        self.path = path
        self.im = Image.open(path)
        self.png_info = PngImagePlugin.PngInfo()
        for key, value in self.im.info.items():
            self.png_info.add_text(key, value)
        print(self.im.info)

    # returns the custom exif data of the image
    def get_metadata_value(self, key):
        value = self.im.info.get(key)
        if value is not None:
            if key in METADATA_KEYS:
                value = json.loads(value)
        return value

    # sets a metadata value and saves the image
    def set_metadata_value(self, key, value):
        if not key in METADATA_KEYS:
            raise Exception(f"The {key} key is not accepted in custom metadata")
        json_value = json.dumps(value)
        self.png_info.add_text(key, json_value)
        self.im.save(self.path, pnginfo=self.png_info)
        # reopen image to access updated metadata
        self.im = Image.open(self.path)
