from flask import Flask
from config import Config
from blueprints.main import main_bp
from blueprints.user import user_bp
from blueprints.expert import expert_bp

def create_app():
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Blueprint 등록
    app.register_blueprint(main_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(expert_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
