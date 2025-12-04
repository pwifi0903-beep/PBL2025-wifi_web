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
        
        # Rogue AP 시나리오 추가: 같은 SSID를 가진 WiFi (WPA2와 OPEN)
        rogue_ap_ssid = "Cafe_WiFi"
        
        # 정상 WiFi (WPA2)
        wifi_list.append({
            "ssid": rogue_ap_ssid,
            "protocol": "WPA2",
            "security_level": "safe"
        })
        
        # Rogue AP (OPEN) - 같은 SSID
        wifi_list.append({
            "ssid": rogue_ap_ssid,
            "protocol": "OPEN",
            "security_level": "critical"
        })
        
        # SWU WiFi 데이터 추가 (사용자용 간소화)
        swu_wifi_user = self._generate_swu_wifi_user()
        wifi_list.extend(swu_wifi_user)
        
        return wifi_list
    
    def _generate_swu_wifi_user(self) -> List[Dict[str, Any]]:
        """SWU WiFi 사용자용 데이터 생성 - TP-LINK 먼저, 나머지는 섞어서"""
        result_list = []
        
        # TP-LINK_AD43 (OPEN) - Cafe_WiFi 바로 다음에 표시 (맨 위)
        result_list.append({
            "ssid": "TP-LINK_AD43",
            "protocol": "OPEN",
            "security_level": "critical",
            "is_new_data": True
        })
        
        # TP-LINK_AD43 (WPA2) - KRACK 취약 (두 번째)
        result_list.append({
            "ssid": "TP-LINK_AD43",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True,
            "krack_vulnerable": True
        })
        
        # 나머지 데이터는 섞어서 배치
        # SWU_WiFi(Auth)_5G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_5G",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "protocol": "OPEN",
            "security_level": "critical",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_2.4G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_2.4G",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True
        })
        
        # DIRECT-11 C56x Series (WPA2 PSK)
        result_list.append({
            "ssid": "DIRECT-11 C56x Series",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth) (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)",
            "protocol": "WPA2",
            "security_level": "safe",
            "is_new_data": True
        })
        
        return result_list
    
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
        
        # Rogue AP 시나리오 추가: 같은 SSID를 가진 WiFi (WPA2와 OPEN)
        rogue_ap_ssid = "Cafe_WiFi"
        
        # 정상 WiFi (WPA2)
        wifi_list.append({
            "ssid": rogue_ap_ssid,
            "bssid": "00:11:22:33:44:70",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -55,
            "encryption": "WPA2-CCMP"
        })
        
        # Rogue AP (OPEN) - 같은 SSID
        wifi_list.append({
            "ssid": rogue_ap_ssid,
            "bssid": "00:11:22:33:44:71",
            "protocol": "OPEN",
            "channel": 6,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -60,
            "encryption": "없음"
        })
        
        # SWU WiFi 데이터 추가 (관리자용 상세)
        swu_wifi_expert = self._generate_swu_wifi_expert()
        wifi_list.extend(swu_wifi_expert)
        
        return wifi_list
    
    def _generate_swu_wifi_expert(self) -> List[Dict[str, Any]]:
        """SWU WiFi 관리자용 상세 데이터 생성 - TP-LINK 먼저, 나머지는 섞어서"""
        result_list = []
        
        # TP-LINK_AD43 (OPEN) - Cafe_WiFi 바로 다음에 표시 (맨 위)
        result_list.append({
            "ssid": "TP-LINK_AD43",
            "bssid": "98:DE:D0:C4:AD:43",
            "protocol": "OPEN",
            "channel": 6,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -21,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # TP-LINK_AD43 (WPA2) - KRACK 취약 (두 번째)
        result_list.append({
            "ssid": "TP-LINK_AD43",
            "bssid": "98:DE:D0:C4:AD:44",
            "protocol": "WPA2",
            "channel": 6,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -21,
            "encryption": "WPA2-CCMP",
            "is_new_data": True,
            "krack_vulnerable": True
        })
        
        # 나머지 데이터는 섞어서 배치 (고정된 섞인 순서)
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "60:10:9E:C0:8C:13",
            "protocol": "OPEN",
            "channel": 11,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -40,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_5G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_5G",
            "bssid": "60:10:9E:C0:8C:12",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -39,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "bssid": "60:10:9E:C0:8C:14",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -41,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_2.4G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_2.4G",
            "bssid": "60:10:9E:C0:8C:11",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -41,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "F8:B1:32:BD:C1:63",
            "protocol": "OPEN",
            "channel": 1,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -65,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth) (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)",
            "bssid": "60:10:9E:C0:8C:10",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -41,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "bssid": "60:10:9E:C0:C5:34",
            "protocol": "WPA2",
            "channel": 6,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -68,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "60:10:9E:C0:C5:33",
            "protocol": "OPEN",
            "channel": 6,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -67,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "bssid": "60:10:9E:C0:BB:B4",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -77,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_5G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_5G",
            "bssid": "60:10:9E:C0:BB:B2",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -77,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "60:10:9E:C0:BB:B3",
            "protocol": "OPEN",
            "channel": 11,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -75,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth) (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)",
            "bssid": "60:10:9E:C0:BB:B0",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -77,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "bssid": "60:10:9E:C0:87:B4",
            "protocol": "WPA2",
            "channel": 6,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -69,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "60:10:9E:C0:87:B3",
            "protocol": "OPEN",
            "channel": 6,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -70,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_2.4G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_2.4G",
            "bssid": "60:10:9E:C0:BB:B1",
            "protocol": "WPA2",
            "channel": 11,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -77,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # DIRECT-11 C56x Series (WPA2 PSK)
        result_list.append({
            "ssid": "DIRECT-11 C56x Series",
            "bssid": "86:25:19:C7:DD:11",
            "protocol": "WPA2",
            "channel": 1,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -85,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth) (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)",
            "bssid": "C4:34:5B:FA:7C:10",
            "protocol": "WPA2",
            "channel": 1,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -82,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # SWU_WiFi_Help (OPEN)
        result_list.append({
            "ssid": "SWU_WiFi_Help",
            "bssid": "C4:34:5B:FA:7C:13",
            "protocol": "OPEN",
            "channel": 1,
            "security_level": "critical",
            "vulnerabilities": ["무제한 접근", "데이터 도청 위험", "중간자 공격 가능", "패킷 스니핑 위험"],
            "signal_strength": -82,
            "encryption": "없음",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_5G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_5G",
            "bssid": "C4:34:5B:FA:7C:12",
            "protocol": "WPA2",
            "channel": 1,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -78,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        # swu-vrlab (WPA2 PSK)
        result_list.append({
            "ssid": "swu-vrlab",
            "bssid": "C4:34:5B:FA:7C:14",
            "protocol": "WPA2",
            "channel": 1,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -80,
            "encryption": "WPA2-CCMP",
            "auth_type": "PSK",
            "is_new_data": True
        })
        
        # SWU_WiFi(Auth)_2.4G (WPA2 MGT)
        result_list.append({
            "ssid": "SWU_WiFi(Auth)_2.4G",
            "bssid": "C4:34:5B:FA:7C:11",
            "protocol": "WPA2",
            "channel": 1,
            "security_level": "safe",
            "vulnerabilities": [],
            "signal_strength": -82,
            "encryption": "WPA2-CCMP",
            "auth_type": "MGT",
            "is_new_data": True
        })
        
        return result_list
    
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
