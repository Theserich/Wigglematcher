from src.file import read_file, write_file
from typing import Union
from os.path import join

settingspath = join('Library','Settings')


def read_settings(file_name: str, path: str = settingspath) -> Union[dict, None]:
    return read_file(file_name=file_name, path=path, file_format="json")


def write_settings(data: dict, file_name: str, path: str = settingspath) -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='json')


def read_data(file_name: str, path: str = "Data") -> Union[dict, None]:
    return read_file(file_name=file_name, path=path, file_format='pickle')


def write_data(data: dict, file_name: str, path: str = "Data") -> None:
    return write_file(data=data, file_name=file_name, path=path, file_format='pickle')

