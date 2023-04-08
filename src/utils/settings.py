import configparser

from utils.constants import CONFIGS_DIR


class Settings:
    def __init__(self):
        self.profile_file_name = CONFIGS_DIR + "profiles.ini"
        self.settings_file_name = CONFIGS_DIR + "settings.ini"
        self.profiles_config = configparser.ConfigParser()
        self.settings_config = configparser.ConfigParser()

    def create_profile(self):
        self.profiles_config.read(self.profile_file_name)
        if not self.profiles_config.has_section('default'):
            data = ["D:/", "database"]

    def create_settings(self):
        self.settings_config.add_section('settings')
        self.settings_config.set('settings', 'profile', 'default')
        self.settings_config.set('settings', 'sorting', 'True')
        self._save_to_file_settings()

    def load_settings(self):
        self.settings_config.read(self.settings_file_name)
        if not self.settings_config.has_section('settings'):
            self.create_settings()
        return [self.settings_config.get('settings', 'profile'), self.settings_config.get('settings', 'sorting')]

    def save_settings(self, data):
        self.settings_config.set('settings', 'profile', data[0])
        self.settings_config.set('settings', 'sorting', data[1])
        self._save_to_file_settings()

    def load_profile(self):
        pass

    def save_profile(self):
        pass

    def new_template(self, section, data) -> bool:
        self.profiles_config.read(self.profile_file_name)
        if not self.profiles_config.has_section(section):
            self.profiles_config.read(section)
            self._set_data_to_profile(section, data)
            self._save_to_file_profile()
            return True
        return False

    def get_profile_list(self):
        self.profiles_config.read(self.profile_file_name)
        return self.profiles_config.sections()

    def get_data_from_profile(self, section):
        self.profiles_config.read(self.profile_file_name)
        return [self.profiles_config.get(section, 'path'), self.profiles_config.get(section, 'database')]

    def _save_to_file_profile(self):
        file_ini = open(self.profile_file_name, 'w')
        self.profiles_config.write(file_ini)
        file_ini.close()

    def _save_to_file_settings(self):
        file_ini = open(self.settings_file_name, 'w')
        self.settings_config.write(file_ini)
        file_ini.close()

    def _set_data_to_profile(self, section, data):
        self.profiles_config.add_section(section)
        self.profiles_config.set(section, 'path', str(data[0]))
        self.profiles_config.set(section, 'database', str(data[1]) + ".db")
