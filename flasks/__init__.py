import click
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

import os

from flask_wtf import CSRFProtect

# 初始化数据库对象
db = SQLAlchemy()

def create_app(test_config=None):
    """应用工厂函数"""
    app = Flask(__name__, instance_relative_config=True)
    
    # 默认配置
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'flaskr.sqlite'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # 加载实例配置（如果存在）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 加载测试配置
        app.config.update(test_config)

    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 初始化扩展
    db.init_app(app)
    csrf = CSRFProtect(app)

    # 注册蓝图
    from .blueprints import auth, admin, main, user, chat, claude
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(main)
    app.register_blueprint(user)
    app.register_blueprint(chat)
    app.register_blueprint(claude)

    # 注册错误处理器
    register_error_handlers(app)

    # 注册命令
    register_commands(app)

    with app.app_context():
        from .utils import init_auto_refresh
        init_auto_refresh()

    return app

def register_error_handlers(app):
    """注册错误处理器"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/500.html'), 500

def register_commands(app):
    """注册Flask命令"""
    @app.cli.command('init-db')
    def init_db_command():
        """初始化数据库"""
        from .models import User
        from werkzeug.security import generate_password_hash
        
        db.create_all()
        
        # 创建默认管理员账户（如果不存在）
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                password=generate_password_hash('123123'),
                email='admin@example.com',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            click.echo('Initialized the database and created admin user.')