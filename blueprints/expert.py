from flask import Blueprint, render_template, jsonify, request, redirect, url_for, make_response
from data.wifi_data import wifi_generator
from services.security_check import security_service
from utils.jwt_auth import (
    generate_access_token, 
    generate_refresh_token, 
    verify_token,
    get_token_from_request,
    get_refresh_token_from_request,
    jwt_required
)
from config import Config

expert_bp = Blueprint('expert', __name__)

def login_required(f):
    """로그인 필수 데코레이터 (JWT 기반)"""
    @jwt_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@expert_bp.route('/expert/login', methods=['GET', 'POST'])
def login():
    """관리자 로그인 페이지"""
    if request.method == 'POST':
        # JSON 요청 처리 (AJAX)
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            # 폼 데이터 처리
            username = request.form.get('username')
            password = request.form.get('password')
        
        # 인증 확인
        if username == 'admin' and password == 'admin':
            # JWT 토큰 생성
            access_token = generate_access_token(username, Config.JWT_SECRET_KEY)
            refresh_token = generate_refresh_token(username, Config.JWT_SECRET_KEY)
            
            # JSON 응답 (AJAX 요청인 경우)
            if request.is_json:
                response = make_response(jsonify({
                    'success': True,
                    'message': '로그인 성공',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }))
                # 쿠키에도 토큰 저장 (HTML 페이지 접근을 위해)
                response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax', max_age=900)  # 15분
                response.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax', max_age=604800)  # 7일
                return response, 200
            
            # 폼 제출인 경우 쿠키에 토큰 저장 후 리다이렉트
            response = make_response(redirect(url_for('expert.expert_page')))
            response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax', max_age=900)  # 15분
            response.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax', max_age=604800)  # 7일
            return response
        else:
            # 인증 실패
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': '잘못된 사용자명 또는 비밀번호입니다.'
                }), 401
            else:
                return render_template('login.html', error='잘못된 사용자명 또는 비밀번호입니다.')
    
    return render_template('login.html')

@expert_bp.route('/expert')
@login_required
def expert_page():
    """관리자용 페이지"""
    security_guide = wifi_generator.get_security_guide_expert()
    return render_template('expert.html', security_guide=security_guide)

@expert_bp.route('/api/expert/scan', methods=['POST'])
@login_required
def expert_scan_wifi():
    """관리자용 와이파이 스캔 API"""
    try:
        wifi_list = wifi_generator.generate_expert_wifi_list()
        return jsonify({
            'success': True,
            'wifi_list': wifi_list,
            'count': len(wifi_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@expert_bp.route('/api/expert/security-check', methods=['POST'])
@login_required
def security_check():
    """보안 점검 API"""
    try:
        data = request.get_json()
        protocol = data.get('protocol')
        
        if not protocol:
            return jsonify({
                'success': False,
                'error': '프로토콜 정보가 필요합니다.'
            }), 400
        
        result = security_service.simulate_security_check(protocol)
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@expert_bp.route('/expert/logout', methods=['POST', 'GET'])
def logout():
    """로그아웃"""
    response = make_response(redirect(url_for('main.landing')))
    
    # 쿠키에서 토큰 삭제
    response.set_cookie('access_token', '', expires=0)
    response.set_cookie('refresh_token', '', expires=0)
    
    # JSON 응답 (AJAX 요청인 경우)
    if request.is_json or request.method == 'POST':
        return jsonify({
            'success': True,
            'message': '로그아웃되었습니다.'
        }), 200
    
    return response

@expert_bp.route('/api/expert/refresh', methods=['POST'])
def refresh_token():
    """Refresh Token으로 Access Token 갱신"""
    refresh_token_value = get_refresh_token_from_request()
    
    if not refresh_token_value:
        return jsonify({
            'success': False,
            'error': 'Refresh Token이 제공되지 않았습니다.'
        }), 401
    
    payload = verify_token(refresh_token_value, Config.JWT_SECRET_KEY, 'refresh')
    
    if not payload:
        return jsonify({
            'success': False,
            'error': '유효하지 않거나 만료된 Refresh Token입니다.'
        }), 401
    
    # 새로운 Access Token 생성
    username = payload.get('username')
    new_access_token = generate_access_token(username, Config.JWT_SECRET_KEY)
    
    response = jsonify({
        'success': True,
        'access_token': new_access_token
    })
    
    # 쿠키에 새 Access Token 저장
    response.set_cookie('access_token', new_access_token, httponly=True, secure=False, samesite='Lax', max_age=900)
    
    return response

@expert_bp.route('/api/expert/verify', methods=['GET'])
@jwt_required
def verify():
    """토큰 유효성 검증"""
    return jsonify({
        'success': True,
        'message': '토큰이 유효합니다.',
        'username': getattr(request, 'current_user', None)
    }), 200
