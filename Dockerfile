FROM python:3.9-slim

WORKDIR /app

# 替换apt源为中国源
RUN echo "deb https://mirrors.aliyun.com/debian/ bullseye main non-free contrib" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bullseye-updates main non-free contrib" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bullseye-security main non-free contrib" >> /etc/apt/sources.list

# 安装依赖
RUN apt-get update && apt-get install -y \
    openssl \
    && rm -rf /var/lib/apt/lists/*

# 配置pip使用中国源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY generate_certs.py .
COPY trae_proxy.py .
COPY trae_proxy_cli.py .
COPY config.yaml .

# 创建证书目录
RUN mkdir -p ca

# 暴露443端口
EXPOSE 443

# 设置启动命令
CMD ["python", "trae_proxy_cli.py", "start"]