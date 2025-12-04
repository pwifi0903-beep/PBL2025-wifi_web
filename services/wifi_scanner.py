import subprocess
import re
from typing import List, Dict, Any, Optional
from config import Config


class WiFiScanner:
    """nmcli를 사용한 빠른 WiFi 스캔 서비스"""
    
    def __init__(self, interface: Optional[str] = None, scan_duration: int = 15):
        """
        Args:
            interface: WiFi 어댑터 인터페이스 (nmcli는 자동 감지하므로 무시됨)
            scan_duration: 스캔 지속 시간 (nmcli는 즉시 반환하므로 무시됨)
        """
        self.interface = interface
        self.max_results = 15  # 최대 결과 개수
        
    def scan_wifi(self) -> List[Dict[str, Any]]:
        """WiFi 스캔 수행 (nmcli 사용)"""
        print("=" * 60)
        print("[WiFi 스캔 시작 - nmcli 방식]")
        
        try:
            # nmcli를 사용한 WiFi 스캔
            print(f"[1단계] nmcli로 WiFi 스캔 중...")
            
            # nmcli device wifi list 실행
            # -t: 파싱하기 쉬운 형식
            # -f: 필요한 필드만 선택 (SSID, BSSID, CHAN, SIGNAL, SECURITY)
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'SSID,BSSID,CHAN,SIGNAL,SECURITY', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                print(f"[오류] nmcli 실행 실패: {result.stderr}")
                return []
            
            print(f"[2단계] nmcli 스캔 완료")
            
            # 결과 파싱
            wifi_list = self.parse_nmcli_output(result.stdout)
            
            # 최대 15개로 제한
            wifi_list = wifi_list[:self.max_results]
            
            print(f"[3단계] 파싱 완료: {len(wifi_list)}개의 WiFi 발견")
            
            if wifi_list:
                for i, wifi in enumerate(wifi_list, 1):
                    print(f"  {i}. {wifi.get('ssid', 'N/A')} ({wifi.get('bssid', 'N/A')}) - {wifi.get('protocol', 'N/A')} - {wifi.get('signal_strength', 0)}dBm")
            else:
                print(f"  - 발견된 WiFi가 없습니다.")
            
            print("=" * 60)
            return wifi_list
            
        except subprocess.TimeoutExpired:
            print(f"[오류] nmcli 실행 시간 초과")
            return []
        except FileNotFoundError:
            print(f"[오류] nmcli가 설치되어 있지 않습니다.")
            print(f"  - 설치: sudo apt-get install network-manager")
            return []
        except Exception as e:
            print(f"[오류] WiFi 스캔 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def parse_nmcli_output(self, output: str) -> List[Dict[str, Any]]:
        """nmcli 출력 파싱"""
        wifi_list = []
        
        lines = output.strip().split('\n')
        print(f"[파싱] 총 {len(lines)}줄")
        
        for line in lines:
            if not line.strip():
                continue
            
            # nmcli -t 형식: SSID:BSSID:CHAN:SIGNAL:SECURITY
            # 예: MyWiFi:AA:BB:CC:DD:EE:FF:1:75:WPA2
            parts = line.split(':')
            
            # BSSID는 콜론으로 구분되므로 최소 8개 파트 필요
            # parts[0]: SSID
            # parts[1:7]: BSSID (6개)
            # parts[7]: CHAN
            # parts[8]: SIGNAL
            # parts[9:]: SECURITY (여러 개일 수 있음)
            
            if len(parts) < 9:
                continue
            
            ssid = parts[0]
            bssid = ':'.join(parts[1:7])  # BSSID 재조립
            channel = parts[7]
            signal = parts[8]
            security = ':'.join(parts[9:]) if len(parts) > 9 else ''
            
            # SSID 필터링 (빈 SSID는 숨겨진 네트워크)
            if not ssid:
                ssid = '<Hidden Network>'
            
            # BSSID 검증
            if not re.match(r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$', bssid):
                continue
            
            # 채널 파싱
            try:
                channel_num = int(channel) if channel.isdigit() else 0
            except:
                channel_num = 0
            
            # 신호 강도 파싱
            try:
                signal_strength = int(signal) if signal.lstrip('-').isdigit() else 0
            except:
                signal_strength = 0
            
            # 프로토콜 파싱
            protocol = self.parse_protocol(security)
            
            # 보안 수준 결정
            security_level = self.get_security_level(protocol)
            
            # 취약점 목록
            vulnerabilities = self.get_vulnerabilities(protocol)
            
            wifi_info = {
                'ssid': ssid,
                'bssid': bssid,
                'protocol': protocol,
                'channel': channel_num,
                'signal_strength': signal_strength,
                'security_level': security_level,
                'vulnerabilities': vulnerabilities,
                'encryption': security,
                'is_real_scan': True
            }
            
            wifi_list.append(wifi_info)
        
        print(f"[파싱] {len(wifi_list)}개 WiFi 파싱 완료")
        return wifi_list
    
    def parse_protocol(self, security: str) -> str:
        """보안 정보에서 프로토콜 추출"""
        security_upper = security.upper()
        
        if not security or security == '--' or 'NONE' in security_upper:
            return 'OPEN'
        elif 'WPA3' in security_upper:
            return 'WPA3'
        elif 'WPA2' in security_upper:
            if 'WPS' in security_upper:
                return 'WPA2_WPS'
            return 'WPA2'
        elif 'WPA' in security_upper:
            return 'WPA'
        elif 'WEP' in security_upper:
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
