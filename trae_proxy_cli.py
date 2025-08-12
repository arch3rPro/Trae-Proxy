#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import argparse
import yaml
import json
import logging
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trae_proxy_cli')

# 全局变量
config_file = "config.yaml"

def load_config():
    """从配置文件加载配置"""
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data
        
        # 如果配置为空，返回默认配置
        return {
            "domain": "api.openai.com",
            "apis": [
                {
                    "name": "默认OpenAI API",
                    "endpoint": "https://api.openai.com",
                    "custom_model_id": "gpt-4",
                    "target_model_id": "gpt-4",
                    "stream_mode": None,
                    "active": True
                }
            ],
            "server": {
                "port": 443,
                "debug": True
            }
        }
    except Exception as e:
        logger.error(f"加载配置失败: {str(e)}")
        return {
            "domain": "api.openai.com",
            "apis": [
                {
                    "name": "默认OpenAI API",
                    "endpoint": "https://api.openai.com",
                    "custom_model_id": "gpt-4",
                    "target_model_id": "gpt-4",
                    "stream_mode": None,
                    "active": True
                }
            ],
            "server": {
                "port": 443,
                "debug": True
            }
        }

def save_config(config):
    """保存配置到配置文件"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        logger.info(f"配置已保存到 {config_file}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def list_apis():
    """列出所有API配置"""
    config = load_config()
    apis = config.get('apis', [])
    
    print("\n当前API配置列表:")
    print("-" * 80)
    print(f"代理域名: {config.get('domain', 'api.openai.com')}")
    print("-" * 80)
    
    for i, api in enumerate(apis):
        status = "✓ 激活" if api.get('active', False) else "✗ 未激活"
        print(f"{i+1}. {api['name']} [{status}]")
        print(f"   后端API: {api.get('endpoint', '')}")
        print(f"   自定义模型ID: {api.get('custom_model_id', '')}")
        print(f"   目标模型ID: {api.get('target_model_id', '')}")
        print(f"   流模式: {api.get('stream_mode', 'None')}")
        print("-" * 80)
    
    return config

def add_api(name, endpoint, custom_model, target_model, stream_mode, active=False):
    """添加新API配置"""
    config = load_config()
    
    # 验证URL格式
    try:
        parsed_url = urlparse(endpoint)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error("无效的API URL格式")
            return False
    except:
        logger.error("无效的API URL格式")
        return False
    
    # 处理流模式
    if stream_mode == "true":
        stream_mode = "true"
    elif stream_mode == "false":
        stream_mode = "false"
    else:
        stream_mode = None
    
    # 创建新API配置
    new_api = {
        'name': name,
        'endpoint': endpoint,
        'custom_model_id': custom_model,
        'target_model_id': target_model,
        'stream_mode': stream_mode,
        'active': active
    }
    
    # 添加到API列表
    if 'apis' not in config:
        config['apis'] = []
    
    config['apis'].append(new_api)
    
    # 保存配置
    if save_config(config):
        logger.info(f"已添加新API配置: {name}")
        return True
    return False

def remove_api(index):
    """删除API配置"""
    config = load_config()
    apis = config.get('apis', [])
    
    # 检查索引是否有效
    if index < 0 or index >= len(apis):
        logger.error(f"无效的API索引: {index}")
        return False
    
    # 检查是否至少保留一个API配置
    if len(apis) <= 1:
        logger.error("至少需要保留一个API配置")
        return False
    
    # 删除API配置
    removed = apis.pop(index)
    config['apis'] = apis
    
    # 保存配置
    if save_config(config):
        logger.info(f"已删除API配置: {removed['name']}")
        return True
    return False

def update_api(index, name=None, endpoint=None, custom_model=None, target_model=None, stream_mode=None, active=None):
    """更新API配置"""
    config = load_config()
    apis = config.get('apis', [])
    
    # 检查索引是否有效
    if index < 0 or index >= len(apis):
        logger.error(f"无效的API索引: {index}")
        return False
    
    # 获取当前API配置
    api = apis[index]
    
    # 更新API配置
    if name is not None:
        api['name'] = name
    
    if endpoint is not None:
        # 验证URL格式
        try:
            parsed_url = urlparse(endpoint)
            if not parsed_url.scheme or not parsed_url.netloc:
                logger.error("无效的API URL格式")
                return False
            api['endpoint'] = endpoint
        except:
            logger.error("无效的API URL格式")
            return False
    
    if custom_model is not None:
        api['custom_model_id'] = custom_model
    
    if target_model is not None:
        api['target_model_id'] = target_model
    
    if stream_mode is not None:
        if stream_mode == "true":
            api['stream_mode'] = "true"
        elif stream_mode == "false":
            api['stream_mode'] = "false"
        else:
            api['stream_mode'] = None
    
    if active is not None:
        api['active'] = active
        
        # 如果激活当前API，则禁用其他API
        if active:
            for i, other_api in enumerate(apis):
                if i != index:
                    other_api['active'] = False
    
    # 保存配置
    if save_config(config):
        logger.info(f"已更新API配置: {api['name']}")
        return True
    return False

def activate_api(index):
    """激活指定API配置"""
    config = load_config()
    apis = config.get('apis', [])
    
    # 检查索引是否有效
    if index < 0 or index >= len(apis):
        logger.error(f"无效的API索引: {index}")
        return False
    
    # 禁用所有API
    for api in apis:
        api['active'] = False
    
    # 激活指定API
    apis[index]['active'] = True
    
    # 保存配置
    if save_config(config):
        logger.info(f"已激活API配置: {apis[index]['name']}")
        return True
    return False

def update_domain(domain):
    """更新代理域名"""
    config = load_config()
    
    # 更新域名
    config['domain'] = domain
    
    # 保存配置
    if save_config(config):
        logger.info(f"已更新代理域名: {domain}")
        return True
    return False

def generate_certificates(domain=None):
    """生成证书"""
    if domain is None:
        config = load_config()
        domain = config.get('domain', 'api.openai.com')
    
    logger.info(f"为域名 {domain} 生成证书...")
    
    # 创建ca目录（如果不存在）
    os.makedirs("ca", exist_ok=True)
    
    # 运行证书生成脚本
    cmd = [sys.executable, "generate_certs.py", "--domain", domain]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # 读取输出
    for line in process.stdout:
        logger.info(line.strip())
    
    # 等待进程结束
    process.wait()
    
    if process.returncode == 0:
        logger.info("证书生成成功")
        return True
    else:
        logger.error(f"证书生成失败，返回码: {process.returncode}")
        return False

def start_proxy_server(debug=False):
    """启动代理服务器"""
    config = load_config()
    domain = config.get('domain', 'api.openai.com')
    apis = config.get('apis', [])
    
    # 检查是否有激活的API配置
    active_apis = [api for api in apis if api.get('active', False)]
    if not active_apis:
        if apis:
            logger.warning(f"未找到激活的API配置，将激活第一个配置: {apis[0]['name']}")
            apis[0]['active'] = True
            active_apis = [apis[0]]
        else:
            logger.error("未找到任何API配置")
            return False
    
    logger.info(f"多后端配置已启用，共 {len(apis)} 个API配置，{len(active_apis)} 个激活")
    for api in apis:
        status = "✓ 激活" if api.get('active', False) else "✗ 未激活"
        logger.info(f"  - {api['name']} [{status}]: {api.get('endpoint', '')} -> {api.get('custom_model_id', '')}")
    
    # 检查证书文件
    cert_file = os.path.join("ca", f"{domain}.crt")
    key_file = os.path.join("ca", f"{domain}.key")
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        logger.error(f"证书文件不存在: {cert_file} 或 {key_file}")
        logger.info("正在生成证书...")
        if not generate_certificates(domain):
            return False
    
    # 构建命令 - 不再传递特定的API参数，让代理服务器根据配置文件自动选择
    cmd = [
        sys.executable,
        "trae_proxy.py",
        "--cert", cert_file,
        "--key", key_file
    ]
    
    if debug or config.get('server', {}).get('debug', False):
        cmd.append("--debug")
    
    # 注意：trae_proxy.py 硬编码使用443端口，不支持--port参数
    # port = config.get('server', {}).get('port', 443)
    # cmd.extend(["--port", str(port)])
    
    logger.info(f"启动多后端代理服务器: {' '.join(cmd)}")
    logger.info("代理服务器将根据请求的模型ID自动选择后端API")
    
    # 执行命令
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 读取输出
        for line in process.stdout:
            print(line.strip())
        
        # 等待进程结束
        process.wait()
        
        if process.returncode != 0:
            logger.error(f"代理服务器异常退出，返回码: {process.returncode}")
            return False
        
        return True
        
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在停止代理服务器...")
        process.terminate()
        process.wait()
        logger.info("代理服务器已停止")
        return True
        
    except Exception as e:
        logger.error(f"启动代理服务器过程中发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Trae代理命令行工具')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出所有API配置')
    
    # add命令
    add_parser = subparsers.add_parser('add', help='添加新API配置')
    add_parser.add_argument('--name', required=True, help='配置名称')
    add_parser.add_argument('--endpoint', required=True, help='后端API URL')
    add_parser.add_argument('--custom-model', required=True, help='自定义模型ID')
    add_parser.add_argument('--target-model', required=True, help='目标模型ID')
    add_parser.add_argument('--stream-mode', choices=['true', 'false', 'none'], default='none', help='流模式')
    add_parser.add_argument('--active', action='store_true', help='激活此API配置')
    
    # remove命令
    remove_parser = subparsers.add_parser('remove', help='删除API配置')
    remove_parser.add_argument('--index', type=int, required=True, help='API索引（从0开始）')
    
    # update命令
    update_parser = subparsers.add_parser('update', help='更新API配置')
    update_parser.add_argument('--index', type=int, required=True, help='API索引（从0开始）')
    update_parser.add_argument('--name', help='配置名称')
    update_parser.add_argument('--endpoint', help='后端API URL')
    update_parser.add_argument('--custom-model', help='自定义模型ID')
    update_parser.add_argument('--target-model', help='目标模型ID')
    update_parser.add_argument('--stream-mode', choices=['true', 'false', 'none'], help='流模式')
    update_parser.add_argument('--active', action='store_true', help='激活此API配置')
    
    # activate命令
    activate_parser = subparsers.add_parser('activate', help='激活API配置')
    activate_parser.add_argument('--index', type=int, required=True, help='API索引（从0开始）')
    
    # domain命令
    domain_parser = subparsers.add_parser('domain', help='更新代理域名')
    domain_parser.add_argument('--name', required=True, help='域名')
    
    # cert命令
    cert_parser = subparsers.add_parser('cert', help='生成证书')
    cert_parser.add_argument('--domain', help='域名（默认使用配置中的域名）')
    
    # start命令
    start_parser = subparsers.add_parser('start', help='启动代理服务器')
    start_parser.add_argument('--debug', action='store_true', help='启用调试模式')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 执行命令
    if args.command == 'list':
        list_apis()
    
    elif args.command == 'add':
        stream_mode = None if args.stream_mode == 'none' else args.stream_mode
        add_api(args.name, args.endpoint, args.custom_model, args.target_model, stream_mode, args.active)
    
    elif args.command == 'remove':
        remove_api(args.index)
    
    elif args.command == 'update':
        stream_mode = None
        if hasattr(args, 'stream_mode') and args.stream_mode is not None:
            stream_mode = None if args.stream_mode == 'none' else args.stream_mode
        update_api(args.index, args.name, args.endpoint, args.custom_model, args.target_model, stream_mode, args.active)
    
    elif args.command == 'activate':
        activate_api(args.index)
    
    elif args.command == 'domain':
        update_domain(args.name)
    
    elif args.command == 'cert':
        generate_certificates(args.domain)
    
    elif args.command == 'start':
        start_proxy_server(args.debug)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()