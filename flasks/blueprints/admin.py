from flask import Blueprint, current_app, render_template, request, jsonify
from sqlalchemy import func
from ..models import AutoRefresh, ChatToken, InvitationCodes, Record, User, db
from ..utils import admin_required, generate_verification_code, login_required,is_valid_email, refresh_access_tokens, schedule_next_refresh, usage_record
import psutil
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import platform


bp = Blueprint('admin', __name__)


# 分页与搜索函数
def get_paginated_users(page=1, per_page=5, search=''):
    """
    获取分页的用户列表，并支持按用户名和邮箱搜索。
    """
    page = request.args.get('page', page, type=int)
    search = request.args.get('search', search, type=str).strip().lower()  # 获取搜索关键字
    
    query = User.query.filter()

    # 如果存在搜索条件，进行用户名或邮箱模糊匹配
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )

    query = query.order_by(User.id)  # 排序
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 计算当前页显示的记录范围
    start_index = (page - 1) * per_page + 1
    end_index = min(page * per_page, pagination.total)

    pagination_info = {
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'has_prev': pagination.has_prev,
        'has_next': pagination.has_next,
        'prev_num': pagination.prev_num,
        'next_num': pagination.next_num,
        'start_index': start_index,
        'end_index': end_index
    }

    return pagination.items, pagination_info

@bp.route('/admin')
@login_required
@admin_required
def index():
    return render_template('admin/admin_info.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

# 获取系统负载信息
@bp.route('/system_load')
@admin_required
def system_load():
    # 获取CPU、内存等信息
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 系统版本信息
    system_version = platform.platform()

    # 上次更新时间，设为固定值
    last_update = "2024-10-01"  # 固定的时间戳或描述字符串

    # 运行时长
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    current_time = datetime.now()
    uptime = str(current_time - boot_time)

    # 返回 JSON 格式的系统负载信息
    return jsonify({
        'cpu_percent': cpu_percent,
        'memory_total': memory.total,
        'memory_used': memory.used,
        'memory_percent': memory.percent,
        'disk_total': disk.total,
        'disk_used': disk.used,
        'disk_percent': disk.percent,
        'system_version': system_version,
        'last_update': last_update,
        'uptime': uptime
    })

# 获取用户统计信息
@bp.route('/user_stats')
@admin_required
def user_stats():
    try:
        # 获取总用户数
        total_users = User.query.count()
        
        # 获取最近30天注册的用户数
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        new_users_30d = User.query.filter(User.registered_at >= thirty_days_ago).count()
        
        # 获取最近7天注册的用户数
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        new_users_7d = User.query.filter(User.registered_at >= seven_days_ago).count()
        
        # 获取不同角色的用户数量
        role_counts = db.session.query(
            User.role, 
            func.count(User.id)
        ).group_by(User.role).all()
        
        # 计算每个角色的用户数量
        role_stats = {role: count for role, count in role_counts}
        
        # 获取最近24小时内活跃（登录）的用户数
        last_24h = datetime.utcnow() - timedelta(hours=24)
        active_users_24h = User.query.filter(User.last_login >= last_24h).count()
        
        return jsonify({
            'total_users': total_users,
            'new_users_30d': new_users_30d,
            'new_users_7d': new_users_7d,
            'role_distribution': role_stats,
            'active_users_24h': active_users_24h,
            'growth_rate': {
                'monthly': round((new_users_30d / total_users * 100), 1) if total_users > 0 else 0,
                'weekly': round((new_users_7d / total_users * 100), 1) if total_users > 0 else 0
            },
            'last_updated': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch user statistics',
            'message': str(e)
        }), 500 
    
# 最近用户 
@bp.route('/api/users/recent', methods=['GET'])
@admin_required
def get_recent_users():
    users = User.query.order_by(User.registered_at.desc()).limit(5).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'registered_at': user.registered_at.strftime('%Y-%m-%d'),
        'is_active': bool(user.last_login and (datetime.utcnow() - user.last_login).days < 7)
    } for user in users])

# 添加用户
@bp.route('/api/users', methods=['POST'])
@admin_required
def add_user():
    data = request.json

    # 验证请求数据的存在性
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'status': 'error', 'message': f'{field} 字段缺失'}), 400

    # 检查用户名和邮箱的唯一性
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'status': 'error', 'message': '用户名已存在'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'status': 'error', 'message': '邮箱已存在'}), 400
    # 验证邮箱可用性
    if not is_valid_email(data['email']):
        return jsonify({'status': 'error', 'message': '邮箱不可用'}), 400

    try:
        # 创建用户实例
        user = User(
            username=data['username'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            role=data.get('role', 'user'),  # 默认角色为 'user'
            registered_at=datetime.utcnow()
        )

        # 添加到数据库
        db.session.add(user)
        db.session.commit()

        # 返回成功的响应
        return jsonify({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'registered_at': user.registered_at.strftime('%Y-%m-%d'),
                'is_active': True
            }
        }), 201

    except Exception as e:
        # 出现异常时回滚
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/api/code', methods=['POST', 'GET'])
@login_required
@admin_required
def code():
    if request.method == 'POST':
        # 处理生成新的邀请码
        code = generate_verification_code()
        
        while True:
            if InvitationCodes.query.filter_by(code=code).first():
                # 如果邀请码已存在，重新生成邀请码
                code = generate_verification_code()  
            else:
                # 如果邀请码不重复，创建新邀请码并添加到数据库
                newCode = InvitationCodes(code=code)
                db.session.add(newCode)
                db.session.commit()
                return jsonify({'message': '邀请码生成成功', 'code': code}), 201

    elif request.method == 'GET':
        # 处理返回邀请码列表
        codes = InvitationCodes.query.all()
        code_list = [code_entry.code for code_entry in codes]
        return jsonify({'codes': code_list}), 200

    return jsonify({'error': '不支持的请求方法'}), 405  # 如果请求方法不是 GET 或 POST

    
    


