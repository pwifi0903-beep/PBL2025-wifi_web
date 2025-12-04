# WiSAFE - WiFi 보안 분석 플랫폼

WiFi 네트워크의 보안 취약점을 실시간으로 탐지, 분석, 점검하는 전문 보안 플랫폼입니다.

## 📋 주요 기능

### 1. 실시간 WiFi 스캔

**airodump-ng 기반 실제 스캔**
- 주변 WiFi 네트워크 실시간 탐지
- 모니터 모드 자동 활성화 (airmon-ng)
- 최대 15개 WiFi 발견 시 조기 종료 (1-3초 내 완료)
- 상세 정보 수집:
  - SSID (네트워크 이름)
  - BSSID (MAC 주소)
  - 채널 (Channel)
  - 신호 강도 (Signal Strength)
  - 암호화 프로토콜 (OPEN, WEP, WPA, WPA2, WPA3)

### 2. 프로토콜별 크래킹

**실제 공격 도구 기반 취약점 분석**

#### WEP 크래킹
- aircrack-ng 기반 통계적 크래킹
- IV(Initialization Vector) 수집 및 분석
- 실시간 진행 상황 표시

#### WPA/WPA2 크래킹
- 4-way 핸드셰이크 캡처
- wordlist 기반 사전 공격 (rockyou.txt)
- **KRACK (Key Reinstallation Attack) 취약점 분석**
- WPA2의 4-way 핸드셰이크 재설치 공격

#### WPS 크래킹
- reaver/bully를 통한 핀 브루트포스
- WPS 핀 기반 비밀번호 복구
- Pixie Dust 공격 지원

**실시간 크래킹 모니터링**
- Server-Sent Events(SSE) 기반 실시간 진행 상황
- 진행률, 시도 횟수, 예상 시간 표시
- 크래킹 성공 시 비밀번호 즉시 표시

### 3. 보안 점검 및 분석

**프로토콜별 취약점 분석**
- OPEN: 무제한 접근, 데이터 도청, 중간자 공격
- WEP: 암호화 취약점, 빠른 크래킹 가능
- WPA: TKIP 취약점, 사전 공격 취약
- WPA2: KRACK 공격 취약점
- WPA2_WPS: WPS 핀 브루트포스 취약
- WPA3: 현재 안전

**위험도 평가**
- Critical (치명적): OPEN 네트워크
- Danger (위험): WEP, WPA2_WPS
- Warning (경고): WPA
- Safe (안전): WPA2, WPA3

**구체적인 보안 권고사항 제공**

### 4. 사용자 모드

**일반인용 모드 (`/user`)**
- 쉬운 용어로 설명된 보안 가이드
- WiFi 프로토콜별 위험 수준 색상 표시
- 이해하기 쉬운 보안 권고사항

**전문가용 모드 (`/expert`)**
- JWT 인증 기반 접근 제어
- 상세한 기술 정보 (BSSID, 채널 등)
- 실제 크래킹 기능 제공
- 프로토콜별 공격 방법 상세 설명
- 실시간 보안 점검 결과

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────┐
│   Frontend (HTML/CSS/JavaScript)   │
│  ┌──────────┬──────────┬──────────┐ │
│  │ Landing  │   User   │  Expert  │ │
│  │   Page   │   Mode   │   Mode   │ │
│  └──────────┴──────────┴──────────┘ │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Flask Blueprints             │
│  ┌──────────┬──────────┬──────────┐ │
│  │ main_bp  │ user_bp  │expert_bp │ │
│  │   (/)    │ (/user)  │(/expert) │ │
│  │          │          │+ JWT Auth│ │
│  └──────────┴──────────┴──────────┘ │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Services Layer              │
│  ┌─────────────────────────────────┐│
│  │  WiFiScanner (airodump-ng)      ││
│  │  - 실시간 스캔                   ││
│  │  - 모니터 모드 관리              ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  CrackingService                ││
│  │  - WEP/WPA/WPA2/WPS 크래킹      ││
│  │  - 실시간 진행 상황 스트리밍     ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │  SecurityCheckService           ││
│  │  - 취약점 분석                   ││
│  │  - 보안 권고사항 생성            ││
│  └─────────────────────────────────┘│
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│    System Tools (Linux/Kali)       │
│  ┌─────────────────────────────────┐│
│  │  airmon-ng  (모니터 모드)        ││
│  │  airodump-ng (WiFi 스캔)         ││
│  │  aircrack-ng (크래킹)            ││
│  │  reaver/bully (WPS 공격)         ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

## 🚀 실행 방법

### 필수 요구사항

