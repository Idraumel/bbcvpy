import configparser


class SettingsManager:
    def __init__(self, settings_file_path):
        self.settings_file_path = settings_file_path
        self.config = configparser.ConfigParser()
        self.opened_files = self.config.read(settings_file_path)
        if len(self.opened_files) == 0:
            raise Exception(
                f"Settings file of path {settings_file_path} could not be read"
            )

    def get_value(self, section_name, key):
        value = None
        try:
            section = self.config[section_name]
            value = section[key]
        except:
            print(f"The provided section or key does not exist")
            pass
        return value

    def set_value(self, section_name, key, value):
        try:
            print(value)
            if value == None:
                value = ""
            self.config[section_name][key] = value
            with open(self.settings_file_path, "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            print(f"The provided section or key does not exist")
            pass
