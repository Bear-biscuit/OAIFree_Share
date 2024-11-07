import sys
import os

# 将 `flasks` 目录的上一级目录加入 Python 路径
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from flasks import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080, debug=True)
