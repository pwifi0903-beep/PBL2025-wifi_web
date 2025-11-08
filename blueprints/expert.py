from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
from data.wifi_data import wifi_generator
from services.security_check import security_service

expert_bp = Blueprint('expert', __name__)

def login_required(f):
    """로그인 필수 데코레이터"""
    def decorated_function(*args, **kwargs):
        if 'expert_logged_in' not in session:
            return redirect(url_for('expert.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@expert_bp.route('/expert/login', methods=['GET', 'POST'])
def login():
    """관리자 로그인 페이지"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin':
            session['expert_logged_in'] = True
            return redirect(url_for('expert.expert_page'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')
    
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

@expert_bp.route('/expert/logout')
def logout():
    """로그아웃"""
    session.pop('expert_logged_in', None)
    return redirect(url_for('main.landing'))
