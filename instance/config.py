# config.py

# 数据库配置
MYSQL_HOST = '127.0.0.1'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '031020'
# MYSQL_HOST = '142.171.31.40'
# MYSQL_USER = 'bocchi2b'
# MYSQL_PASSWORD = 'cyh031020'
MYSQL_DB = 'oaifree'

# Flask配置
SECRET_KEY = 'awhkwgbfflauws'  # 请更改为随机字符串
DEBUG = False  # 生产环境设置为False

# Cookie 和 Session 配置
JWT_EXPIRATION_DAYS = 30  # 记住我的过期时间（天）
COOKIE_SECURE = False  # 仅通过HTTPS发送cookie
COOKIE_HTTPONLY = True  # 防止XSS攻击的httponly标志
SESSION_COOKIE_SECURE = False  # 与COOKIE_SECURE保持一致
SESSION_COOKIE_HTTPONLY = True  # 与COOKIE_HTTPONLY保持一致
SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF攻击的SameSite策略

# CSRF 配置
WTF_CSRF_ENABLED = True  # 启用CSRF保护
WTF_CSRF_TIME_LIMIT = 3600  # CSRF Token过期时间（秒）
WTF_CSRF_SSL_STRICT = False  # 是否严格要求HTTPS（与COOKIE_SECURE保持一致）
WTF_CSRF_CHECK_DEFAULT = True  # 默认检查所有POST/PUT/PATCH/DELETE请求

# 数据库URI
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?ssl_disabled=true'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 镜像地址
DOMAIN_CHATGPT = 'new.oaifree.com'
DOMAIN_CLAUDE = 'demo.fuclaude.com'



REGISTER = False # 默认不开启注册

REG_CODE = True # 注册是否需要邀请码 默认需要

# 邮箱发信相关
EMAIL_FORNAME = 'AI共享' # 发件者名称
EMAIL_TONAME = '用户' # 收件者名称
EMAIL_API = 'https://email-worker.bocchi2b.top/api/send_mail' # cloudflare邮箱后端worker地址
EMAIL_JWT = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZGRyZXNzIjoiYWRtaW5AYm9jY2hpMmIudG9wIiwiYWRkcmVzc19pZCI6IjEifQ.wz8aTSwoibHG8shrbMa36pXU-mg-eVt0pRKvvcHl3RU' # 发送邮件的邮箱JWT


# 前端相关
DOMAIN_NAME = 'AI' # 网站名
DOMAIN_EMAIL = 'bocchi2b@qq.com' # “联系我”邮箱