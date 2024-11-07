from flask import Blueprint, current_app, render_template, request, jsonify
from sqlalchemy import func
from ..models import AutoRefresh, ChatToken, Record, User, db
from ..utils import admin_required, login_required,is_valid_email, refresh_access_tokens, schedule_next_refresh, usage_record
import psutil
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import platform


bp = Blueprint('chat', __name__)

# chatgpt页
@bp.route('/chatgpt', methods=['GET', 'POST'])
@admin_required
def chatgpt():
    if request.method == 'GET':

        return render_template('admin/chat.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

    if request.method == 'POST':
        # 获取更新后的 retoken 数据
        new_retokens = request.json.get('retokens')
        
        # 如果数据格式有效，保存到文件
        if new_retokens:
            ChatToken.refresh_token = new_retokens
            db.session.commit()
            return jsonify({"status": "success", "message": "chatToken.json 已更新！"}), 200
        else:
            return jsonify({"status": "error", "message": "无效的数据格式！"}), 400
        

# 设定定时任务
@bp.route('/set_auto_refresh', methods=['POST'])
@admin_required
def set_auto_refresh():
    data = request.json
    config = AutoRefresh.query.filter_by(id=1).first()

    # 取消现有的定时任务
    config.auto_refresh_enabled = data['enabled']
    config.refresh_interval_days = data['interval']
    db.session.commit()

    if config.auto_refresh_enabled:
        schedule_next_refresh()

    return jsonify({"status": "success", "message": "自动刷新设置已更新"})

# 加载定时任务配置信息
@bp.route('/get_auto_refresh_config', methods=['GET'])
def get_auto_refresh_config():
    config = AutoRefresh.query.filter_by(id=1).first()
    if config is None:
        return jsonify({'message': '未找到配置'}), 404
    return jsonify(config.to_dict()), 200




# 手动刷新access token
@bp.route('/refresh_tokens', methods=['POST'])
@admin_required
def refresh_tokens():
    try:
        # 调用刷新 access_token 的函数
        refresh_access_tokens()

        return jsonify({
            "status": "success",
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# 加载账号
@bp.route('/get_tokens')
@admin_required
def get_tokens():
    try:
        tokens = ChatToken.query.all()
        token_list = [token.to_dict() for token in tokens]
        return jsonify(token_list), 200
    except FileNotFoundError:
        return jsonify([]), 200  # 如果文件不存在，返回空列表


# 添加新账号
@bp.route('/api/tokens', methods=['POST'])
@admin_required
def create_tokens():
    data = request.get_json()

    if ChatToken.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'message': '该账号已存在'}), 400
    
    try:
            # 添加新账号
            new_chat = ChatToken(
                email = data['email'],
                refresh_token  = data['ReToken'],
                access_token = data['AcToken'],
                status = True,
                type ="/static/img/gpt.png",
                PLUS = data['PLUS']
            )
            db.session.add(new_chat)
            db.session.commit()
            
            return jsonify({'success': True, 'message': '添加成功'})
            
    except Exception as e:
            db.session.rollback()

            return jsonify({'success': False, 'message': '添加失败'})


# 更新账号信息
@bp.route('/api/tokens/<email>', methods=['PUT'])
@admin_required
def update_token(email):
    data = request.get_json()
    tokens = ChatToken.query.filter(ChatToken.email == email)
    token = ChatToken.query.filter(ChatToken.email == email).first()

    if not tokens:
        return jsonify({'success': False, 'message': '账号不存在'}), 404

    # 如果提供了邮箱，则更新邮箱
    if data.get('email'):
        token.email = data['email']
    
    # 如果提供了ReToken，则更新ReToken
    if data.get('ReToken'):
        token.refresh_token = data['ReToken']
    else:
        token.refresh_token = ''

    # 如果提供了AcToken，则更新AcToken
    if data.get('AcToken'):
        token.access_token = data['AcToken']
        token.status = True
    else:
        token.access_token = ''
    if data.get('PLUS'):
        token.PLUS = data['PLUS']
    db.session.commit()

    return jsonify({'success': True, 'message': '账号更新成功'})

# 删除账号
@bp.route('/api/tokens/<email>', methods=['DELETE'])
@admin_required
def delete_token(email):
    
    email = ChatToken.query.filter(ChatToken.email == email).first()
    
    try:
        db.session.delete(email)
        db.session.commit()
        return jsonify({'success': True, 'message': '账号删除成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '删除失败'}), 404
    

