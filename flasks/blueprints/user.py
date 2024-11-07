from flask import Blueprint,current_app, render_template, session, request, jsonify
from ..utils import login_required
from ..models import User,db
from werkzeug.security import generate_password_hash, check_password_hash
bp = Blueprint('user', __name__)

@bp.route('/profile')
@login_required
def index():
    user = User.query.filter_by(username=session['username']).first()

    return render_template('user/profile.html', user=user,email=current_app.config.get('DOMAIN_EMAIL'),title=current_app.config.get('DOMAIN_NAME'))

# 用户更新密码路由
@bp.route('/api/user/<int:user_id>', methods=['PUT'])
@login_required
def uppassword(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if(session.get('user_id')):
        try:
            if user and check_password_hash(user.password, data['current_password']):
                user.password = generate_password_hash(data['password'])
                db.session.commit()
                return jsonify({'message': '密码更新成功'}), 200
            else:
                return jsonify({'message': '原始密码错误'}), 400

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': f"{user_id}匹配失败"}), 400
    

    
    
# 两步验证
@bp.route('/api/two/<int:user_id>', methods=['PUT'])
@login_required
def two_fa(user_id):
    if not current_app.config.get('REGISTER'):
        return jsonify({'message': '未配置邮箱服务'}), 200
    user = User.query.get_or_404(user_id)
    if(session.get('user_id')):

        try:
            if user and user.two_fa:
                user.two_fa = False
                db.session.commit()
                return jsonify({'message': '两步验证已关闭'}), 200
            else:
                user.two_fa = True
                db.session.commit()
                return jsonify({'message': '两步验证已开启'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': f"{user_id}匹配失败"}), 400