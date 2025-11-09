# WiSAFE - WiFi 보안 스캐너

WiFi 네트워크의 보안 취약점을 탐지하고 분석하는 웹 애플리케이션입니다.

## 🚀 실행 방법

### 1. 가상환경 생성

```bash
# Python 가상환경 생성
python -m venv venv

# Windows PowerShell에서 가상환경 활성화
.\venv\Scripts\Activate.ps1

# Windows CMD에서 가상환경 활성화
venv\Scripts\activate.bat

# Linux/Mac에서 가상환경 활성화
source venv/bin/activate
```

### 2. 의존성 설치

```bash
# requirements.txt에 있는 패키지 설치
pip install -r requirements.txt
```

### 3. 애플리케이션 실행

```bash
# Flask 애플리케이션 실행
python app.py
```

서버가 실행되면 브라우저에서 `http://localhost:5000` 또는 `http://127.0.0.1:5000`으로 접속하세요.

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
- **인증**: JWT (PyJWT 2.8.0, cryptography 41.0.7)
- **데이터**: 로컬 시뮬레이션 데이터

## 🔐 인증 시스템 (JWT)

### JWT 인증이란?

WiSAFE는 전문가용 페이지 접근을 위해 **JWT (JSON Web Token)** 기반 인증 시스템을 사용합니다. 이는 기존 세션 기반 인증보다 보안성이 높고 확장 가능한 인증 방식입니다.

### 왜 JWT를 사용하나요?

1. **보안 강화**
   - 세션 하이재킹 공격 방지
   - 서버 측 세션 저장소 불필요
   - 토큰 기반 무상태(Stateless) 인증

2. **확장성**
   - 서버 간 세션 공유 불필요
   - 마이크로서비스 아키텍처에 적합
   - 로드 밸런싱 환경에서 유리

3. **사용자 경험**
   - 자동 토큰 갱신으로 끊김 없는 서비스
   - 모바일 앱 연동 용이

### 인증 구조

#### 1. Access Token (접근 토큰)
- **만료 시간**: 15분
- **용도**: API 요청 시 인증
- **저장 위치**: 
  - HTTP-only 쿠키 (서버에서 설정)
  - localStorage (클라이언트에서 관리)
- **전송 방식**: `Authorization: Bearer <token>` 헤더

#### 2. Refresh Token (갱신 토큰)
- **만료 시간**: 7일
- **용도**: Access Token 갱신
- **저장 위치**: localStorage
- **보안**: Access Token보다 긴 만료 시간으로 사용자 편의성 제공

#### 3. 토큰 갱신 프로세스
1. Access Token 만료 시 자동으로 Refresh Token 사용
2. `/api/expert/refresh` 엔드포인트로 새 Access Token 발급
3. Refresh Token도 만료된 경우 로그인 페이지로 리다이렉트

### 인증 흐름

```
1. 로그인 요청 (/expert/login)
   ↓
2. 서버에서 Access Token + Refresh Token 발급
   ↓
3. 클라이언트에 토큰 저장 (localStorage 또는 쿠키)
   ↓
4. 이후 모든 API 요청에 Access Token 포함
   ↓
5. Access Token 만료 시 자동으로 Refresh Token으로 갱신
```

### 보안 기능

- **토큰 서명**: HS256 알고리즘으로 토큰 무결성 보장
- **만료 시간 검증**: 자동으로 만료된 토큰 거부
- **자동 갱신**: 사용자 개입 없이 토큰 갱신
- **401 응답 처리**: 인증 실패 시 자동 로그인 페이지 이동

### 로그인 정보

**전문가용 페이지 접근:**
- ID: `admin`
- PW: `admin`

> **참고**: 프로덕션 환경에서는 반드시 강력한 비밀번호와 JWT_SECRET_KEY를 사용하세요.
