# 使用官方 Python 镜像作为基础镜像
FROM python:3.9-slim

# 安装 MySQL 客户端库和构建工具
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制本地文件到容器中的工作目录
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# 暴露 5000 端口
EXPOSE 5000

# 启动 Flask 应用
CMD ["flask", "run"]
