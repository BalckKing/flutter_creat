
"""
使用说明 project_files: 5个文件的目录
python3 domain_deployer.py ./project_files
"""


import os
import shutil
import random
import string
import subprocess
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

def rename_files_and_get_urls(domain_folder, domain, rename_files=True):
    """
    重命名文件并返回对应的URL
    """
    files_to_rename = ['PrivacyPolicy.html', 'Terms&Conditions.html']
    renamed_files = {}
    
    for filename in files_to_rename:
        file_path = os.path.join(domain_folder, filename)
        if os.path.exists(file_path):
            if rename_files:
                new_filename = generate_random_filename(filename)
                new_file_path = os.path.join(domain_folder, new_filename)
                os.rename(file_path, new_file_path)
                
                # 存储映射关系
                if filename == 'PrivacyPolicy.html':
                    renamed_files['privacy_policy'] = new_filename
                elif filename == 'Terms&Conditions.html':
                    renamed_files['terms_conditions'] = new_filename
            else:
                # 如果不重命名，使用原文件名
                if filename == 'PrivacyPolicy.html':
                    renamed_files['privacy_policy'] = filename
                elif filename == 'Terms&Conditions.html':
                    renamed_files['terms_conditions'] = filename
    
    # 构建URLs
    urls = {
        'privacy_policy': f"https://{domain}/{renamed_files.get('privacy_policy', 'PrivacyPolicy.html')}",
        'terms_conditions': f"https://{domain}/{renamed_files.get('terms_conditions', 'Terms&Conditions.html')}",
        'support': f"https://{domain}/Support.html",
        'index': f"https://{domain}/index.html"
    }
    
    return urls

def get_git_user_info():
    """
    获取Git用户信息
    """
    user_info = {'name': '', 'email': ''}
    
    try:
        # 获取Git用户名
        result = subprocess.run(['git', 'config', 'user.name'],
                              capture_output=True, text=True, check=True)
        user_info['name'] = result.stdout.strip()
    except:
        user_info['name'] = 'Auto Script'
    
    try:
        # 获取Git邮箱
        result = subprocess.run(['git', 'config', 'user.email'],
                              capture_output=True, text=True, check=True)
        user_info['email'] = result.stdout.strip()
    except:
        user_info['email'] = 'script@example.com'
    
    return user_info

def get_rename_choice(interactive=True):
    """
    获取用户是否重命名文件的选择
    """
    if not interactive:
        return False  # 非交互式环境默认不重命名
    
    while True:
        try:
            choice = input("是否重命名 PrivacyPolicy.html 和 Terms&Conditions.html 文件？(y/n, 默认n): ").strip().lower()
            if choice in ['y', 'yes']:
                return True
            elif choice in ['n', 'no', '']:
                return False
            else:
                print("请输入 y 或 n")
        except EOFError:
            # 非交互式环境，默认不重命名
            return False

def handle_git_conflicts(local_repo_path):
    """
    处理Git冲突
    """
    print("检测到冲突，正在处理...")
    
    backup_dir = os.path.join(local_repo_path, "git_backup")
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # 获取有冲突的文件
        result = subprocess.run(['git', 'status', '--porcelain'],
                              cwd=local_repo_path, capture_output=True, text=True, check=True)
        
        conflicted_files = []
        for line in result.stdout.split('\n'):
            if line and any(line.startswith(prefix) for prefix in ['UU', 'AA', 'DD', 'DU', 'UD']):
                filename = line[3:].strip()
                conflicted_files.append(filename)
        
        # 备份有冲突的文件
        for file_path in conflicted_files:
            full_path = os.path.join(local_repo_path, file_path)
            if os.path.exists(full_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(full_path, backup_path)
                print(f"已备份: {file_path}")
        
        # 放弃当前更改，重新拉取
        print("正在重置本地更改...")
        subprocess.run(['git', 'reset', '--hard', 'HEAD'],
                      cwd=local_repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'clean', '-fd'],
                      cwd=local_repo_path, check=True, capture_output=True)
        
        # 重新拉取
        print("重新拉取远程更改...")
        subprocess.run(['git', 'pull', 'origin', 'master'],
                      cwd=local_repo_path, check=True, capture_output=True)
        
        # 恢复备份的文件
        if os.path.exists(backup_dir) and os.listdir(backup_dir):
            print("正在恢复您的更改...")
            for file_name in os.listdir(backup_dir):
                src = os.path.join(backup_dir, file_name)
                dest = os.path.join(local_repo_path, file_name)
                shutil.copy2(src, dest)
        
        return True
        
    except Exception as e:
        print(f"处理冲突时出错: {e}")
        return False
    finally:
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)

