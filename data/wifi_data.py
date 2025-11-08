import random
from typing import List, Dict, Any

class WiFiDataGenerator:
    """와이파이 더미 데이터 생성기"""
    
    def __init__(self):
        self.ssids = [
            "SK_WiFi_GIGA", "KT_GiGA_WiFi", "LG_U+", "Free_WiFi", "Cafe_WiFi",
            "Home_Network", "Office_Secure", "Public_Hotspot", "Guest_Network",
            "WiFi_5G", "MyRouter", "TP-Link", "Netgear", "ASUS_Router",
            "iPhone_Hotspot", "Galaxy_Hotspot", "Mi_WiFi", "Huawei_WiFi"
        ]
        
        self.protocols = {
            "open": {"security_level": "critical", "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"]},
            "wep": {"security_level": "danger", "vulnerabilities": ["WEP 암호화 취약", "WEP 크랙 공격 가능"]},
            "wpa": {"security_level": "warning", "vulnerabilities": ["WPA 암호화 취약", "WPA-TKIP 취약점"]},
            "wpa2": {"security_level": "safe", "vulnerabilities": []},
            "wpa2_wps": {"security_level": "danger", "vulnerabilities": ["WPS 활성화", "WPS 핀 브루트포스", "KRACK 공격 취약"]},
            "wpa3": {"security_level": "safe", "vulnerabilities": []}
        }
        
        self.channels = list(range(1, 14)) + [36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 144, 149, 153, 157, 161, 165]
    
    def generate_bssid(self) -> str:
        """랜덤 BSSID 생성"""
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
    
    def generate_user_wifi_list(self) -> List[Dict[str, Any]]:
        """사용자용 와이파이 목록 생성 (간소화된 정보) - 프로토콜별 고정"""
        wifi_list = []
        
        # 프로토콜별로 하나씩 생성
        protocol_examples = {
            "open": "Free_WiFi",
            "wep": "Old_Router_WEP", 
            "wpa": "Home_WPA_Network",
            "wpa2": "Office_WPA2_Secure",
            "wpa2_wps": "Cafe_WPS_Enabled",
            "wpa3": "Modern_WPA3_Router"
        }
        
        for protocol, example_ssid in protocol_examples.items():
            protocol_info = self.protocols[protocol]
            
            wifi_data = {
                "ssid": example_ssid,
                "protocol": protocol.upper(),
                "security_level": protocol_info["security_level"]
            }
            wifi_list.append(wifi_data)
        
        return wifi_list
    
    def generate_expert_wifi_list(self) -> List[Dict[str, Any]]:
        """관리자용 와이파이 목록 생성 (상세 정보) - 프로토콜별 고정"""
        wifi_list = []
        
        # 프로토콜별로 하나씩 생성 (고정된 BSSID와 채널)
        protocol_examples = {
            "open": {
                "ssid": "Free_WiFi",
                "bssid": "00:11:22:33:44:55",
                "channel": 6
            },
            "wep": {
                "ssid": "Old_Router_WEP", 
                "bssid": "00:11:22:33:44:56",
                "channel": 1
            },
            "wpa": {
                "ssid": "Home_WPA_Network",
                "bssid": "00:11:22:33:44:57",
                "channel": 11
            },
            "wpa2": {
                "ssid": "Office_WPA2_Secure",
                "bssid": "00:11:22:33:44:58",
                "channel": 36
            },
            "wpa2_wps": {
                "ssid": "Cafe_WPS_Enabled",
                "bssid": "00:11:22:33:44:59",
                "channel": 149
            },
            "wpa3": {
                "ssid": "Modern_WPA3_Router",
                "bssid": "00:11:22:33:44:60",
                "channel": 64
            }
        }
        
        for protocol, example_data in protocol_examples.items():
            protocol_info = self.protocols[protocol]
            
            wifi_data = {
                "ssid": example_data["ssid"],
                "bssid": example_data["bssid"],
                "protocol": protocol.upper(),
                "channel": example_data["channel"],
                "security_level": protocol_info["security_level"],
                "vulnerabilities": protocol_info["vulnerabilities"],
                "signal_strength": -50 - (list(protocol_examples.keys()).index(protocol) * 5),  # 약간씩 다른 신호 강도
                "encryption": self._get_encryption_type(protocol)
            }
            wifi_list.append(wifi_data)
        
        return wifi_list
    
    def _get_encryption_type(self, protocol: str) -> str:
        """프로토콜에 따른 암호화 타입 반환"""
        encryption_map = {
            "open": "없음",
            "wep": "WEP",
            "wpa": "WPA-TKIP",
            "wpa2": "WPA2-CCMP",
            "wpa2_wps": "WPA2-CCMP + WPS",
            "wpa3": "WPA3-SAE"
        }
        return encryption_map.get(protocol, "알 수 없음")
    
    def get_security_guide_user(self) -> Dict[str, Any]:
        """사용자용 보안 가이드"""
        return {
            "critical": {
                "title": "매우 위험",
                "color": "#cc0000",
                "protocols": ["OPEN"],
                "description": "극도로 위험한 네트워크입니다. 절대 사용하지 마세요.",
                "recommendations": [
                    "정보가 외부에 노출될 가능성이 매우 높음",
                    "다른 네트워크 사용 권고",
                    "이용시 검색 용도에만 사용 권고"
                ]
            },
            "danger": {
                "title": "위험",
                "color": "#ff4444",
                "protocols": ["WEP"],
                "description": "개인 정보 유출 위험이 매우 높습니다.",
                "recommendations": [
                    "사용하지 마세요",
                    "개인정보 입력 금지",
                    "VPN 사용 권고"
                ]
            },
            "warning": {
                "title": "경고",
                "color": "#ff8800",
                "protocols": ["WPA", "WPA2"],
                "description": "보안 취약점이 있을 수 있습니다.",
                "recommendations": [
                    "신중하게 사용하세요",
                    "중요한 작업은 피하세요",
                    "VPN 사용 권고"
                ]
            },
            "safe": {
                "title": "안전",
                "color": "#44ff44",
                "protocols": ["WPA2", "WPA3"],
                "description": "현재 안전한 프로토콜입니다.",
                "recommendations": [
                    "안전하게 사용 가능",
                    "강력한 패스프레이즈 사용 권고"
                ]
            }
        }
    
    def get_security_guide_expert(self) -> Dict[str, Any]:
        """관리자용 보안 가이드"""
        return {
            "critical": {
                "title": "매우 위험",
                "color": "#cc0000",
                "protocols": ["OPEN"],
                "description": "암호화가 전혀 없는 극도로 위험한 네트워크입니다.",
                "attack_vectors": [
                    "패킷 스니핑 (Packet Sniffing)",
                    "중간자 공격 (MITM)",
                    "데이터 도청 (Eavesdropping)",
                    "네트워크 침입",
                    "세션 하이재킹",
                    "DNS 스푸핑"
                ],
                "recommendations": [
                    "절대 사용 금지",
                    "WPA3 또는 WPA2-Enterprise 사용",
                    "강력한 패스프레이즈 설정",
                    "네트워크 분리 (Network Segmentation)",
                    "VPN 필수 사용"
                ]
            },
            "danger": {
                "title": "위험",
                "color": "#ff4444",
                "protocols": ["WEP"],
                "description": "심각한 보안 취약점이 존재합니다.",
                "attack_vectors": [
                    "패킷 스니핑",
                    "중간자 공격 (MITM)",
                    "데이터 도청",
                    "네트워크 침입"
                ],
                "recommendations": [
                    "WPA3 또는 WPA2-Enterprise 사용",
                    "강력한 패스프레이즈 설정",
                    "WPS 비활성화",
                    "정기적인 보안 업데이트"
                ]
            },
            "warning": {
                "title": "경고",
                "color": "#ff8800",
                "protocols": ["WPA", "WPA2"],
                "description": "알려진 취약점이 존재합니다.",
                "attack_vectors": [
                    "KRACK 공격 (WPA2)",
                    "WPS 핀 브루트포스",
                    "WPA-TKIP 취약점",
                    "사전 공격 (Dictionary Attack)"
                ],
                "recommendations": [
                    "WPA3으로 업그레이드",
                    "WPS 비활성화",
                    "강력한 패스프레이즈 사용",
                    "MAC 주소 필터링 고려"
                ]
            },
            "safe": {
                "title": "안전",
                "color": "#44ff44",
                "protocols": ["WPA2", "WPA3"],
                "description": "현재 안전한 무선 보안 프로토콜입니다.",
                "attack_vectors": [],
                "recommendations": [
                    "CCMP 암호화 사용 (WPA2)",
                    "SAE 사용 권고 (WPA3)",
                    "강력한 패스프레이즈 유지",
                    "정기적인 펌웨어 업데이트",
                    "WPS 기능 비활성화 권고"
                ]
            }
        }

# 전역 인스턴스
wifi_generator = WiFiDataGenerator()
