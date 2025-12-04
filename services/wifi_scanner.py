import subprocess
import re
import os
import time
import csv
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

class WiFiScanner:
    """aircrack-ng를 사용한 실제 WiFi 스캔 서비스"""
    
    def __init__(self, interface: Optional[str] = None, scan_duration: int = 15):
        """
        Args:
            interface: WiFi 어댑터 인터페이스 (None이면 자동 감지)
            scan_duration: 스캔 지속 시간 (초)
        """
        self.interface = interface
        self.scan_duration = scan_duration
        self.monitor_interface = None
        self.scan_output_dir = "/tmp/wisafe_scan"
        
    def detect_wifi_interface(self) -> Optional[str]:
        """WiFi 어댑터 인터페이스 자동 감지"""
        try:
            # iwconfig로 무선 인터페이스 찾기
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # wlan0, wlan1, wlp 등 무선 인터페이스 찾기
            for line in result.stdout.split('\n'):
                if 'IEEE 802.11' in line or 'ESSID' in line:
                    match = re.search(r'^(\w+)\s+', line)
                    if match:
                        interface = match.group(1)
                        # lo, eth 등은 제외
                        if interface.startswith(('wlan', 'wlp', 'wlx', 'wifi')):
                            return interface
            
            # ip link로도 시도
            result = subprocess.run(
                ['ip', 'link', 'show'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'wlan' in line.lower() or 'wlp' in line.lower():
                    match = re.search(r':\s*(\w+):', line)
                    if match:
                        interface = match.group(1)
                        if interface.startswith(('wlan', 'wlp', 'wlx', 'wifi')):
                            return interface
            
            return None
        except Exception as e:
            print(f"WiFi 인터페이스 감지 오류: {e}")
            return None
    
    def start_monitor_mode(self, interface: str) -> Optional[str]:
        """모니터 모드 활성화"""
        try:
            # airmon-ng로 모니터 모드 시작
            result = subprocess.run(
                ['sudo', 'airmon-ng', 'start', interface],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 모니터 모드 인터페이스 이름 찾기 (보통 wlan0mon, wlan1mon 등)
            for line in result.stdout.split('\n'):
                if 'monitor mode enabled' in line.lower():
                    match = re.search(r'on\s+(\w+)', line, re.IGNORECASE)
                    if match:
                        return match.group(1)
            
            # 기본 패턴으로 찾기
            if 'mon' in interface:
                return interface
            else:
                return f"{interface}mon"
                
        except Exception as e:
            print(f"모니터 모드 활성화 오류: {e}")
            return None
    
    def stop_monitor_mode(self, monitor_interface: str):
        """모니터 모드 비활성화"""
        try:
            if monitor_interface:
                subprocess.run(
                    ['sudo', 'airmon-ng', 'stop', monitor_interface],
                    capture_output=True,
                    timeout=10
                )
        except Exception as e:
            print(f"모니터 모드 비활성화 오류: {e}")
    
    def scan_wifi(self) -> List[Dict[str, Any]]:
        """실제 WiFi 스캔 수행"""
        # 인터페이스 감지
        if not self.interface:
            self.interface = self.detect_wifi_interface()
        
        if not self.interface:
            print("WiFi 인터페이스를 찾을 수 없습니다.")
            return []
        
        # 출력 디렉토리 생성
        os.makedirs(self.scan_output_dir, exist_ok=True)
        
        # 모니터 모드 활성화
        self.monitor_interface = self.start_monitor_mode(self.interface)
        
        if not self.monitor_interface:
            print("모니터 모드를 활성화할 수 없습니다.")
            return []
        
        try:
            # airodump-ng 실행
            output_file = os.path.join(self.scan_output_dir, "scan")
            csv_file = f"{output_file}-01.csv"
            
            # 기존 파일 삭제
            if os.path.exists(csv_file):
                os.remove(csv_file)
            
            # airodump-ng 실행 (백그라운드)
            process = subprocess.Popen(
                ['sudo', 'airodump-ng', '-w', output_file, '--output-format', 'csv', self.monitor_interface],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 스캔 시간만큼 대기
            time.sleep(self.scan_duration)
            
            # 프로세스 종료
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # CSV 파일 파싱
            wifi_list = self.parse_airodump_csv(csv_file)
            
            return wifi_list
            
        except Exception as e:
            print(f"WiFi 스캔 오류: {e}")
            return []
        finally:
            # 모니터 모드 비활성화
            if self.monitor_interface:
                self.stop_monitor_mode(self.monitor_interface)
    
    def parse_airodump_csv(self, csv_file: str) -> List[Dict[str, Any]]:
        """airodump-ng CSV 파일 파싱"""
        wifi_list = []
        
        if not os.path.exists(csv_file):
            return wifi_list
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # CSV 헤더 찾기
            header_line = None
            data_start = 0
            
            for i, line in enumerate(lines):
                if 'BSSID' in line and 'ESSID' in line:
                    header_line = i
                    data_start = i + 1
                    break
            
            if header_line is None:
                return wifi_list
            
            # 헤더 파싱
            header = [h.strip() for h in lines[header_line].split(',')]
            
            # 데이터 파싱
            for line in lines[data_start:]:
                if not line.strip() or line.strip().startswith('Station'):
                    break
                
                values = [v.strip() for v in line.split(',')]
                
                if len(values) < len(header):
                    continue
                
                # 딕셔너리 생성
                wifi_data = {}
                for i, key in enumerate(header):
                    if i < len(values):
                        wifi_data[key] = values[i]
                
                # 필요한 정보 추출
                bssid = wifi_data.get('BSSID', '').strip()
                essid = wifi_data.get('ESSID', '').strip()
                
                if not bssid or not essid or essid == '':
                    continue
                
                # 프로토콜 파싱
                encryption = wifi_data.get('Encryption', '').upper()
                protocol = self.parse_protocol(encryption)
                
                # 채널 파싱
                channel = wifi_data.get('channel', '0')
                try:
                    channel = int(re.search(r'\d+', str(channel)).group() if re.search(r'\d+', str(channel)) else '0')
                except:
                    channel = 0
                
                # 신호 강도 파싱
                power = wifi_data.get('Power', '0')
                try:
                    power = int(re.search(r'-?\d+', str(power)).group() if re.search(r'-?\d+', str(power)) else '0')
                except:
                    power = 0
                
                # 보안 수준 결정
                security_level = self.get_security_level(protocol)
                
                # 취약점 목록
                vulnerabilities = self.get_vulnerabilities(protocol)
                
                wifi_info = {
                    'ssid': essid,
                    'bssid': bssid,
                    'protocol': protocol,
                    'channel': channel,
                    'signal_strength': power,
                    'security_level': security_level,
                    'vulnerabilities': vulnerabilities,
                    'encryption': encryption,
                    'is_real_scan': True  # 실제 스캔 데이터 표시
                }
                
                wifi_list.append(wifi_info)
            
            return wifi_list
            
        except Exception as e:
            print(f"CSV 파싱 오류: {e}")
            return wifi_list
    
    def parse_protocol(self, encryption: str) -> str:
        """암호화 정보에서 프로토콜 추출"""
        encryption_upper = encryption.upper()
        
        if 'WPA3' in encryption_upper:
            return 'WPA3'
        elif 'WPA2' in encryption_upper:
            if 'WPS' in encryption_upper:
                return 'WPA2_WPS'
            return 'WPA2'
        elif 'WPA' in encryption_upper:
            return 'WPA'
        elif 'WEP' in encryption_upper:
            return 'WEP'
        else:
            return 'OPEN'
    
    def get_security_level(self, protocol: str) -> str:
        """프로토콜에 따른 보안 수준 반환"""
        level_map = {
            'OPEN': 'critical',
            'WEP': 'danger',
            'WPA': 'warning',
            'WPA2': 'safe',
            'WPA2_WPS': 'danger',
            'WPA3': 'safe'
        }
        return level_map.get(protocol.upper(), 'unknown')
    
    def get_vulnerabilities(self, protocol: str) -> List[str]:
        """프로토콜에 따른 취약점 목록 반환"""
        vuln_map = {
            'OPEN': ['무제한 접근', '데이터 도청 위험', '중간자 공격 가능', '패킷 스니핑 위험'],
            'WEP': ['WEP 암호화 취약', 'WEP 크랙 공격 가능'],
            'WPA': ['WPA 암호화 취약', 'WPA-TKIP 취약점'],
            'WPA2': [],
            'WPA2_WPS': ['WPS 활성화', 'WPS 핀 브루트포스', 'KRACK 공격 취약'],
            'WPA3': []
        }
        return vuln_map.get(protocol.upper(), [])
    
    def merge_with_dummy(self, real_wifi_list: List[Dict[str, Any]], dummy_wifi_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """실제 스캔 데이터와 더미 데이터 병합 (더미 데이터 먼저, 실제 데이터 나중에)"""
        # 더미 데이터에 is_real_scan 플래그 추가
        for wifi in dummy_wifi_list:
            wifi['is_real_scan'] = False
        
        # 더미 데이터 + 실제 데이터 순서로 병합
        merged_list = dummy_wifi_list + real_wifi_list
        
        return merged_list

# 전역 인스턴스
wifi_scanner = WiFiScanner()

