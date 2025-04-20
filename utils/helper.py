import os
import sys
import time
import requests

from ping3 import ping
from functools import lru_cache


def get_resource_path_relative(relative_path):
    """PyInstaller ve normal çalışmada dosya yolu çözücüsü"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

@lru_cache
def get_resource_path(*path_parts):
    """PyInstaller ile uyumlu dosya yolu döndürür"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, *path_parts)


@lru_cache(3)
def check_ping(ip_list):
    _result = 0
    for ip in ip_list:
        response = ping(ip, timeout=2)
        _result += response * 1000
    return round(_result / len(ip_list), 2)


def create_message(identifier, msg_type, data):
    return {
        "id": identifier,
        "timestamp": time.time(),
        "data": {"type": msg_type, **data}
    }

@lru_cache(5)
def get_hub_ip(attempt = 0):
    if attempt > 5:
        return "192.168.1.31"
    try:
        if int(os.getenv("local", 0)) == 1:
            return os.getenv("HUB_IP")
        return requests.get(r"https://raw.githubusercontent.com/kantrveysel/sroserverbrowser/refs/heads/main/hub.txt").text
    except:
        time.sleep(3)
        return get_hub_ip(attempt+1)