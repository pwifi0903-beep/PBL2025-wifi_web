from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def landing():
    """랜딩 페이지"""
    return render_template('landing.html')
