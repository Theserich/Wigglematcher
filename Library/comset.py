from Library.file import read_file, write_file
from typing import Union
from os.path import join



#settings = read_file(file_name='settings', path='Settings', file_format="json")
#path = settings['Settingspath']
#settingsFiles = settings['SettingsFiles']
#
#def set_path():
#    path = QFileDialog.getExistingDirectory(splash,'Select directory')
#    settingspath = join(path,'Settings')
#    datapath = join(path,'Data')
#    if path:
#        for name in settingsFiles:
#            set = read_file(file_name=name, path='Settings', file_format='json')
#            write_file(data=set, file_name=name, path=settingspath, file_format='json')
#        write_file(data=set, file_name=name, path=settingspath, file_format='json')
#        return settingspath,datapath,path
#    else:
#        return set_path()
#if path is None:
#   settingspath,datapath,path = set_path()
#   settings['Settingspath'] = path
#   write_file(data=settings, file_name='settings', path='Settings', file_format='json')
#else:
#    settingspath = join(path,'Settings')
#    datapath = join(path, 'Data')

settingspath = join('Library','Settings')


def read_settings(file_name: str, path: str = settingspath) -> Union[dict, None]:
    return read_file(file_name=file_name, path=path, file_format="json")


def write_settings(data: dict, file_name: str, path: str = settingspath) -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='json')


def read_data(file_name: str, path: str = "Data") -> Union[dict, None]:
    return read_file(file_name=file_name, path=path, file_format='pickle')


def write_data(data: dict, file_name: str, path: str = "Data") -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='pickle')

