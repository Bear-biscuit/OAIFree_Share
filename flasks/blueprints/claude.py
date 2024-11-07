from flask import Blueprint, current_app, render_template, request, jsonify
from sqlalchemy import func
from ..models import AutoRefresh, ClaudeToken, User, db
from ..utils import admin_required, login_required,is_valid_email, refresh_access_tokens, schedule_next_refresh
import psutil
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import platform


bp = Blueprint('claude', __name__)





@bp.route('/claude')
@admin_required
def claude():
    return render_template('admin/claude.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))


# 加载Refresh Token
@bp.route('/get_Claude')
@admin_required
def get_Claude():
    try:
        tokens = ClaudeToken.query.all()
        token_list = [token.to_dict() for token in tokens]
        return jsonify(token_list), 200
    except FileNotFoundError:
        return jsonify([]), 200  # 如果文件不存在，返回空列表


# 添加新账号
@bp.route('/api/Claude', methods=['POST'])
@admin_required
def create_Claude():
    data = request.get_json()

    if ClaudeToken.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '该账号已存在'}), 400
    
    try:
            # 添加新账号
            new_chat = ClaudeToken(
                email = data['email'],
                skToken  = data['SkToken'],
                status = True,
                type ="/static/img/claude.png",
                PLUS = data['PLUS']
            )
            db.session.add(new_chat)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '添加成功'})
            
    except Exception as e:
            db.session.rollback()
            print(e)
            return jsonify({'success': False, 'message': '添加失败'})


# 更新账号信息
@bp.route('/api/Claude/<email>', methods=['PUT'])
@admin_required
def update_Claude(email):
    data = request.get_json()
    tokens = ClaudeToken.query.filter(ClaudeToken.email == email)
    token = ClaudeToken.query.filter(ClaudeToken.email == email).first()

    if not tokens:
        return jsonify({'success': False, 'message': '账号不存在'}), 404

    # 如果提供了邮箱，则更新邮箱
    if data.get('email'):
        token.email = data['email']
    
    # 如果提供了ReToken，则更新ReToken
    if data.get('SkToken'):
        token.SkToken = data['SkToken']
        token.status = True
    
    if data.get('PLUS'):
        token.PLUS = data['PLUS']
    db.session.commit()

    return jsonify({'success': True, 'message': '账号更新成功'})

# 删除账号
@bp.route('/api/Claude/<email>', methods=['DELETE'])
@admin_required
def delete_Claude(email):
    
    email = ClaudeToken.query.filter(ClaudeToken.email == email).first()
    
    try:
        db.session.delete(email)
        db.session.commit()
        return jsonify({'success': True, 'message': '账号删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '删除失败'}), 404