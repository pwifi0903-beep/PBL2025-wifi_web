import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wisafe-secret-key-2024'
    DEBUG = True
    
    # JWT 설정
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # WiFi 스캔 설정
    WIFI_INTERFACE = os.environ.get('WIFI_INTERFACE') or None  # None이면 자동 감지
    WIFI_SCAN_DURATION = int(os.environ.get('WIFI_SCAN_DURATION', 15))  # 스캔 지속 시간 (초)
    
    # 크래킹 설정
    CRACKING_WORDLIST_PATH = os.environ.get('CRACKING_WORDLIST_PATH') or '/usr/share/wordlists/rockyou.txt'
    CRACKING_TIMEOUT = int(os.environ.get('CRACKING_TIMEOUT', 300))  # 크래킹 타임아웃 (초)
    CRACKING_PROGRESS_POLL_INTERVAL = int(os.environ.get('CRACKING_PROGRESS_POLL_INTERVAL', 2))  # 진행 상황 조회 간격 (초)