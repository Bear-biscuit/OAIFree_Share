from . import db
from datetime import datetime

class User(db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    last_login = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(100))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.DateTime, nullable=True)
    two_fa = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
    
class AutoRefresh(db.Model):
    """自动刷新模型"""
    __tablename__ = 'auto_refresh'

    id = db.Column(db.Integer, primary_key=True)
    auto_refresh_enabled = db.Column(db.Boolean, default=False, nullable=False)
    refresh_interval_days = db.Column(db.Integer, nullable=False)
    next_refresh_time = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<AutoRefresh {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'auto_refresh_enabled': self.auto_refresh_enabled,
            'refresh_interval_days': self.refresh_interval_days,
            'next_refresh_time': self.next_refresh_time
        }
    
class ChatToken(db.Model):
    """ChatGPT 令牌模型"""
    __tablename__ = 'chat_token'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.String(255), nullable=True)
    access_token = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, default=True, nullable=False)
    type = db.Column(db.String(255), nullable=False)
    PLUS = db.Column(db.String(10), default='False', nullable=False)
    
    def __repr__(self):
        return f'<ChatToken {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'refresh_token': self.refresh_token,
            'access_token': self.access_token,
            'status': self.status,
            'type': self.type,
            'PLUS': self.PLUS
        }

class ClaudeToken(db.Model):
    """Claude 令牌模型"""
    __tablename__ = 'claude_token'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    skToken = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Boolean, default=True, nullable=False)
    type = db.Column(db.String(255), nullable=True)
    PLUS = db.Column(db.String(10), default='False', nullable=False)
    
    def __repr__(self):
        return f'<ClaudeToken {self.email}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'skToken': self.skToken,
            'status': self.status,
            'type': self.type,
            'PLUS': self.PLUS
        }
    
class Record(db.Model):
    """用量记录模型"""
    __tablename__ = 'record'  

    id = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(255), nullable=False)  
    email = db.Column(db.String(255), nullable=False)  
    access_token = db.Column(db.Text, nullable=False)  
    shared_token = db.Column(db.Text, nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  

    def __repr__(self):
        return f"<Record username={self.username}, email={self.email}>"
    
    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'access_token': self.access_token,
            'shared_token': self.shared_token,
            'created_at': self.created_at
        }
    def to_dict_user(self):
        return {
            'username': self.username
        }
    def to_dict_email(self):
        return {
            'email': self.email
        }

class InvitationCodes(db.Model):
    """注册邀请码"""
    __tablename__ = 'invitation_codes'
    code = db.Column(db.String(6), primary_key=True)  

    def __repr__(self):
        return f'<Code {self.code}>'
    
    def to_dict(self):
        return {
            'code': self.code
        }