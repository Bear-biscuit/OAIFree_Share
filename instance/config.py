import os

# 数据库配置
MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')  # 默认为 'mysql'
MYSQL_USER = os.getenv('MYSQL_USER', 'root')  # 默认为 'root'
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')  # 默认为 'password'
MYSQL_DB = os.getenv('MYSQL_DB', 'oaifree')  # 默认为 'oaifree'

# 数据库 URI
SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}?ssl_disabled=true'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Flask 配置
SECRET_KEY = os.getenv('SECRET_KEY', 'awhkwgbfflauws')  # 默认值可以更改
DEBUG = os.getenv('DEBUG', 'False') == 'True'  # 通过环境变量控制是否启用调试模式

# Cookie 和 Session 配置
JWT_EXPIRATION_DAYS = int(os.getenv('JWT_EXPIRATION_DAYS', 30))  # 默认为 30 天
COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'False') == 'True'  # 默认为 False
COOKIE_HTTPONLY = os.getenv('COOKIE_HTTPONLY', 'True') == 'True'  # 默认为 True
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True'  # 默认为 False
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True') == 'True'  # 默认为 True
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')  # 默认为 'Lax'

# CSRF 配置
WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', 'True') == 'True'  # 默认为 True
WTF_CSRF_TIME_LIMIT = int(os.getenv('WTF_CSRF_TIME_LIMIT', 3600))  # 默认为 3600 秒
WTF_CSRF_SSL_STRICT = os.getenv('WTF_CSRF_SSL_STRICT', 'False') == 'True'  # 默认为 False
WTF_CSRF_CHECK_DEFAULT = os.getenv('WTF_CSRF_CHECK_DEFAULT', 'True') == 'True'  # 默认为 True

# 镜像地址
DOMAIN_CHATGPT = os.getenv('DOMAIN_CHATGPT', 'new.oaifree.com')  # 默认为 'new.oaifree.com'
DOMAIN_CLAUDE = os.getenv('DOMAIN_CLAUDE', 'demo.fuclaude.com')  # 默认为 'demo.fuclaude.com'

# 注册
REGISTER = os.getenv('REGISTER','False') == 'True' # 默认不开启注册

REG_CODE = os.getenv('REG_CODE','True') == 'True' # 注册是否需要邀请码 默认需要


# 邮箱配置
# 如果开启注册必须进行配置 

EMAIL_API = os.getenv('EMAIL_API','https://yourdomain.com') # cloudflare邮箱后端worker地址
EMAIL_JWT = os.getenv('EMAIL_JWT','ahkuwhdkauwdkakdwwww') # 发送邮件的邮箱JWT
EMAIL_FORNAME = os.getenv('EMAIL_FORNAME','AI共享') # 发件者名称
EMAIL_TONAME = os.getenv('EMAIL_TONAME','用户') # 收件者名称

# 前端相关
DOMAIN_NAME = os.getenv('DOMAIN_NAME','AI共享站') # 网站名
DOMAIN_EMAIL = os.getenv('DOMAIN_EMAIL','your@email.com') # “联系我”邮箱