**운영체제**
- Linux (Ubuntu, Kali Linux 권장)

**WiFi 어댑터**
- 모니터 모드를 지원하는 무선 어댑터 필요
- 권장: Alfa AWUS036ACH, TP-Link TL-WN722N v1

**시스템 도구**
```bash
# aircrack-ng suite 설치
sudo apt-get update
sudo apt-get install aircrack-ng

# WPS 크래킹 도구 설치 (선택)
sudo apt-get install reaver pixiewps
```

### 1. 가상환경 생성 및 활성화

```bash
# Python 가상환경 생성
python3 -m venv venv

# Linux/Mac에서 가상환경 활성화
source venv/bin/activate
```

### 2. 의존성 설치

```bash
# requirements.txt에 있는 패키지 설치
pip install -r requirements.txt
```

### 3. 설정 파일 수정

`config.py` 파일을 열어 다음 설정을 수정하세요:

```python
class Config:
    # sudo 비밀번호 (모니터 모드 활성화 및 스캔에 필요)
    SUDO_PASSWORD = "your_sudo_password"
    
    # WiFi 인터페이스 (wlan0, wlan1 등)
    WIFI_INTERFACE = "wlan0"
    
    # 스캔 지속 시간 (초, 최대 15개 발견 시 조기 종료)
    WIFI_SCAN_DURATION = 5
```

### 4. 애플리케이션 실행

```bash
# sudo 권한으로 실행 (모니터 모드 활성화 필요)
sudo python3 app.py
```

서버가 실행되면 브라우저에서 접속하세요:
- **일반인용**: `http://localhost:5000/user`
- **전문가용**: `http://localhost:5000/expert`

### 로그인 정보 (전문가 모드)

- **ID**: `admin`
- **PW**: `admin`

> ⚠️ **보안 경고**: 프로덕션 환경에서는 반드시 강력한 비밀번호로 변경하세요.

## 🛠 기술 스택

**Backend**
- Python 3.11
- Flask 2.3.3
- JWT 인증 (PyJWT 2.8.0)

**Frontend**
- HTML5, CSS3
- Vanilla JavaScript
- Server-Sent Events (실시간 통신)

**보안 도구**
- aircrack-ng suite (스캔 및 크래킹)
- reaver/bully (WPS 공격)

## 🔐 인증 시스템

**JWT 기반 인증**
- Access Token: 15분 (API 요청 인증)
- Refresh Token: 7일 (토큰 자동 갱신)
- 자동 토큰 갱신으로 끊김 없는 사용
- 전문가 모드 접근 제한

## ⚠️ 법적 고지

이 도구는 **교육 및 보안 연구 목적**으로만 제작되었습니다.

**주의사항:**
- 본인이 소유하거나 명시적인 허가를 받은 네트워크에만 사용하세요
- 무단으로 타인의 WiFi 네트워크를 스캔하거나 공격하는 것은 불법입니다
- 이 도구의 부적절한 사용으로 인한 법적 책임은 사용자에게 있습니다

**합법적 사용 예:**
- 본인 소유의 WiFi 네트워크 보안 점검
- 허가받은 펜테스팅(Penetration Testing)
- 보안 교육 및 연구

## 📁 프로젝트 구조

```
PBL2025-wifi_web/
├── app.py                  # Flask 애플리케이션 진입점
├── config.py               # 설정 파일
├── requirements.txt        # Python 의존성
│
├── blueprints/            # Flask Blueprint
│   ├── main.py            # 랜딩 페이지
│   ├── user.py            # 일반인용 페이지
│   └── expert.py          # 전문가용 페이지 + JWT
│
├── services/              # 핵심 서비스
│   ├── wifi_scanner.py    # WiFi 스캔 (airodump-ng)
│   ├── cracking_service.py # 크래킹 (aircrack-ng, reaver)
│   └── security_check.py  # 보안 점검 및 분석
│
├── utils/                 # 유틸리티
│   └── jwt_auth.py        # JWT 인증
│
├── templates/             # HTML 템플릿
│   ├── landing.html
│   ├── user.html
│   ├── expert.html
│   └── login.html
│
├── static/                # 정적 파일
│   ├── css/
│   └── js/
│
└── cap_files/             # 패킷 캡처 파일 저장소
```

## 📝 개발 정보

**개발 목적**: 교육용 WiFi 보안 분석 플랫폼

**주요 학습 목표**:
- WiFi 보안 프로토콜 이해
- 네트워크 취약점 분석
- 실전 보안 도구 활용
- 웹 기반 보안 플랫폼 개발