# 管理员-用户管理面板路由
@bp.route('/admin_user')
@login_required
@admin_required
def admin_panel():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    search = request.args.get('search', '', type=str)  # 获取搜索参数

    users, pagination = get_paginated_users(page, per_page, search)


    # 获取当前时间
    now = datetime.utcnow()
    
    # 计算15天前的日期
    seven_days_ago = now - timedelta(days=15)
    
    # 基础统计
    total_users = User.query.count()
    new_users_count = User.query.filter(User.registered_at >= seven_days_ago).count()
    active_users_count = User.query.filter(User.last_login >= seven_days_ago).count()
    inactive_users_count = total_users - active_users_count
    
    # 获取近15天的日期列表
    dates = [(now - timedelta(days=i)).strftime('%m-%d') for i in range(14, -1, -1)]
    
    # 获取每天的注册用户数
    registration_data = []
    activity_data = []
    
    for i in range(14, -1, -1):
        date = (now - timedelta(days=i)).date()
        next_date = date + timedelta(days=1)
        
        # 统计注册用户
        reg_count = User.query.filter(
            User.registered_at >= date,
            User.registered_at < next_date
        ).count()
        registration_data.append(reg_count)
        
        # 统计活跃用户
        active_count = User.query.filter(
            User.last_login >= date,
            User.last_login < next_date
        ).count()
        activity_data.append(active_count)

    # 检查是否为 AJAX 请求
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 如果是 AJAX 请求，只返回表格和分页部分
        return render_template('admin/_user_table.html', users=users, pagination=pagination,email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

    # 正常请求返回完整页面
    return render_template('admin/admin_user.html',
                            users=users, pagination=pagination,
                            total_users=total_users,
                            new_users_count=new_users_count,
                            active_users_count=active_users_count,
                            inactive_users_count=inactive_users_count,
                            dates=dates,
                            registration_data=registration_data,
                            activity_data=activity_data,
                            now=now,
                            email=current_app.config.get('DOMAIN_EMAIL'),
                            title=current_app.config.get('DOMAIN_NAME'))

# 更新用户路由
@bp.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    try:
        # 检查用户名是否已存在（排除当前用户）
        if 'username' in data and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user:
                return jsonify({'error': '用户名已存在'}), 400
            user.username = data['username']

        # 检查邮箱是否已存在（排除当前用户）
        if 'email' in data and data['email'] != user.email:
            existing_email = User.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'error': '邮箱已存在'}), 400
            # 验证邮箱可用性
            if not is_valid_email(data['email']):
                return jsonify({'error': '邮箱不可用'}), 400
            user.email = data['email']

        # 更新角色
        if 'role' in data:
            user.role = data['role']

        # 如果提供了新密码，则更新密码
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])
        
        db.session.commit()
        return jsonify({'message': '用户更新成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    
# 删除用户路由
@bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': '用户删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
    

# 用量表信息
@bp.route('/api/record_info/<value>')
@admin_required
def record_value(value):
    try:
        
        values = Record.query.all()
        if value == 'email':
            value_list = [value.to_dict_email() for value in values]
        elif value == 'user':
            value_list = [value.to_dict_user() for value in values]
        # 使用集合去重
        unique_values = []
        seen_values = set()

        for info in value_list:
            if value == 'email':
                if info['email'] not in seen_values:
                    unique_values.append(info)
                    seen_values.add(info['email'])
            elif value == 'user':
                if info['username'] not in seen_values:
                    unique_values.append(info)
                    seen_values.add(info['username'])

        return jsonify(unique_values), 200

    except FileExistsError:
        return jsonify([]), 200

# 用量查询

@bp.route('/api/record/<type>/<value>')
@admin_required
def record(type,value):
    statistics = None
    gpt35_limit = 0
    gpt4_limit = 0
    gpt4o_limit = 0
    gpt4o_mini_limit = 0
    o1_limit = 0
    o1_mini_limit = 0
    auto = 0
    if type == 'All':
        statistics = Record.query.all()
    else:
        if type == 'email':
            statistics = Record.query.filter_by(email = value).all()
        elif type == 'username':
            statistics = Record.query.filter_by(username = value).all()

    if statistics:
        for statistic in statistics:
            at = statistic.access_token
            st = statistic.shared_token
            result = usage_record(at,st)
            if result.get("usage"):
                if result["usage"].get("auto"):
                    auto = auto + int(result["usage"]["auto"])
            if result.get("gpt35_limit"):
                gpt35_limit = gpt35_limit + int(result['gpt35_limit'])
            if result.get("gpt4_limit"):
                gpt4_limit = gpt4_limit + int(result['gpt4_limit'])
            if result.get("gpt4o_limit"):
                gpt4o_limit = gpt4o_limit + int(result['gpt4o_limit'])
            if result.get("gpt4_limit"):
                gpt4o_mini_limit = gpt4o_mini_limit + int(result['gpt4o_mini_limit'])
            if result.get("o1_limit"):
                o1_limit = o1_limit + int(result['o1_limit'])
            if result.get("o1_mini_limit"):
                o1_mini_limit = o1_mini_limit + int(result['o1_mini_limit'])
    return {"auto":auto,
            "gpt3.5":gpt35_limit,
            "gpt4":gpt4_limit,
            "gpt4o":gpt4o_limit,
            "gpt4o-mini":gpt4o_mini_limit,
            "o1":o1_limit,
            "o1-mini":o1_mini_limit}
    
