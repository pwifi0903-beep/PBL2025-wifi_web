from flask import Blueprint, render_template, jsonify, request
from data.wifi_data import wifi_generator

user_bp = Blueprint('user', __name__)

@user_bp.route('/user')
def user_page():
    """사용자용 페이지"""
    security_guide = wifi_generator.get_security_guide_user()
    return render_template('user.html', security_guide=security_guide)

@user_bp.route('/api/scan', methods=['POST'])
def scan_wifi():
    """사용자용 와이파이 스캔 API"""
    try:
        wifi_list = wifi_generator.generate_user_wifi_list()
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