def git_operations(domain_folder):
    """
    执行Git操作
    """
    # Git仓库地址（请替换为实际的仓库地址）
    repo_url = "https://codeup.aliyun.com/6366640f0cd435624679b545/chatting_agreement/chatting_lingfeng_agreement.git"  # 在这里替换你的仓库地址
    local_repo_path = "temp_repo"
    
    max_retries = 3
    retry_count = 0
    success = False
    original_dir = os.getcwd()
    
    # 获取Git用户信息
    git_user = get_git_user_info()
    print(f"使用Git用户: {git_user['name']} <{git_user['email']}>")
    
    try:
        while retry_count < max_retries:
            try:
                # 清理临时目录（如果存在）
                if os.path.exists(local_repo_path):
                    shutil.rmtree(local_repo_path)
                
                # 克隆仓库
                print("正在克隆Git仓库...")
                subprocess.run(['git', 'clone', repo_url, local_repo_path],
                             check=True, capture_output=True)
                
                # 切换到仓库目录
                os.chdir(local_repo_path)
                
                print("使用分支: master")
                
                # 配置Git用户信息（使用获取到的用户信息）
                try:
                    subprocess.run(['git', 'config', 'user.email', git_user['email']],
                                 check=True, capture_output=True)
                    subprocess.run(['git', 'config', 'user.name', git_user['name']],
                                 check=True, capture_output=True)
                except:
                    pass
                
                # 拉取最新更改
                print("正在拉取最新更改...")
                subprocess.run(['git', 'pull', 'origin', 'master'],
                             check=True, capture_output=True)
                
                # 创建linfeng文件夹（在仓库根目录）
                linfeng_path = "linfeng"
                os.makedirs(linfeng_path, exist_ok=True)
                
                # 复制域名文件夹到linfeng目录
                destination_path = os.path.join(linfeng_path, os.path.basename(domain_folder))
                if os.path.exists(destination_path):
                    shutil.rmtree(destination_path)
                
                # 直接复制，不需要切换目录
                source_folder = os.path.join(original_dir, domain_folder)
                shutil.copytree(source_folder, destination_path)
                
                # Git操作
                print("正在添加文件到Git...")
                subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                
                # 检查是否有更改
                result = subprocess.run(['git', 'status', '--porcelain'],
                                      capture_output=True, text=True, check=True)
                if not result.stdout.strip():
                    print("没有更改需要提交")
                    success = True
                    break
                
                print("正在提交更改...")
                commit_message = f'Add {os.path.basename(domain_folder)}'
                subprocess.run(['git', 'commit', '-m', commit_message],
                             check=True, capture_output=True)
                
                print("正在推送到远程仓库...")
                subprocess.run(['git', 'push', 'origin', 'master'],
                             check=True, capture_output=True)
                
                print("Git操作完成！")
                success = True
                break
                
            except subprocess.CalledProcessError as e:
                retry_count += 1
                error_output = e.stderr.decode() if e.stderr else str(e)
                print(f"Git操作出错 (尝试 {retry_count}/{max_retries}): {error_output}")
                
                # 确保回到原始目录
                os.chdir(original_dir)
                
                if "conflict" in error_output.lower():
                    print("检测到冲突，正在处理...")
                    if handle_git_conflicts(local_repo_path):
                        # 冲突处理后需要重新切换到仓库目录
                        os.chdir(local_repo_path)
                        continue
                elif retry_count < max_retries:
                    print("等待2秒后重试...")
                    import time
                    time.sleep(2)
                else:
                    print("达到最大重试次数，操作失败")
                    break
                    
    except Exception as e:
        print(f"Git操作过程中发生异常: {e}")
    finally:
        # 确保回到原始目录
        os.chdir(original_dir)
        
        # 清理临时仓库
        if os.path.exists(local_repo_path):
            print("正在清理临时仓库...")
            shutil.rmtree(local_repo_path)
    
    return success

def main():
    """
    主函数
    """
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='自动化部署脚本')
    parser.add_argument('path', help='包含5个必需文件的目录路径')
    parser.add_argument('--domain', help='H5域名 (例如: AAA.BBB.CCC)', default=None)
    parser.add_argument('--rename', action='store_true', help='重命名 PrivacyPolicy.html 和 Terms&Conditions.html 文件')
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
    
    # 必需文件列表（不包括可选的index.html）
    required_files = ['PrivacyPolicy.html', 'Support.html', 'Terms&Conditions.html', 'logo.png']
    # 可选文件列表
    optional_files = ['index.html']
    # 所有文件列表
    all_files = required_files + optional_files
    
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
    
    if 'index.html' not in existing_files:
        print("注意：index.html 文件不存在，将跳过该文件")
    
    print(f"使用文件路径: {source_path}")
    
    # 获取域名输入
    if args.domain:
        domain = args.domain.strip()
    else:
        domain = input("请输入H5域名 (例如: AAA.BBB.CCC): ").strip()
    if not domain:
        print("错误：域名不能为空")
        return
    
    # 询问是否重命名文件
    if args.rename:
        rename_choice = True
    else:
        # 如果通过命令行提供了域名，则使用非交互模式
        rename_choice = get_rename_choice(interactive=not args.domain)
    
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
    
    # 重命名文件并获取URLs
    if rename_choice:
        print("正在重命名文件...")
    else:
        print("跳过文件重命名...")
    
    urls = rename_files_and_get_urls(domain_folder_name, domain, rename_choice)
    
    # 执行Git操作
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
    if 'index.html' in existing_files:
        print(f"首页: {urls['index']}")
    print(f"隐私政策: {urls['privacy_policy']}")
    print(f"用户协议: {urls['terms_conditions']}")
    print(f"Support: {urls['support']}")
    print("="*50)

if __name__ == "__main__":
    main()
