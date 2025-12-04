import subprocess
import re
import os
import time
import csv
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from config import Config

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
            # airmon-ng로 모니터 모드 시작 (sudo 비밀번호 자동 입력)
            result = subprocess.run(
                f"echo '{Config.SUDO_PASSWORD}' | sudo -S airmon-ng start {interface}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"[모니터 모드] airmon-ng stdout:\n{result.stdout}")
            if result.stderr:
                print(f"[모니터 모드] airmon-ng stderr:\n{result.stderr}")
            
            # 모니터 모드 활성화 후 iwconfig로 확인
            # 이 시스템에서는 모니터 모드 인터페이스 이름이 원래 인터페이스와 동일함 (wlan0 -> wlan0)
            iwconfig_result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 원래 인터페이스가 모니터 모드인지 확인
            for line in iwconfig_result.stdout.split('\n'):
                if interface in line and 'Mode:Monitor' in line:
                    print(f"[모니터 모드] 인터페이스 {interface}가 모니터 모드로 활성화됨")
                    return interface
            
            # 원래 인터페이스 이름 반환 (이 시스템에서는 모니터 모드 인터페이스가 원래 이름과 동일)
            print(f"[모니터 모드] 기본 인터페이스 사용: {interface}")
            return interface
                
        except Exception as e:
            print(f"모니터 모드 활성화 오류: {e}")
            return None
    
    def stop_monitor_mode(self, monitor_interface: str):
        """모니터 모드 비활성화"""
        try:
            if monitor_interface:
                subprocess.run(
                    f"echo '{Config.SUDO_PASSWORD}' | sudo -S airmon-ng stop {monitor_interface}",
                    shell=True,
                    capture_output=True,
                    timeout=10
                )
        except Exception as e:
            print(f"모니터 모드 비활성화 오류: {e}")
    
    def scan_wifi(self) -> List[Dict[str, Any]]:
        """실제 WiFi 스캔 수행"""
        print("=" * 50)
        print("[WiFi 스캔 시작]")
        print(f"설정된 인터페이스: {self.interface}")
        print(f"스캔 지속 시간: {self.scan_duration}초")
        
        # 인터페이스 감지
        if not self.interface:
            print("[1단계] WiFi 인터페이스 자동 감지 중...")
            self.interface = self.detect_wifi_interface()
            print(f"감지된 인터페이스: {self.interface}")
        
        if not self.interface:
            print("[오류] WiFi 인터페이스를 찾을 수 없습니다.")
            return []
        
        print(f"[2단계] 사용할 인터페이스: {self.interface}")
        
        # 출력 디렉토리 생성
        os.makedirs(self.scan_output_dir, exist_ok=True)
        print(f"[3단계] 출력 디렉토리: {self.scan_output_dir}")
        
        # 이미 모니터 모드인지 확인
        self.monitor_interface = None
        print("[4단계] 모니터 모드 확인 중...")
        try:
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(f"iwconfig 출력:\n{result.stdout}")
            for line in result.stdout.split('\n'):
                if 'Mode:Monitor' in line:
                    match = re.search(r'^(\w+)\s+', line)
                    if match:
                        self.monitor_interface = match.group(1)
                        print(f"[성공] 이미 모니터 모드 활성화됨: {self.monitor_interface}")
                        break
        except Exception as e:
            print(f"[오류] 모니터 모드 확인 오류: {e}")
        
        # 모니터 모드가 없으면 활성화 시도
        if not self.monitor_interface:
            print("[5단계] 모니터 모드 활성화 시도 중...")
            self.monitor_interface = self.start_monitor_mode(self.interface)
            if self.monitor_interface:
                print(f"[성공] 모니터 모드 활성화: {self.monitor_interface}")
            else:
                print("[오류] 모니터 모드를 활성화할 수 없습니다.")
        
        if not self.monitor_interface:
            print("[오류] 모니터 모드 인터페이스를 찾을 수 없습니다.")
            return []
        
        print(f"[6단계] 사용할 모니터 인터페이스: {self.monitor_interface}")
        
        try:
            # airodump-ng 실행
            output_file = os.path.join(self.scan_output_dir, "scan")
            csv_file = f"{output_file}-01.csv"
            
            print(f"[7단계] airodump-ng 실행 준비")
            print(f"  - 출력 파일: {output_file}")
            print(f"  - 예상 CSV 파일: {csv_file}")
            
            # 기존 파일 삭제
            import glob
            for old_file in glob.glob(f"{output_file}*"):
                try:
                    os.remove(old_file)
                    print(f"  - 기존 파일 삭제: {old_file}")
                except Exception as e:
                    print(f"  - 파일 삭제 실패: {e}")
            
            # airodump-ng 실행 명령어
            cmd = f"echo '{Config.SUDO_PASSWORD}' | sudo -S airodump-ng -w {output_file} --output-format csv {self.monitor_interface}"
            print(f"[8단계] airodump-ng 실행 중...")
            print(f"  - 명령어: airodump-ng -w {output_file} --output-format csv {self.monitor_interface}")
            
            # airodump-ng 실행 (백그라운드, sudo 비밀번호 자동 입력)
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"[9단계] 스캔 대기 중... ({self.scan_duration}초)")
            # 스캔 시간만큼 대기
            time.sleep(self.scan_duration)
            
            print(f"[10단계] airodump-ng 프로세스 종료 중...")
            # 프로세스 종료
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # stderr 확인
            stderr_output = process.stderr.read() if process.stderr else ""
            if stderr_output:
                print(f"[경고] airodump-ng stderr:\n{stderr_output}")
            
            # CSV 파일 찾기
            print(f"[11단계] CSV 파일 확인 중...")
            csv_files = glob.glob(f"{output_file}-*.csv")
            print(f"  - 찾은 CSV 파일: {csv_files}")
            
            if csv_files:
                # 가장 최근 파일 선택
                csv_file = max(csv_files, key=os.path.getmtime)
                print(f"  - 사용할 CSV 파일: {csv_file}")
                print(f"  - 파일 크기: {os.path.getsize(csv_file)} bytes")
            else:
                print(f"[오류] CSV 파일을 찾을 수 없습니다!")
                print(f"  - 검색 경로: {output_file}-*.csv")
                print(f"  - 디렉토리 내용:")
                try:
                    for item in os.listdir(self.scan_output_dir):
                        print(f"    - {item}")
                except Exception as e:
                    print(f"    - 디렉토리 읽기 실패: {e}")
                return []
            
            # CSV 파일 내용 확인 (처음 20줄)
            print(f"[12단계] CSV 파일 내용 확인 (처음 20줄):")
            try:
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    preview_lines = f.readlines()[:20]
                    for i, line in enumerate(preview_lines, 1):
                        print(f"  {i}: {line.strip()[:100]}")
            except Exception as e:
                print(f"  - 파일 읽기 실패: {e}")
            
            # CSV 파일 파싱
            print(f"[13단계] CSV 파일 파싱 중...")
            wifi_list = self.parse_airodump_csv(csv_file)
            print(f"[14단계] 파싱 완료: {len(wifi_list)}개의 WiFi 발견")
            
            for i, wifi in enumerate(wifi_list, 1):
                print(f"  {i}. {wifi.get('ssid', 'N/A')} ({wifi.get('bssid', 'N/A')}) - {wifi.get('protocol', 'N/A')}")
            
            print("=" * 50)
            return wifi_list
            
        except Exception as e:
            print(f"[오류] WiFi 스캔 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            # 모니터 모드는 유지 (다음 스캔을 위해)
            pass
    
    def parse_airodump_csv(self, csv_file: str) -> List[Dict[str, Any]]:
        """airodump-ng CSV 파일 파싱"""
        wifi_list = []
        
        print(f"[CSV 파싱] 파일: {csv_file}")
        
        if not os.path.exists(csv_file):
            print(f"[CSV 파싱 오류] 파일이 존재하지 않습니다: {csv_file}")
            return wifi_list
        
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            print(f"[CSV 파싱] 총 라인 수: {len(lines)}")
            
            # CSV 헤더 찾기
            header_line = None
            data_start = 0
            
            for i, line in enumerate(lines):
                if 'BSSID' in line and 'ESSID' in line:
                    header_line = i
                    data_start = i + 1
                    print(f"[CSV 파싱] 헤더 라인 발견: {i}")
                    print(f"[CSV 파싱] 헤더 내용: {line.strip()}")
                    break
            
            if header_line is None:
                print(f"[CSV 파싱 오류] 헤더를 찾을 수 없습니다.")
                print(f"[CSV 파싱] 첫 10줄:")
                for i, line in enumerate(lines[:10], 1):
                    print(f"  {i}: {line.strip()}")
                return wifi_list
            
            # 헤더 파싱
            header = [h.strip() for h in lines[header_line].split(',')]
            print(f"[CSV 파싱] 헤더 컬럼: {header}")
            
            # 데이터 파싱
            parsed_count = 0
            skipped_count = 0
            
            for line_num, line in enumerate(lines[data_start:], start=data_start+1):
                line = line.strip()
                
                # 빈 줄이나 Station 섹션 시작 시 중단
                if not line or line.startswith('Station'):
                    print(f"[CSV 파싱] 데이터 섹션 종료 (라인 {line_num}): {line[:50]}")
                    break
                
                values = [v.strip() for v in line.split(',')]
                
                if len(values) < 3:  # 최소 BSSID, ESSID, 채널
                    skipped_count += 1
                    continue
                
                # 딕셔너리 생성
                wifi_data = {}
                for i, key in enumerate(header):
                    if i < len(values):
                        wifi_data[key] = values[i]
                
                # 필요한 정보 추출
                bssid = wifi_data.get('BSSID', '').strip()
                essid = wifi_data.get('ESSID', '').strip()
                
                # ESSID가 없거나 숨겨진 네트워크인 경우 처리
                if not bssid:
                    skipped_count += 1
                    continue
                
                if not essid or essid == '':
                    essid = '<Hidden Network>'
                
                # 프로토콜 파싱
                encryption = wifi_data.get('Encryption', '').upper()
                protocol = self.parse_protocol(encryption)
                
                # 채널 파싱
                channel = wifi_data.get('channel', '0')
                try:
                    channel_match = re.search(r'\d+', str(channel))
                    channel = int(channel_match.group()) if channel_match else 0
                except:
                    channel = 0
                
                # 신호 강도 파싱
                power = wifi_data.get('Power', '0')
                try:
                    power_match = re.search(r'-?\d+', str(power))
                    power = int(power_match.group()) if power_match else 0
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
                parsed_count += 1
                print(f"[CSV 파싱] WiFi 발견 ({parsed_count}): {essid} ({bssid}) - {protocol}")
            
            print(f"[CSV 파싱 완료] 파싱: {parsed_count}개, 건너뜀: {skipped_count}개")
            return wifi_list
            
        except Exception as e:
            print(f"[CSV 파싱 오류] {e}")
            import traceback
            traceback.print_exc()
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

