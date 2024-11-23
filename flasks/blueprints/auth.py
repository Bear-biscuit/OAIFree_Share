from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import InvitationCodes, User, db
from ..utils import generate_remember_token, generate_reset_token, get_user_ip, send_otp_email, send_reset_email, send_verification_email, generate_verification_code, verify_code, verify_otp_code
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__)

@bp.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    """发送验证码的路由"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'success': False, 'message': '请提供邮箱地址'}), 400
    
    # 检查是否在冷却时间内
    last_send_time = session.get(f'last_send_time_{email}')
    if last_send_time:
        last_send_time = datetime.fromisoformat(last_send_time)
        if datetime.now() - last_send_time < timedelta(minutes=1):
            return jsonify({'success': False, 'message': '请求频率过高,请稍后再试'}), 429

    # 生成验证码
    code = generate_verification_code()
    

    # 发送验证码
    if send_verification_email(email, code):
        # 存储验证码和发送时间
        session[f'verification_code_{email}'] = code
        session[f'code_expire_time_{email}'] = (datetime.now() + timedelta(minutes=5)).isoformat()
        session[f'last_send_time_{email}'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': '验证码已发送'}), 200
    else:
        return jsonify({'success': False, 'message': '验证码发送失败'}), 500


@bp.route('/register', methods=['GET', 'POST'])
def register():

    if not current_app.config.get('REGISTER'):
        flash('暂未开启注册', 'danger')
        return redirect(url_for('auth.login'))

    if 'username' in session:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        # 获取表单数据
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        verification_code = request.form.get('verification_code', '').strip()
        vecode = request.form.get('vcode', '').strip()
        
        # 判断是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        def error_response(message):
            """统一错误响应处理"""
            flash(message, 'danger')
            if is_ajax:
                return jsonify({'success': False, 'message': message}), 400
            return render_template('auth/register.html')
        
        
        # 基础验证
        if not all([username, password, email, verification_code]):
            return error_response('请填写所有必需的字段！')
            
        # 验证码检查
        if not verify_code(email, verification_code):
            return error_response('验证码无效或已过期')
            
        # 表单验证
        if len(username) < 3:
            return error_response('用户名至少需要3个字符！')
            
        if len(password) < 6:
            return error_response('密码至少需要6个字符！')
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return error_response('用户名已存在！')
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return error_response('邮箱已被注册！')
        
        if current_app.config.get('REG_CODE'):
            # 邀请码验证
            code_entry = InvitationCodes.query.filter_by(code=vecode).first()
            
            if not code_entry:
                return error_response('邀请码错误！')
        
        db.session.delete(code_entry)
        db.session.commit()

        try:
            # 创建新用户
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username, 
                password=hashed_password, 
                email=email,
                role='user'  # 默认角色为普通用户
            )
            db.session.add(new_user)
            db.session.commit()
            
            # 清除验证码
            session.pop(f'verification_code_{email}', None)
            session.pop(f'code_expire_time_{email}', None)
            
            # 注册成功响应
            flash('注册成功！请登录。', 'success')
            if is_ajax:
                return jsonify({
                    'success': True, 
                    'message': '注册成功！请登录。',
                    'redirect': url_for('auth.login')
                }), 200
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            print(e)
            return error_response(f'注册失败，请稍后重试。{e}')
    
    # GET 请求返回注册页面
    return render_template('auth/register.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = request.form.get('remember') == 'on'
        user_ip = get_user_ip()
        user = User.query.filter_by(username=username).first()
        if user is None:
            # 处理用户未找到的情况 
            flash(‘用户名或密码错误！’， danger')
            return redirect(url_for('auth.login'))
        if not user.two_fa or user_ip == user.last_login_ip:
            
            if user and check_password_hash(user.password, password):
                
                session['username'] = user.username
                session['user_id'] = user.id
                session['role'] = user.role
                # 处理"记住我"
                response = make_response(redirect(url_for('main.index')))
                if remember:
                    # 生成记住我令牌
                    remember_token = generate_remember_token(user.id)
                    # 设置cookie，过期时间30天
                    response.set_cookie(
                        'remember_token',
                        remember_token,
                        max_age=60 * 60 *24 * current_app.config.get('JWT_EXPIRATION_DAYS',30),
                        httponly=True,  # 防止XSS攻击
                        secure = current_app.config.get('COOKIE_SECURE')  # 仅通过HTTPS发送
                    )

                # 更新最后登录时间
                user.last_login = datetime.utcnow()
                # 记录本次登录ip
                user.last_login_ip = user_ip

                db.session.commit()
                
                flash('登录成功！', 'success')
                return response
            
            flash('用户名或密码错误！', 'danger')
        else:
            if user and check_password_hash(user.password, password):
            # 存储临时登录信息
                session['temp_user_id'] = user.id
                session['temp_remember'] = remember
                session['temp_email'] = user.email
                
                # 发送OTP验证码
                send_otp_email(user)
                
                return redirect(url_for('auth.verify_otp'))
            
            flash('用户名或密码错误！', 'danger')
            
    return render_template('auth/login.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

@bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['temp_user_id'])
    if not user:
        flash('用户不存在！', 'danger')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        otp_code = request.form.get('otp_code')
        remember = session.get('temp_remember')
        user_ip = get_user_ip()
        
        if verify_otp_code(user, otp_code):
            # 清除临时会话数据
            session.pop('temp_user_id', None)
            session.pop('temp_remember', None)
            
            # 设置登录会话
            session['username'] = user.username
            session['user_id'] = user.id
            session['role'] = user.role
            
            # 处理"记住我"
            response = make_response(redirect(url_for('main.index')))
            if remember:
                remember_token = generate_remember_token(user.id)
                response.set_cookie(
                    'remember_token',
                    remember_token,
                    max_age=60 * 60 * 24 * current_app.config.get('JWT_EXPIRATION_DAYS', 30),
                    httponly=True,
                    secure=current_app.config.get('COOKIE_SECURE')
                )
            
            # 更新最后登录时间
            user.last_login = datetime.utcnow()
            # 记录本次登录ip
            user.last_login_ip = user_ip
            user.otp_code = None
            user.otp_expiration =None
            db.session.commit()
            
            flash('登录成功！', 'success')
            return response
        
        flash('验证码错误或已过期！', 'danger')
    
    return render_template('auth/verify_otp.html',email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'temp_user_id' not in session:
        return jsonify({'error': 'Invalid session'}), 400
        
    user = User.query.get(session['temp_user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    send_otp_email(user)
    return jsonify({'message': 'OTP sent successfully'}), 200


reset_tokens = {}

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if 'username' in session:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('请输入邮箱地址', 'danger')
            return redirect(url_for('auth.forgot_password'))

        # 检查邮箱是否存在
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('该邮箱地址未注册', 'danger')
            return redirect(url_for('auth.forgot_password'))

        # 生成重置令牌并保存
        token = generate_reset_token()
        reset_tokens[token] = {
            'email': email,
            'expires_at': datetime.now() + timedelta(minutes=30)
        }

        # 生成重置链接
        reset_link = url_for('auth.reset_password', token=token, _external=True,email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))
        
        # 发送重置邮件
        if send_reset_email(email, reset_link):
            flash('重置链接已发送到您的邮箱，请查收', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('发送邮件失败，请稍后重试', 'danger')
            return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if 'username' in session:
        return redirect(url_for('main.index'))

    # 检查令牌是否存在
    if token not in reset_tokens:
        flash('重置链接无效或已过期', 'danger')
        return redirect(url_for('auth.forgot_password'))

    # 检查令牌是否过期
    token_data = reset_tokens[token]
    if datetime.now() > token_data['expires_at']:
        del reset_tokens[token]
        flash('重置链接已过期，请重新申请', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not all([new_password, confirm_password]):
            flash('请填写所有字段', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        # 验证密码
        if new_password != confirm_password:
            flash('两次输入的密码不匹配', 'danger')
            return redirect(url_for('auth.reset_password', token=token))

        # 更新密码
        user = User.query.filter_by(email=token_data['email']).first()
        user.password = generate_password_hash(new_password)
        db.session.commit()

        # 清除令牌
        del reset_tokens[token]

        flash('密码重置成功，请使用新密码登录', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token,email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))


@bp.route('/logout')
def logout():
    session.clear()
    response = make_response(redirect(url_for('auth.login')))
    response.delete_cookie('remember_token')
    flash('已成功退出登录！', 'info')
    return response