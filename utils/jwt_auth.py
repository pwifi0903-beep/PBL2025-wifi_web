import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Optional, Tuple

def generate_access_token(username: str, secret_key: str) -> str:
    """Access Token 생성 (15분 만료)"""
    payload = {
        'username': username,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=15),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

def generate_refresh_token(username: str, secret_key: str) -> str:
    """Refresh Token 생성 (7일 만료)"""
    payload = {
        'username': username,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, secret_key, algorithm='HS256')

def verify_token(token: str, secret_key: str, token_type: str = 'access') -> Optional[Dict]:
    """JWT 토큰 검증 및 디코딩"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        # 토큰 타입 확인
        if payload.get('type') != token_type:
            return None
            
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_token_from_request() -> Optional[str]:
    """요청에서 JWT 토큰 추출 (쿠키 또는 Authorization 헤더)"""
    # 1. Authorization 헤더에서 추출
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            scheme, token = auth_header.split(' ', 1)
            if scheme.lower() == 'bearer':
                return token
        except ValueError:
            pass
    
    # 2. 쿠키에서 추출
    token = request.cookies.get('access_token')
    if token:
        return token
    
    return None

def get_refresh_token_from_request() -> Optional[str]:
    """요청에서 Refresh Token 추출"""
    # 1. Authorization 헤더에서 추출
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            scheme, token = auth_header.split(' ', 1)
            if scheme.lower() == 'bearer':
                return token
        except ValueError:
            pass
    
    # 2. 쿠키에서 추출
    token = request.cookies.get('refresh_token')
    if token:
        return token
    
    return None

def jwt_required(f):
    """JWT 인증 데코레이터 (JSON 응답용)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from config import Config
        from flask import redirect, url_for
        
        token = get_token_from_request()
        
        if not token:
            # HTML 요청인 경우 리다이렉트
            if request.accept_mimetypes.accept_html:
                return redirect(url_for('expert.login'))
            return jsonify({
                'success': False,
                'error': '토큰이 제공되지 않았습니다.'
            }), 401
        
        payload = verify_token(token, Config.JWT_SECRET_KEY, 'access')
        
        if not payload:
            # HTML 요청인 경우 리다이렉트
            if request.accept_mimetypes.accept_html:
                return redirect(url_for('expert.login'))
            return jsonify({
                'success': False,
                'error': '유효하지 않거나 만료된 토큰입니다.'
            }), 401
        
        # 사용자 정보를 request에 추가
        request.current_user = payload.get('username')
        
        return f(*args, **kwargs)
    
    return decorated_function

