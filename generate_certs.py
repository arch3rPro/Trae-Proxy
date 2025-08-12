#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import tempfile
import atexit
import shutil

# 临时文件列表，用于退出时清理
temp_files = []

def error(message):
    """打印错误信息并退出"""
    print(f"错误: {message}", file=sys.stderr)
    sys.exit(1)

def run_command(command, check=True):
    """运行命令并检查返回码"""
    print(f"执行命令: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and result.returncode != 0:
        error(f"命令执行失败: {command}\n{result.stderr}")
    return result

def create_temp_file(content):
    """创建临时文件并返回其路径"""
    fd, path = tempfile.mkstemp()
    os.write(fd, content.encode('utf-8'))
    os.close(fd)
    temp_files.append(path)
    return path

def cleanup_temp_files():
    """清理所有临时文件"""
    for path in temp_files:
        try:
            os.unlink(path)
        except:
            pass

# 注册退出时的清理函数
atexit.register(cleanup_temp_files)

def check_openssl():
    """检查OpenSSL是否已安装"""
    try:
        run_command("openssl version")
    except:
        error("未找到OpenSSL。请确保OpenSSL已安装并在PATH中。")

def create_default_config_files(domain="api.openai.com"):
    """创建默认的OpenSSL配置文件"""
    # 创建ca目录（如果不存在）
    os.makedirs("ca", exist_ok=True)
    
    # 基本OpenSSL配置
    openssl_cnf = """
[ req ]
default_bits        = 2048
default_md          = sha256
default_keyfile     = privkey.pem
distinguished_name  = req_distinguished_name
req_extensions      = v3_req
x509_extensions     = v3_ca

[ req_distinguished_name ]
countryName                     = 国家代码 (2字符)
countryName_default             = CN
stateOrProvinceName             = 省/州
stateOrProvinceName_default     = State
localityName                    = 城市
localityName_default            = City
organizationName                = 组织名称
organizationName_default        = Organization
organizationalUnitName          = 组织单位名称
organizationalUnitName_default  = Unit
commonName                      = 通用名称
commonName_max                  = 64
commonName_default              = localhost
emailAddress                    = 电子邮件地址
emailAddress_max                = 64
emailAddress_default            = admin@example.com

[ v3_req ]
basicConstraints       = CA:FALSE
keyUsage               = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth
subjectAltName         = @alt_names

[ v3_ca ]
basicConstraints       = critical, CA:true
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always, issuer:always
keyUsage               = cRLSign, keyCertSign, digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
"""
    
    # CA证书扩展配置（不包含subjectAltName）
    v3_ca_cnf = """
[ v3_ca ]
basicConstraints       = critical, CA:true
subjectKeyIdentifier   = hash
authorityKeyIdentifier = keyid:always, issuer:always
keyUsage               = cRLSign, keyCertSign, digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
"""
    
    # 服务器证书扩展配置
    v3_req_cnf = """
[ v3_req ]
basicConstraints       = CA:FALSE
keyUsage               = nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage       = serverAuth
subjectAltName         = @alt_names
"""
    
    # 写入配置文件（如果不存在）
    if not os.path.exists("ca/openssl.cnf"):
        with open("ca/openssl.cnf", "w") as f:
            f.write(openssl_cnf)
    
    if not os.path.exists("ca/v3_ca.cnf"):
        with open("ca/v3_ca.cnf", "w") as f:
            f.write(v3_ca_cnf)
    
    if not os.path.exists("ca/v3_req.cnf"):
        with open("ca/v3_req.cnf", "w") as f:
            f.write(v3_req_cnf)
    
    # 主题备用名称配置
    domain_cnf = f"""
[ alt_names ]
DNS.1 = {domain}
"""
    
    # 证书主题信息
    domain_subj = f"/C=CN/ST=State/L=City/O=Organization/OU=Unit/CN={domain}"
    
    # 写入域名特定配置
    if not os.path.exists(f"ca/{domain}.cnf"):
        with open(f"ca/{domain}.cnf", "w") as f:
            f.write(domain_cnf)
    
    if not os.path.exists(f"ca/{domain}.subj"):
        with open(f"ca/{domain}.subj", "w") as f:
            f.write(domain_subj)

def generate_ca_cert():
    """生成CA证书和私钥"""
    print("生成CA证书...")
    
    # 生成CA私钥
    run_command("openssl genrsa -out ca/ca.key 2048")
    
    # 使用简单的命令生成自签名CA证书，避免复杂的配置文件
    run_command("openssl req -new -x509 -days 36500 -key ca/ca.key -out ca/ca.crt -subj \"/C=CN/ST=State/L=City/O=TraeProxy CA/OU=TraeProxy/CN=TraeProxy Root CA\"")
    
    print("CA证书生成完成")

def generate_server_cert(domain="api.openai.com"):
    """为指定域名生成服务器证书"""
    print(f"为域名 {domain} 生成服务器证书...")
    
    # 检查必要文件
    required_files = [
        "ca/openssl.cnf",
        "ca/v3_req.cnf",
        f"ca/{domain}.cnf",
        f"ca/{domain}.subj",
        "ca/ca.key",
        "ca/ca.crt"
    ]
    
    for file in required_files:
        if not os.path.exists(file):
            error(f"缺少必要文件: {file}")
    
    # 读取配置文件
    with open("ca/openssl.cnf", "r") as f:
        openssl_cnf = f.read()
    
    with open("ca/v3_req.cnf", "r") as f:
        v3_req_cnf = f.read()
    
    with open(f"ca/{domain}.cnf", "r") as f:
        domain_cnf = f.read()
    
    with open(f"ca/{domain}.subj", "r") as f:
        domain_subj = f.read().strip()
    
    # 合并配置
    merged_cnf = openssl_cnf + "\n" + v3_req_cnf + "\n" + domain_cnf
    temp_cnf = create_temp_file(merged_cnf)
    
    # 生成服务器私钥
    run_command(f"openssl genrsa -out ca/{domain}.key 2048")
    
    # 转换为PKCS#8格式
    run_command(f"openssl pkcs8 -topk8 -nocrypt -in ca/{domain}.key -out ca/{domain}.key.pkcs8")
    shutil.move(f"ca/{domain}.key.pkcs8", f"ca/{domain}.key")
    
    # 生成CSR
    run_command(f"openssl req -reqexts v3_req -sha256 -new -key ca/{domain}.key -out ca/{domain}.csr -config {temp_cnf} -subj \"{domain_subj}\"")
    
    # 使用CA签署证书
    run_command(f"openssl x509 -req -days 365 -in ca/{domain}.csr -CA ca/ca.crt -CAkey ca/ca.key -CAcreateserial -out ca/{domain}.crt -extfile {temp_cnf} -extensions v3_req")
    
    # 删除CSR文件
    os.remove(f"ca/{domain}.csr")
    
    print(f"服务器证书生成完成: ca/{domain}.crt")

def main():
    """主函数"""
    # 解析命令行参数
    domain = "api.openai.com"
    if len(sys.argv) > 1 and sys.argv[1] == "--domain" and len(sys.argv) > 2:
        domain = sys.argv[2]
    
    # 检查OpenSSL
    check_openssl()
    
    # 创建默认配置文件
    create_default_config_files(domain)
    
    # 生成CA证书
    generate_ca_cert()
    
    # 生成服务器证书
    generate_server_cert(domain)
    
    print("所有证书生成完成")

if __name__ == "__main__":
    main()