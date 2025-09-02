from src.comset import read_settings, write_settings
from os.path import join
from PyQt5.Qt import QFont

def resize_window(window,name):
    path = join('UISettings','windowsizes')
    settings = read_settings(path)
    width = settings[name]['width']
    height = settings[name]['height']
    window.resize(width, height)
    set_label_size(window,name)


def save_size(window,name):
    w = window.width()
    h = window.height()
    path = 'windowsizes'
    settings = read_settings(path)
    settings[name]['height'] = h
    settings[name]['width'] = w
    write_settings(settings, path)

def set_label_size(window,name,factor=1):
    fontsize = read_settings('display_settings')['fontsize']*factor
    path = 'windowsizes'
    settings = read_settings(path)
    font = QFont()
    font.setPointSize(int(fontsize * 0.8))
    for label in settings[name]['labels']:
        window.__dict__[label].setFont(font)
