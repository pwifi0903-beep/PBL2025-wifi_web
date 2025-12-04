from flask import Blueprint, render_template, jsonify, request, redirect, url_for, make_response, Response
from data.wifi_data import wifi_generator
from services.security_check import security_service
from services.wifi_scanner import wifi_scanner
from services.cracking_service import cracking_service
from utils.jwt_auth import (
    generate_access_token, 
    generate_refresh_token, 
    verify_token,
    get_token_from_request,
    get_refresh_token_from_request,
    jwt_required
)
from config import Config
import json

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
    """관리자용 와이파이 스캔 API (더미 데이터 + 실제 스캔)"""
    try:
        # 더미 데이터 생성
        dummy_wifi_list = wifi_generator.generate_expert_wifi_list()
        
        # 실제 WiFi 스캔 수행
        try:
            scanner = wifi_scanner.__class__(
                interface=Config.WIFI_INTERFACE,
                scan_duration=Config.WIFI_SCAN_DURATION
            )
            real_wifi_list = scanner.scan_wifi()
            
            # 더미 데이터와 실제 스캔 데이터 병합
            merged_wifi_list = scanner.merge_with_dummy(real_wifi_list, dummy_wifi_list)
        except Exception as scan_error:
            # 실제 스캔 실패 시 더미 데이터만 반환
            print(f"실제 WiFi 스캔 실패: {scan_error}")
            merged_wifi_list = dummy_wifi_list
        
        return jsonify({
            'success': True,
            'wifi_list': merged_wifi_list,
            'count': len(merged_wifi_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@expert_bp.route('/api/expert/security-check', methods=['POST'])
@login_required
def security_check():
    """보안 점검 API (크래킹 시작)"""
    try:
        data = request.get_json()
        wifi_data = data.get('wifi_data')
        protocol = data.get('protocol')
        
        if not wifi_data and not protocol:
            return jsonify({
                'success': False,
                'error': 'WiFi 정보 또는 프로토콜 정보가 필요합니다.'
            }), 400
        
        # 프로토콜 추출
        if not protocol and wifi_data:
            protocol = wifi_data.get('protocol', '')
        
        # OPEN 프로토콜은 크래킹 불필요
        if protocol and protocol.upper() == 'OPEN':
            return jsonify({
                'success': False,
                'error': 'OPEN 네트워크는 크래킹이 불필요합니다.'
            }), 400
        
        # 크래킹 시작
        if wifi_data:
            cracking_id = cracking_service.start_cracking(
                wifi_data,
                interface=Config.WIFI_INTERFACE
            )
            
            return jsonify({
                'success': True,
                'cracking_id': cracking_id,
                'message': '크래킹을 시작했습니다.'
            })
        else:
            # WiFi 데이터가 없으면 시뮬레이션만 수행
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

@expert_bp.route('/api/expert/cracking-progress', methods=['GET'])
@login_required
def cracking_progress():
    """크래킹 진행 상황 조회 API"""
    try:
        cracking_id = request.args.get('cracking_id')
        
        if not cracking_id:
            return jsonify({
                'success': False,
                'error': 'cracking_id가 필요합니다.'
            }), 400
        
        progress = cracking_service.get_progress(cracking_id)
        
        # 크래킹이 완료되었거나 실패한 경우 결과도 포함
        result = None
        if progress.get('status') in ['completed', 'failed', 'error']:
            result = cracking_service.get_result(cracking_id)
        
        return jsonify({
            'success': True,
            'progress': progress,
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@expert_bp.route('/api/expert/verify', methods=['GET'])
@jwt_required
def verify():
    """토큰 유효성 검증"""
    return jsonify({
        'success': True,
        'message': '토큰이 유효합니다.',
        'username': getattr(request, 'current_user', None)
    }), 200
