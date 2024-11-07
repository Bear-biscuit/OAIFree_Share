import json
import secrets
import threading
import time
from flask import current_app, request, redirect, url_for, flash, session
from email_validator import validate_email, EmailNotValidError
from functools import wraps
from datetime import datetime, timedelta
import random
import string
import jwt
import requests
from .models import AutoRefresh, ChatToken, Record, User, db

def login_required(f):
    """登录状态装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            remember_token = request.cookies.get('remember_token')
            if remember_token:
                user_id = verify_remember_token(remember_token)
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        # 重新设置session
                        session['username'] = user.username
                        session['user_id'] = user.id
                        session['role'] = user.role
                        return f(*args, **kwargs)
            flash('请先登录！', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('请先登录！', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        user = User.query.filter_by(username=session['username']).first()
        if not user or user.role != 'admin':
            flash('需要管理员权限！', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# 邮箱验证函数
def is_valid_email(email):
    try:
        # 验证邮箱格式和域名
        validate_email(email)
        return True
    except EmailNotValidError as e:
        return False
    

def generate_verification_code(length=6):
    """生成指定长度的验证码"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(to_email, code):
    """发送验证码邮件"""
    send_body = {
        "from_name": current_app.config.get('EMAIL_FORNAME'),  # 替换为你的发件人名称
        "to_name": current_app.config.get('EMAIL_TONAME'),
        "to_mail": to_email,
        "subject": "注册验证码",
        "is_html": True,
        "content": f"""
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
                <h2 style="color: #333;">验证码</h2>
                <p>您好！</p>
                <p>您的验证码是：</p>
                <div style="background-color: #f5f5f5; padding: 10px; margin: 15px 0; text-align: center;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">{code}</span>
                </div>
                <p>验证码有效期为5分钟。如果不是您本人的操作，请忽略此邮件。</p>
                <p>此邮件为系统自动发送，请勿回复。</p>
            </div>
        """
    }

    try:
        response = requests.post(
            url=current_app.config.get('EMAIL_API'),
            json=send_body,
            headers={
                "Authorization": f"Bearer {current_app.config.get('EMAIL_JWT')}",
                "Content-Type": "application/json"
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"发送邮件失败：{str(e)}")
        return False
    
def send_otp_code_email(to_email, code):
    """发送验证码邮件"""
    send_body = {
        "from_name": current_app.config.get('EMAIL_FORNAME'),  # 替换为你的发件人名称
        "to_name": current_app.config.get('EMAIL_TONAME'),
        "to_mail": to_email,
        "subject": "登录验证码",
        "is_html": True,
        "content": f"""
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
                <h2 style="color: #333;">验证码</h2>
                <p>您好！</p>
                <p>您的登录验证码是：</p>
                <div style="background-color: #f5f5f5; padding: 10px; margin: 15px 0; text-align: center;">
                    <span style="font-size: 24px; font-weight: bold; letter-spacing: 5px;">{code}</span>
                </div>
                <p>验证码有效期为5分钟。如果不是您本人的操作，请尽快更改您的密码。</p>
                <p>此邮件为系统自动发送，请勿回复。</p>
            </div>
        """
    }

    try:
        response = requests.post(
            url=current_app.config.get('EMAIL_API'),
            json=send_body,
            headers={
                "Authorization": f"Bearer {current_app.config.get('EMAIL_JWT')}",
                "Content-Type": "application/json"
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"发送邮件失败：{str(e)}")
        return False


def verify_code(email, code):
    """验证验证码是否正确"""
    stored_code = session.get(f'verification_code_{email}')
    expire_time = session.get(f'code_expire_time_{email}')
    
    if not stored_code or not expire_time:
        return False
    
    expire_time = datetime.fromisoformat(expire_time)
    if datetime.now() > expire_time:
        # 清除过期的验证码
        session.pop(f'verification_code_{email}', None)
        session.pop(f'code_expire_time_{email}', None)
        return False
    
    return stored_code == code

def generate_reset_token():
    """生成安全的重置令牌"""
    return secrets.token_urlsafe(32)

def send_reset_email(to_email, reset_link):
    """发送密码重置链接邮件"""
    send_body = {
        "from_name": current_app.config.get('EMAIL_FORNAME'),  # 替换为你的发件人名称
        "to_name": current_app.config.get('EMAIL_TONAME'),
        "to_mail": to_email,
        "subject": "密码重置",
        "is_html": True,
        "content": f"""
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif;">
                <h2 style="color: #333;">密码重置</h2>
                <p>您好！</p>
                <p>我们收到了您的密码重置请求。请点击下面的链接重置您的密码：</p>
                <div style="margin: 15px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        重置密码
                    </a>
                </div>
                <p>此链接将在30分钟后过期。如果不是您本人的操作，请忽略此邮件。</p>
                <p style="color: #666; margin-top: 20px; font-size: 12px;">
                    如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
                    {reset_link}
                </p>
                <p>此邮件为系统自动发送，请勿回复。</p>
            </div>
        """
    }

    try:
        response = requests.post(
            url=current_app.config.get('EMAIL_API'),
            json=send_body,
            headers={
                "Authorization": f"Bearer {current_app.config.get('EMAIL_JWT')}",
                "Content-Type": "application/json"
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"发送邮件失败：{str(e)}")
        return False

# 记录用户登录ip
def get_user_ip():
    # 尝试从请求头中获取 X-Forwarded-For
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip

def generate_remember_token(user_id):
    """生成记住我令牌"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=current_app.config.get('JWT_EXPIRATION_DAYS',30))
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    # 如果 token 是字节对象，则解码为字符串
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return token

def verify_remember_token(token):
    """验证记住我令牌"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except:
        return None
    

# 两步验证
def send_otp_email(user):
    otp_code = generate_verification_code()  # 生成一个随机OTP
    user.otp_code = otp_code
    user.otp_expiration = datetime.utcnow() + timedelta(minutes=5)  # 5分钟有效期
    db.session.commit()
    # 使用邮件库发送OTP到用户邮箱
    send_otp_code_email(user.email, otp_code)

def verify_otp_code(user, otp_code):
    """验证OTP码是否有效
    
    Args:
        user: User对象，包含otp_code和otp_expiration属性
        otp_code: 用户输入的OTP验证码
        
    Returns:
        bool: 验证是否成功
    """
    if not user.otp_code or not user.otp_expiration:
        return False
    
    if datetime.utcnow() > user.otp_expiration:
        return False
    
    return user.otp_code == otp_code


# 刷新 access_token 的主函数
def refresh_access_tokens():
    # 读取 refresh_token 列表
    refresh_tokens_list = ChatToken.query.all()
    refresh_tokens = [token.to_dict() for token in refresh_tokens_list]

    # 遍历 refresh_token 列表
    for token_info in refresh_tokens:
      
        token = ChatToken.query.filter(ChatToken.email == token_info['email']).first()

        refresh_token = token.refresh_token

        # 如果 refresh_token 为空，跳过这一行
        if not refresh_token:
            continue

        # 先清除用量表中的access_token
        records_to_delete = Record.query.filter_by(access_token=token.access_token).all()
        for record in records_to_delete:
            db.session.delete(record)
        db.session.commit()
        
        try:
            # 使用 POST 请求通过 refresh_token 获取 access_token
            response = requests.post(
                "https://token.oaifree.com/api/auth/refresh",
                data={"refresh_token": refresh_token}
            )
            response_data = response.json()

            access_token = response_data.get("access_token")
            if access_token:  # 如果成功获取到 access_token
                # 更新 access_token 和状态为 True
                token.access_token = access_token
                token.status = True
            else:
                # 如果获取失败，设置状态为 False
                token.status = False

            db.session.commit()
        except Exception as e:
            # 捕获请求错误并记录失败的 token，状态为 False
            token.status = False
            db.session.commit()

    return refresh_tokens

# 获取share token
def register_token(access_token, unique_name, expire_in=0, show_userinfo=True, gpt35_limit=-1, 
                   gpt4_limit=-1, reset_limit=False, show_conversations=False, site_limit="", 
                   temporary_chat=False):
    """
    注册共享令牌的函数。

    :param access_token: 用户的访问令牌
    :param unique_name: 独一无二的共享令牌名称
    :param expire_in: 共享令牌的过期秒数，默认为0
    :param show_userinfo: 是否显示用户信息，默认为False
    :param gpt35_limit: GPT-3.5模型的使用限制，默认为-1表示不限制
    :param gpt4_limit: GPT-4模型的使用限制，默认为-1表示不限制
    :param reset_limit: 是否重置使用限制，默认为False
    :param show_conversations: 是否显示对话记录，默认为True
    :param site_limit: 站点使用限制，默认为空字符串，表示不限制
    :param temporary_chat: 是否开启临时聊天功能，默认为True

    :return: token_key (str)，注册成功后返回的共享令牌 key
    """
    
    url = 'https://chat.oaifree.com/token/register'
    
    # 数据 payload
    data = {
        "access_token": access_token,
        "unique_name": unique_name,
        "expire_in": expire_in,
        "show_userinfo": show_userinfo,
        "gpt35_limit": gpt35_limit,
        "gpt4_limit": gpt4_limit,
        "reset_limit": reset_limit,
        "show_conversations": show_conversations,
        "site_limit": site_limit,
        "temporary_chat": temporary_chat
    }

    # 发起 POST 请求
    response = requests.post(url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=data)

    # 获取返回的共享令牌 key
    token_key = response.json().get("token_key")

    return token_key

# 获取用量信息
def usage_record(at,st):
    # 构建URL
    base_url = "https://chat.oaifree.com/token/info/"
    url = f"{base_url}{st}"
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {at}",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    try:
        # 发送GET请求
        response = requests.get(url, headers=headers)
        
        # 检查响应状态码
        response.raise_for_status()
        
        # 返回JSON响应
        return response.json()
        
    except requests.exceptions.RequestException as e:
        # print(f"请求发生错误: {e}")
        return None


# 获取登陆链接
def getoauth(token):
    domain = current_app.config.get('DOMAIN_CHATGPT')
    print(domain)
    share_token = token 
    
    url = f'https://{domain}/api/auth/oauth_token'
    headers = {
        'Origin': f'https://{domain}',
        'Content-Type': 'application/json'
    }
    data = {
        'share_token': share_token
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        loginurl = response.json().get('login_url')
        return loginurl
    except requests.RequestException as e:
        return None
    

# 定时刷新token
    
def is_main_process():
    import os
    return os.environ.get('WERKZEUG_RUN_MAIN') != 'true'

current_timer = None
timer_lock = threading.Lock()

def schedule_next_refresh():
        
    global current_timer
    config = AutoRefresh.query.filter_by(id=1).first()
    
    with timer_lock:
        if config.auto_refresh_enabled:
            if current_timer:
                current_timer.cancel()
                
            next_refresh = datetime.now() + timedelta(days=config.refresh_interval_days)
            config.next_refresh_time = next_refresh.isoformat()
            db.session.commit()

            current_timer = threading.Timer(
                (next_refresh - datetime.now()).total_seconds(), 
                auto_refresh_tokens
            )
            current_timer.start()

def auto_refresh_tokens():

    print('开始自动刷新')
    refresh_access_tokens()

    # 添加延时，确保两次刷新之间有足够间隔
    time.sleep(2)  # 等待1秒

    # 刷新完成后，调度下一次刷新
    schedule_next_refresh()

# 在应用启动时调用这个函数
def init_auto_refresh():
    if not is_main_process():
        print("在 reloader 进程中，跳过定时器初始化")
        return
        
    print(f"在主进程中初始化自动刷新, 当前时间: {datetime.now()}")
    config = AutoRefresh.query.filter_by(id=1).first()

    if config.auto_refresh_enabled and config.next_refresh_time:
        next_refresh = datetime.fromisoformat(config.next_refresh_time)
        
        if next_refresh > datetime.now():
            delay_seconds = (next_refresh - datetime.now()).total_seconds()
            print(f"设置初始定时器, 延迟秒数: {delay_seconds}")
            
            global current_timer
            with timer_lock:
                current_timer = threading.Timer(delay_seconds, auto_refresh_tokens)
                current_timer.start()
        else:
            schedule_next_refresh()

# claude登陆链接获取
def get_claude_login_url(session_key,uname):
    domain = current_app.config.get('DOMAIN_CLAUDE')
    url = f'https://{domain}/manage-api/auth/oauth_token'
    
    # 请求体参数
    data = {
        'session_key': session_key,
        'unique_name': uname  # 生成唯一标识符
    }

    # 设置请求头
    headers = {'Content-Type': 'application/json'}

    try:
        # 发送 POST 请求
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # 检查响应状态码是否为200
        if response.status_code == 200:
            response_data = response.json()

            # 检查 'login_url' 是否存在
            if 'login_url' in response_data:
                login_url = response_data['login_url']
                
                # 如果URL没有以http开头，拼接基础URL
                if not login_url.startswith('http'):
                    return f'https://{domain}' + login_url
                return login_url
        
        # 如果状态码不是200或login_url不存在，返回None
        return None
    
    except requests.RequestException as e:
        # 捕获异常并返回错误信息
        return None