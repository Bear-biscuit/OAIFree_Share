from .auth import bp as auth_bp
from .admin import bp as admin_bp
from .main import bp as main_bp
from .user import bp as user_bp
from .chat import bp as chat_bp
from .claude import bp as claude_bp

# 导出所有蓝图，这样可以在工厂函数中直接使用 from .blueprints import auth, admin, main
auth = auth_bp
admin = admin_bp
main = main_bp
user = user_bp
chat = chat_bp
claude = claude_bp

__all__ = ['auth', 'admin', 'main', 'chat', 'claude']