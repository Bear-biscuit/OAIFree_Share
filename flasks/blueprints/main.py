from flask import Blueprint,current_app, render_template, session, request, jsonify
from ..utils import  get_claude_login_url, getoauth, login_required, register_token
from ..models import ChatToken, ClaudeToken, Record, User,db
from werkzeug.security import generate_password_hash, check_password_hash
bp = Blueprint('main', __name__)

@bp.route('/')
@login_required
def index():
    # 读取 chatToken.json 中的 access_tokens
    gpt_tokens_list = ChatToken.query.all()
    gpt_tokens = [token.to_dict() for token in gpt_tokens_list]

    # 读取 claudeToken.json 中的 token
    claude_tokens_list = ClaudeToken.query.all()
    claude_tokens = [token.to_dict() for token in claude_tokens_list]
    
    # 创建两个列表分别存储PLUS和普通账号
    gpt_plus_tokens = []
    gpt_normal_tokens = []

    claude_plus_tokens = []
    claude_normal_tokens = []
    
    # 遍历所有token并分组
    for idx, token in enumerate(gpt_tokens):
        if token['status']:  # 如果token有效
            token_info = {
                'index': idx,
                'type': token.get('type', 'unknown'),
                'PLUS': token.get('PLUS', 'false')
            }
            
            # 根据PLUS状态分组
            if token_info['PLUS'].lower() == 'true':
                gpt_plus_tokens.append(token_info)
            else:
                gpt_normal_tokens.append(token_info)

    # 遍历所有token并分组
    for idx, token in enumerate(claude_tokens):
        if token['status']:  # 如果token有效
            token_info = {
                'index': idx,
                'type': token.get('type', 'unknown'),
                'PLUS': token.get('PLUS', 'false')
            }
            
            # 根据PLUS状态分组
            if token_info['PLUS'].lower() == 'true':

                claude_plus_tokens.append(token_info)
            else:
                claude_normal_tokens.append(token_info)
    

    # 按顺序合并两个列表，PLUS账号在前
    gpt_valid_tokens = gpt_plus_tokens + gpt_normal_tokens

    claude_valid_tokens = claude_plus_tokens + claude_normal_tokens


    # 渲染模板,传递有效token的详细信息
    return render_template(
        'main/index.html',
        gpt_valid_tokens=gpt_valid_tokens,  # 传递排序后的token列表
        claude_valid_tokens= claude_valid_tokens,
        email=current_app.config.get('DOMAIN_EMAIL'),
        title=current_app.config.get('DOMAIN_NAME')
    )

# 用于处理 UNIQUE_NAME 的提交
@bp.route('/submit_name', methods=['POST'])
@login_required
def submit_name():
    data = request.json
    unique_name = data.get('unique_name')
    index = data.get('index')
    Type = data.get('type')


    if Type == 'chatgpt':

        tokens_list = ChatToken.query.all()
        tokens = [token.to_dict() for token in tokens_list]
        valid_tokens = tokens
        
        # 确保 index 是有效的索引
        if index and 1 <= index <= len(valid_tokens):
            
            # 获取对应的 access_token
            token_info = valid_tokens[index - 1]
            
            access_token = token_info['access_token']

            email = token_info['email']

            # 注册 token 并获取对应的 token_key
            token_key = register_token(access_token, unique_name)
            # token_key = None

            if not token_key:
                # 更新 chatToken.json 中对应条目的 status 为 false
                token = ChatToken.query.filter(ChatToken.access_token == access_token).first()
                token.status = False
                db.session.commit()

                # 清除用量表中对应的access_token记录
                records_to_delete = Record.query.filter_by(access_token=access_token).all()
                for record in records_to_delete:
                    db.session.delete(record)
                db.session.commit()

                return jsonify({
                    "status": "error",
                    "message": "账号失效了，换一个吧"
                }), 400

            # 检查是否存在相同的shared_token
            if not Record.query.filter_by(shared_token=token_key).first():
                new_record = Record(
                    username=unique_name,
                    email=email,
                    access_token=access_token,
                    shared_token=token_key
                )
                db.session.add(new_record)
                db.session.commit()

            # 获取 OAuth 登录 URL
            logurl = getoauth(token_key)


            return jsonify({
                "status": "success",
                "login_url": logurl
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid index."
            }), 400
    else:
        # tokens = load_cltoken()
        tokens_list = ClaudeToken.query.all()
        tokens = [token.to_dict() for token in tokens_list]
        valid_tokens = tokens

        # 确保 index 是有效的索引
        if index and 1 <= index <= len(valid_tokens):
            
            # 获取对应的 token
            token_info = valid_tokens[index - 1]
            
            skToken = token_info['skToken']

            # 获取登录链接 
            logurl = get_claude_login_url(skToken, unique_name)
            if not logurl:
                # 更新 chatToken.json 中对应条目的 status 为 false
                token = ClaudeToken.query.filter(ClaudeToken.skToken == skToken).first()
                token.status = False
                db.session.commit()

                return jsonify({
                    "status": "error",
                    "message": "账号失效了，换一个吧"
                }), 400
            
            return jsonify({
                "status": "success",
                "login_url": logurl
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid index."
            }), 400