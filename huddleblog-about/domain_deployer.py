
"""
使用说明 project_files: 4个文件（3个协议页和logo.png）的目录
python3 domain_deployer.py ./project_files
"""


import os
import shutil
import random
import string
import argparse
from pathlib import Path

def generate_random_filename(original_name, length=10):
    """
    生成随机文件名，保留原始文件扩展名
    """
    name, ext = os.path.splitext(original_name)
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{random_string}{ext}"

def create_domain_folder(domain):
    """
    根据域名创建文件夹
    命名规则: BBBCCC-about
    """
    parts = domain.split('.')
    if len(parts) >= 3:
        folder_name = f"{parts[1]}{parts[2]}-about"
    elif len(parts) == 2:
        folder_name = f"{parts[1]}-about"
    else:
        folder_name = f"{domain}-about"
    
    return folder_name

def rename_files_and_get_urls(domain_folder, domain, rename_files=False):
    """Return fixed HTTP protocol URLs without changing any file names.

    ``rename_files`` remains accepted for compatibility with older callers, but
    is intentionally ignored: the three published page names are part of the
    contract and must remain byte-for-byte addressable.
    """
    del domain_folder, rename_files
    return {
        'privacy_policy': f"http://{domain}/PrivacyPolicy.html",
        'terms_conditions': f"http://{domain}/Terms&Conditions.html",
        'support': f"http://{domain}/Support.html",
    }

def git_operations(domain_folder):
    """Keep protocol-page preparation local; never clone, commit, or push."""
    # The workflow does not publish protocol pages and must not touch a remote
    # repository from this helper. Final project Git association is handled only
    # after all acceptance gates, on the user-provided repository URL, by the
    # main Flutter workflow. The generated folder remains available to the caller.
    print("跳过远程 Git 部署：协议页仅做本地整理，验收后的 Git 交接由主流程执行。")
    return True

def main():
    """
    主函数
    """
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='自动化部署脚本')
    parser.add_argument('path', help='包含三个协议页和 logo.png 的目录路径')
    parser.add_argument('--domain', help='H5域名 (例如: AAA.BBB.CCC)', default=None)
    args = parser.parse_args()
    
    # 获取文件路径
    source_path = args.path
    
    # 检查路径是否存在
    if not os.path.exists(source_path):
        print(f"错误：路径 '{source_path}' 不存在")
        return
    
    if not os.path.isdir(source_path):
        print(f"错误：'{source_path}' 不是一个目录")
        return
    
    # 必需文件列表：三个协议页和品牌图片；站点目录不生成首页
    required_files = ['PrivacyPolicy.html', 'Support.html', 'Terms&Conditions.html', 'logo.png']
    all_files = required_files
    
    # 检查所有必需文件是否存在
    missing_files = []
    for filename in required_files:
        file_path = os.path.join(source_path, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    
    if missing_files:
        print(f"错误：在路径 '{source_path}' 中缺少以下文件: {', '.join(missing_files)}")
        print(f"请确保以下文件存在: {', '.join(required_files)}")
        return
    
    # 检查可选文件
    existing_files = []
    for filename in all_files:
        file_path = os.path.join(source_path, filename)
        if os.path.exists(file_path):
            existing_files.append(filename)
    
    print(f"使用文件路径: {source_path}")
    
    # 获取域名输入
    if args.domain:
        domain = args.domain.strip()
    else:
        domain = input("请输入H5域名 (例如: AAA.BBB.CCC): ").strip()
    if not domain:
        print("错误：域名不能为空")
        return
    
    # 协议文件名固定，不提供重命名选项；域名仅用于生成可搜索的 HTTP 模板。
    rename_choice = False

    # 创建域名文件夹
    domain_folder_name = create_domain_folder(domain)
    if os.path.exists(domain_folder_name):
        shutil.rmtree(domain_folder_name)
    os.makedirs(domain_folder_name, exist_ok=True)
    
    # 从指定路径复制文件到域名文件夹
    print("正在复制文件...")
    for filename in existing_files:
        source_file = os.path.join(source_path, filename)
        if filename == 'logo.png':
            # 为logo.png创建img文件夹
            img_folder = os.path.join(domain_folder_name, 'img')
            os.makedirs(img_folder, exist_ok=True)
            shutil.copy2(source_file, os.path.join(img_folder, 'logo.png'))
        else:
            shutil.copy2(source_file, os.path.join(domain_folder_name, filename))
    
    # 保留固定文件名并获取 HTTP 模板 URL。
    print("保留协议文件名：PrivacyPolicy.html、Terms&Conditions.html、Support.html")
    urls = rename_files_and_get_urls(domain_folder_name, domain, rename_choice)
    
    # 保持协议页本地交付；不克隆、提交或推送任何远程仓库。
    success = git_operations(domain_folder_name)
    
    # 清理域名文件夹
    if os.path.exists(domain_folder_name):
        shutil.rmtree(domain_folder_name)
    
    # 输出结果
    print("\n" + "="*50)
    if success:
        print("处理完成！")
    else:
        print("处理完成（但有警告）")
    print("="*50)
    print(f"隐私政策: {urls['privacy_policy']}")
    print(f"用户协议: {urls['terms_conditions']}")
    print(f"Support: {urls['support']}")
    print("="*50)

if __name__ == "__main__":
    main()
