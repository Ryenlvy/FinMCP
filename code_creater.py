import os
import json
import re
from openai import OpenAI

# 配置API密钥和客户端
API_KEY = os.getenv("DASHSCOPE_API_KEY", "your_api_key")  # 请替换为您的实际API密钥
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

def read_file_content(file_path):
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None

def get_json_files(directory):
    """获取指定目录下的所有JSON文件"""
    json_files = []
    try:
        for file in os.listdir(directory):
            if file.endswith('.json'):
                json_files.append(os.path.join(directory, file))
    except Exception as e:
        print(f"读取目录 {directory} 时出错: {e}")
    return json_files

def call_llm_api(prompt):
    """调用LLM API生成代码"""
    try:
        completion = client.chat.completions.create(
            model="qwen-max-latest",  # 使用通义千问最新模型
            messages=[
                {"role": "system", "content": "你是一个专业的Python开发者，擅长编写工具函数。请直接输出Python函数代码，不要包含任何Markdown格式或代码块标记（如```python或```）。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"调用API时出错: {e}")
        return None

def clean_code_output(code_text):
    """清理代码输出，移除可能的Markdown代码块标记"""
    # 移除开头的```python或```及类似标记
    code_text = re.sub(r'^```\w*\n', '', code_text)
    # 移除结尾的```
    code_text = re.sub(r'\n```$', '', code_text)
    # 移除其他可能的代码块标记
    code_text = re.sub(r'```\w*', '', code_text)
    return code_text.strip()

def extract_functions(generated_code):
    """从生成的代码中提取函数"""
    # 使用正则表达式匹配函数定义
    function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    functions = re.findall(function_pattern, generated_code)
    return functions

def ensure_directory_exists(directory):
    """确保目录存在，如果不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")

def save_functions_to_file(generated_code, output_dir, output_file):
    """将生成的函数保存到文件"""
    try:
        # 确保目录存在
        ensure_directory_exists(output_dir)
        
        # 清理代码输出
        clean_code = clean_code_output(generated_code)
        
        # 构建完整的文件路径
        full_path = os.path.join(output_dir, output_file)
        
        with open(full_path, 'w', encoding='utf-8') as file:
            file.write(clean_code)
        print(f"函数已保存到 {full_path}")
        return True
    except Exception as e:
        print(f"保存函数到文件时出错: {e}")
        return False

def generate_import_statement(functions):
    """生成导入语句和工具注册代码"""
    if not functions:
        return "没有找到函数"
    
    import_statement = f"from tools import ({', '.join(functions)})\n\n"
    tool_registrations = "\n".join([f"mcp.tool()({func})" for func in functions])
    
    return import_statement + tool_registrations

def main():
    # 定义输出目录
    output_dir = "tools_code"
    
    # 读取server.py和tools.py的内容
    server_content = read_file_content('server.py')
    tools_content = read_file_content('tools.py')
    
    if not server_content or not tools_content:
        print("无法读取必要的文件内容")
        return
    
    # 获取JSON文件列表
    json_files = get_json_files('tsanghi_docs')
    
    if not json_files:
        print("未找到JSON文件")
        return
    
    # 为每个JSON文件生成函数
    all_functions = []
    
    for json_file in json_files:
        print(f"处理文件: {json_file}")
        
        # 读取JSON内容
        json_content = read_file_content(json_file)
        if not json_content:
            continue
        
        # 构建提示
        prompt = f"""观察server.py和tools.py以及传入的json，模仿代码风格写一个新的tool function，返回的内容只能是字典，不要列表，只需要输出该函数即可，其余的都不用输出，函数命名和注释必须完整。
请直接输出Python代码，不要包含任何Markdown格式或代码块标记（如```python或```），除了代码外其余的什么都不要出现！

server.py的内容为：
{server_content}

tools.py的内容为：
{tools_content}

JSON内容为：
{json_content}
"""
        
        # 调用LLM API
        generated_code = call_llm_api(prompt)
        if not generated_code:
            continue
        
        # 提取函数名
        clean_code = clean_code_output(generated_code)
        file_functions = extract_functions(clean_code)
        all_functions.extend(file_functions)
        
        # 保存到文件
        output_file = f"generated_function_{os.path.basename(json_file).replace('.json', '.py')}"
        save_functions_to_file(generated_code, output_dir, output_file)
    
    # 生成导入语句和工具注册代码
    import_statement = generate_import_statement(all_functions)
    print("\n生成的导入语句和工具注册代码:")
    print(import_statement)
    
    # 将所有生成的函数合并到一个文件（保存在当前目录）
    combined_file = "all_generated_functions.py"
    with open(combined_file, 'w', encoding='utf-8') as file:
        for json_file in json_files:
            output_file = f"generated_function_{os.path.basename(json_file).replace('.json', '.py')}"
            full_path = os.path.join(output_dir, output_file)
            if os.path.exists(full_path):
                content = read_file_content(full_path)
                if content:
                    file.write(content + "\n\n")
    
    print(f"\n所有生成的函数已合并到 {combined_file}")
    print("请将此文件的内容复制到tools.py中，并使用上面生成的导入语句和工具注册代码")

if __name__ == "__main__":
    main()
