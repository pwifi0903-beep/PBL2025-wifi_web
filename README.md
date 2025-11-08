# WiSafe - WiFi 보안 스캐너

WiFi 네트워크의 보안 취약점을 탐지하고 분석하는 웹 애플리케이션입니다.

## 🚀 실행 방법

### 1. 가상환경 생성
h
# Python 가상환경 생성
python -m venv venv

# Windows PowerShell에서 가상환경 활성화
.\venv\Scripts\Activate.ps1

# Windows CMD에서 가상환경 활성화
venv\Scripts\activate.bat

# Linux/Mac에서 가상환경 활성화
source venv/bin/activate### 2. 의존성 설치
ash
# requirements.txt에 있는 패키지 설치
pip install -r requirements.txt### 3. 애플리케이션 실행

# Flask 애플리케이션 실행
python app.py서버가 실행되면 브라우저에서 `http://localhost:5000` 또는 `http://127.0.0.1:5000`으로 접속하세요.

## 📋 주요 기능

### 1. 랜딩 페이지 (`/`)
- 서비스 소개
- 일반인용 페이지와 전문가용 페이지로 이동하는 버튼 제공

### 2. 일반인용 페이지 (`/user`)
- **좌측 패널**: 프로토콜별 보안 가이드
  - 위험 수준별 색상 구분 (매우 위험/위험/경고/안전)
  - 일반인이 이해하기 쉬운 보안 권고사항 제공
- **우측 패널**: WiFi 네트워크 목록
  - WiFi명 (SSID)
  - 보안 프로토콜 (OPEN, WEP, WPA, WPA2, WPA3 등)
  - 보안 수준 표시

### 3. 전문가용 페이지 (`/expert`)
- **로그인 필요**: ID `admin`, PW `admin`
- **좌측 패널**: 상세 보안 가이드
  - 각 프로토콜별 취약한 공격 유형 설명
  - 전문가 수준의 보안 권고사항
- **우측 패널**: 상세 WiFi 네트워크 목록
  - WiFi명 (SSID)
  - BSSID (MAC 주소)
  - 보안 프로토콜
  - 채널 정보
  - 보안 수준
- **상세 정보**: WiFi 클릭 시
  - 취약한 공격 목록 표시
  - 전문가 수준의 권고사항 제공
  - 보안 점검 기능

### 4. WiFi 스캔 시뮬레이션
- 실제 WiFi 어댑터 없이도 다양한 보안 프로토콜의 WiFi 네트워크를 시뮬레이션
- 일반인용과 전문가용 각각 다른 수준의 정보 제공

## 🛠 기술 스택

- **Backend**: Python 3.11, Flask 2.3.3
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **데이터**: 로컬 시뮬레이션 데이터
