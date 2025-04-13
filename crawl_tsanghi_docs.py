import asyncio
import json
import os
import logging
import time
import random
import re
from typing import List, Dict
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from bs4 import BeautifulSoup
import re
import html


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("tsanghi_crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义要爬取的索引范围
def generate_indices():
    indices = []
    for i in range(2, 6):  # 2到5
        for j in range(1, 6):  # 1到5
            for k in range(1, 6):  # 1到5
                indices.append(f"{i}-{j}-{k}")
    return indices

async def crawl_doc_page(crawler, index: str, output_dir: str):
    # 添加随机延迟，模拟人类行为
    delay = 1 + random.random() * 2  # 1-3秒的随机延迟
    await asyncio.sleep(delay)
    
    logger.info(f"正在爬取索引 {index}...")
    
    # 改进提取结构，使用更多的选择器组合
    schema = {
        "name": "API文档",
        "baseSelector": "body",
        "fields": [
            # 文档标题 - 扩展选择器
            {"name": "title", "selector": "h1, .doc-title, .api-title, .page-title, header h1, .main-title", "type": "text"},
            
            # 新增：提取原始三级标题
            {"name": "raw_title", "selector": ".containerFlex .flex-item p, div.containerFlex h3, h3.api-section-title, .main-content h3", "type": "text"},
            
            # 新增：提取一二级标题
            {"name": "level1_2_title", "selector": f"#div{index}_1 > p, .div{index}_1 > p", "type": "text"},
            
            # 接口说明 - 扩展选择器
            {"name": "description", "selector": ".description, .doc-description, p.intro, .api-description, .summary, .overview", "type": "text"},
            {"name": "api_endpoint", "selector": ".api-endpoint, .endpoint, code.endpoint, .url, .api-url, pre.endpoint", "type": "api"},
            {"name": "request_params_table", "selector": "#pane-request0 .el-table, .request-params table, .params-table, table.request, table.parameters", "type": "html"},
            {"name": "response_params_table", "selector": "#pane-response0 .el-table, .response-params table, .response-table, table.response", "type": "html"},
            {"name": "restful_api", "selector": ".api-section, .api, .endpoint-section, #api-details", "type": "text"},
            {"name": "request", "selector": "#pane-request0, .request-section, .request, #request-details", "type": "html"},
            {"name": "response", "selector": "#pane-response0, .response-section, .response, #response-details", "type": "html"},
            {"name": "python_example", "selector": "pre.python-code, pre, code.python, .code-example, .example-code", "type": "text"},
            # 备份整个页面内容
            {"name": "page_content", "selector": "body", "type": "html"},
            # 添加表格提取
            {"name": "all_tables", "selector": ".el-table, table", "type": "html_list"}
        ]
    }
    js_code = """
    // 模拟用户代理
    Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        writable: false
    });
    
    // 模拟语言设置
    Object.defineProperty(navigator, 'language', {
        value: 'zh-CN',
        writable: false
    });
    
    // 快速检查页面是否为空（在5秒内完成）
    function checkIfPageEmpty() {
        // 检查页面是否有任何有意义的内容
        const hasContent = document.querySelector('.containerFlex, .el-table, table, .api-section, .doc-title, h1');
        if (!hasContent) {
            // 如果没有找到任何内容，标记页面为空
            document.body.setAttribute('data-page-empty', 'true');
            console.log('页面似乎为空，已标记');
            return true;
        }
        return false;
    }
    
    // 等待元素的改进版本，增加超时功能
    function waitForElement(selector, timeout) {
        return new Promise((resolve, reject) => {
            // 先检查页面是否为空
            if (checkIfPageEmpty()) {
                reject(new Error('页面为空'));
                return;
            }
            
            const startTime = Date.now();
            const checkElement = () => {
                const element = document.querySelector(selector);
                if (element) {
                    resolve(element);
                    return;
                }
                
                // 每5秒再次检查页面是否为空
                if (Date.now() - startTime > 5000 && checkIfPageEmpty()) {
                    reject(new Error('页面为空'));
                    return;
                }
                
                if (Date.now() - startTime > timeout) {
                    reject(new Error(`等待元素 ${selector} 超时`));
                    return;
                }
                
                setTimeout(checkElement, 100);
            };
            
            checkElement();
        });
    }
    
    // 主函数
    async function main() {
        try {
            // 快速检查页面是否为空
            if (checkIfPageEmpty()) {
                return;
            }
            
            // 给页面5秒钟加载基本内容
            await new Promise(resolve => setTimeout(resolve, 5000));
            
            // 再次检查是否为空
            if (checkIfPageEmpty()) {
                return;
            }
            
            // 如果页面不为空，继续正常流程
            try {
                // 等待请求选项卡出现
                const requestTab = await waitForElement('#tab-request0', 5000);
                console.log('找到请求选项卡');
                
                // 点击请求选项卡
                requestTab.click();
                console.log('已点击请求选项卡');
                
                // 等待请求内容加载
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // 等待响应选项卡出现
                const responseTab = await waitForElement('#tab-response0', 5000);
                console.log('找到响应选项卡');
                
                // 点击响应选项卡
                responseTab.click();
                console.log('已点击响应选项卡');
                
                // 等待响应内容加载
                await new Promise(resolve => setTimeout(resolve, 1000));
                
                // 标记完成
                document.body.setAttribute('data-tabs-clicked', 'true');
            } catch (error) {
                // 如果过程中出错，但页面不是空的，标记为内容已处理
                if (!document.body.hasAttribute('data-page-empty')) {
                    document.body.setAttribute('data-content-processed', 'true');
                }
                console.error('交互过程中出错:', error);
            }
        } catch (error) {
            console.error('主函数执行出错:', error);
        }
    }
    
    // 执行主函数
    setTimeout(main, 1000);
    """
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        wait_for="[data-tabs-clicked='true'], [data-page-empty='true'], [data-content-processed='true'], .el-table, table",
        page_timeout=30000,
        screenshot=False,
        js_code=js_code
    )
    
    try:
        url = f"https://tsanghi.com/fin/doc?index={index}"
        browser_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://tsanghi.com/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        }
        js_set_headers = """
        Object.defineProperty(navigator, 'userAgent', {
            value: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            writable: false
        });
        """
        config.js_code = js_set_headers
        
        result = await crawler.arun(url=url, config=config)
        await asyncio.sleep(3)
        
        if result.success:
            if result.extracted_content is None or str(result.extracted_content).strip() == "" or str(result.extracted_content).strip() == "[]":
                logger.info(f"索引 {index} 的页面内容为空")
                return {"is_empty_page": True}
            try:
                if isinstance(result.extracted_content, bytes):
                    json_content = json.loads(result.extracted_content.decode('utf-8'))
                else:
                    json_content = json.loads(result.extracted_content)
                if not json_content or (isinstance(json_content, list) and (len(json_content) == 0 or not any(item for item in json_content))):
                    logger.info(f"索引 {index} 的JSON内容为空")
                    return {"is_empty_page": True}
                processed_content = post_process_content(json_content)
                
                # 再次检查处理后的内容是否为空
                if not processed_content or (isinstance(processed_content, list) and len(processed_content) == 0):
                    logger.info(f"索引 {index} 处理后的内容为空")
                    return {"is_empty_page": True}  # 返回空页面标记
                
                # 保存到doc_文件（不再生成processed文件）
                output_file = os.path.join(output_dir, f"doc_{index}.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(processed_content, f, ensure_ascii=False, indent=2)
                
                logger.info(f"成功爬取并保存索引 {index}")
                
                return processed_content
            except json.JSONDecodeError as e:
                logger.error(f"解析JSON失败: {str(e)}")
                return None
        else:
            if result.error_message and any(keyword in result.error_message.lower() for keyword in ["404", "not found", "empty", "timeout", "wait condition failed"]):
                logger.info(f"索引 {index} 的页面可能为空或不存在: {result.error_message}")
                return {"is_empty_page": True}
                
            logger.error(f"爬取索引 {index} 失败: {result.error_message}")
            return None
    except Exception as e:
        logger.exception(f"爬取索引 {index} 时发生异常")
        return None

def clean_text(text):
    """简单的文本清理函数：去除多余的空白符"""
    if text:
        import html
        text = html.unescape(text)
        return " ".join(text.split())
    return ""

def extract_page_hierarchy(page_content):
    """直接从HTML中提取三级层级结构"""
    if not page_content:
        return ""
        
    soup = BeautifulSoup(page_content, 'html.parser')
    hierarchy = []
    
    print("开始提取文档层级结构...")
    all_div_patterns = [
        r'div(\d+-\d+-\d+)_\d+',
        r'id="div(\d+-\d+-\d+)_\d+"',
        r'id=\'div(\d+-\d+-\d+)_\d+\''
    ]
    
    div_id = ""
    for pattern in all_div_patterns:
        div_ids = re.findall(pattern, page_content)
        if div_ids:
            div_id = div_ids[0]
            print(f"找到div ID: {div_id}")
            break
    
    if div_id:
        try:
            for selector in [f'#div{div_id}_1 > p', f'.div{div_id}_1 > p', f'[id^="div{div_id}"] > p']:
                level1_2_element = soup.select_one(selector)
                if level1_2_element:
                    level1_2_text = clean_text(level1_2_element.get_text())
                    print(f"从选择器 '{selector}' 找到第一二级: {level1_2_text}")
                    if level1_2_text:
                        if '>' in level1_2_text:
                            level_parts = level1_2_text.split('>')
                            for i, part in enumerate(level_parts):
                                clean_part = clean_text(part)
                                if clean_part:
                                    hierarchy.append(clean_part)
                                    print(f"添加层级{i+1}: {clean_part}")
                        else:
                            hierarchy.append(level1_2_text)
                            print(f"添加单一层级: {level1_2_text}")
                    break
            
            # 第三级name选择器(通用格式)
            for selector in [
                f'#div{div_id}_1 > div.containerFlex > div.flex-item > p',
                f'.div{div_id}_1 > div.containerFlex > div.flex-item > p',
                f'[id^="div{div_id}"] > div.containerFlex > div.flex-item > p'
            ]:
                level3_element = soup.select_one(selector)
                if level3_element:
                    level3_text = clean_text(level3_element.get_text())
                    print(f"从选择器 '{selector}' 找到第三级: {level3_text}")
                    if level3_text:
                        hierarchy.append(level3_text)
                    break
        except Exception as e:
            print(f"使用特定选择器提取层级时出错: {str(e)}")
    
    # 如果使用特定选择器未能提取全部层级，尝试备用方法
    if len(hierarchy) < 1:
        print("特定选择器未能提取层级，尝试备用方法...")
        
        # 尝试查找所有具有特定样式的段落(通常用于导航路径)
        all_p = soup.find_all('p')
        for p in all_p:
            # 查找灰色字体段落或包含">"的段落
            style = p.get('style', '')
            text = p.get_text().strip()
            
            # 打印调试信息
            if style or '>' in text:
                print(f"找到潜在导航段落: '{text}' (样式: {style})")
            
            if ('color' in style.lower() and any(color in style.lower() for color in ['#7f7f7f', 'rgb(127', 'gray', 'grey'])) or '>' in text:
                if '>' in text:
                    parts = re.split(r'\s*>\s*', html.unescape(text))
                    for part in parts:
                        clean_part = clean_text(part)
                        if clean_part and clean_part not in hierarchy:
                            hierarchy.append(clean_part)
                            print(f"从导航文本添加层级: {clean_part}")
                else:
                    clean_text_p = clean_text(text)
                    if clean_text_p and clean_text_p not in hierarchy:
                        hierarchy.append(clean_text_p)
                        print(f"从样式段落添加层级: {clean_text_p}")
    
    # 组合层级
    if hierarchy:
        result = "-".join(hierarchy)
        print(f"最终提取的层级: {result}")
        return result
    else:
        print("警告：未能提取到任何层级信息")
        return ""

def post_process_content(json_content):
    """使用BeautifulSoup直接从HTML中提取所需信息"""
    if not isinstance(json_content, list) or len(json_content) == 0:
        return json_content
    
    content = json_content[0]
    
    # 获取原始HTML内容 - 直接使用page_content作为主要来源
    raw_html = ""
    
    # 确保我们使用page_content作为主要HTML源
    if "page_content" in content and content["page_content"]:
        raw_html = content["page_content"]
    if not raw_html:
        # 尝试从其他字段获取HTML内容作为备用
        for field in ["request", "response", "all_tables", "request_params_table", "response_params_table"]:
            if field in content and content[field]:
                raw_html += content[field]
    
    # 创建BeautifulSoup对象解析HTML
    soup = BeautifulSoup(raw_html, 'html.parser')
    
    # 提取标题 - 尝试多种方式
    title = ""
    level1_title = ""
    level2_title = ""
    
    # 1. 首先尝试提取一二级标题
    if "level1_2_title" in content and content["level1_2_title"]:
        level1_2_text = clean_text(content["level1_2_title"])
        print(f"提取到一二级标题文本: {level1_2_text}")
        
        # 处理可能包含 ">" 的文本
        if '>' in level1_2_text:
            level_parts = level1_2_text.split('>')
            if len(level_parts) >= 2:
                level1_title = clean_text(level_parts[0])
                level2_title = clean_text(level_parts[1])
                print(f"分离出一级标题: {level1_title}, 二级标题: {level2_title}")
        else:
            # 如果没有分隔符，可能整个就是一级标题
            level1_title = level1_2_text
            print(f"提取出单一标题(视为一级): {level1_title}")
    
    # 2. 如果从level1_2_title无法提取，尝试从HTML直接提取
    if not level1_title and not level2_title:
        try:
            # 从索引构建选择器 - 假设content中有index信息，或从URL中提取
            index_match = re.search(r'index=(\d+-\d+-\d+)', str(content))
            if index_match:
                index = index_match.group(1)
                level1_2_selector = f'#div{index}_1 > p'
                level1_2_element = soup.select_one(level1_2_selector)
                if level1_2_element:
                    level1_2_text = clean_text(level1_2_element.get_text())
                    print(f"从HTML直接提取一二级标题: {level1_2_text}")
                    # 处理分隔符
                    if '>' in level1_2_text:
                        level_parts = level1_2_text.split('>')
                        if len(level_parts) >= 2:
                            level1_title = clean_text(level_parts[0])
                            level2_title = clean_text(level_parts[1])
                    else:
                        level1_title = level1_2_text
        except Exception as e:
            print(f"提取一二级标题时出错: {str(e)}")
    
    # 3. 尝试提取三级标题
    level3_title = ""
    if "raw_title" in content and content["raw_title"]:
        level3_title = clean_text(content["raw_title"])
        print(f"提取到三级标题: {level3_title}")
    
    # 4. 如果没有找到三级标题，尝试从HTML直接提取
    if not level3_title:
        # 尝试从HTML直接提取三级标题
        level3_selectors = [
            'div.containerFlex .flex-item p', 
            'div.containerFlex h3', 
            'h3.api-section-title',
            '.api-title',
            '.page-title h3',
            '.main-content h3'
        ]
        
        for selector in level3_selectors:
            elements = soup.select(selector)
            for element in elements:
                potential_title = clean_text(element.get_text())
                if potential_title and len(potential_title) > 3 and len(potential_title) < 100:
                    level3_title = potential_title
                    print(f"从选择器 '{selector}' 直接提取到三级标题: {level3_title}")
                    break
            if level3_title:
                break
    
    # 5. 组合完整标题
    if level1_title and level2_title and level3_title:
        title = f"{level1_title} > {level2_title} > {level3_title}"
    elif level1_title and level2_title:
        title = f"{level1_title} > {level2_title}"
    elif level3_title:
        title = level3_title
    elif content.get("title"):
        title = clean_text(content["title"])
    
    print(f"最终组合的标题: {title}")
    
    # 创建结构化输出对象 - 只保留需要的字段（删除description和api_endpoint）
    structured_content = {
        "title": title,
        "request_params": [],
        "response_params": [],
        "python_example": clean_python_example(content.get("python_example", "")),
    }
    
    # 处理请求参数表格
    request_table_html = content.get("request_params_table", "")
    if request_table_html:
        structured_content["request_params"] = extract_params_from_table(request_table_html, "request")
    
    # 处理响应参数表格
    response_table_html = content.get("response_params_table", "")
    if response_table_html:
        structured_content["response_params"] = extract_params_from_table(response_table_html, "response")
    
    return [structured_content]

def extract_params_from_table(table_html, table_type):
    """使用BeautifulSoup从HTML表格中提取参数信息"""
    params = []
    soup = BeautifulSoup(table_html, 'html.parser')
    
    # 查找所有表格行
    rows = soup.select('tr.el-table__row')
    
    for row in rows:
        # 查找所有单元格
        cells = row.select('div.cell')
        
        if len(cells) < 3:
            continue
            
        param = {}
        
        if table_type == "request" and len(cells) >= 4:
            param = {
                "name": clean_text(cells[0].get_text()),
                "type": clean_text(cells[1].get_text()),
                "required": "必选" in clean_text(cells[2].get_text()),
                "option": clean_text(cells[2].get_text()),
                "description": clean_text(cells[3].get_text())
            }
        elif table_type == "response" and len(cells) >= 3:
            param = {
                "name": clean_text(cells[0].get_text()),
                "type": clean_text(cells[1].get_text()),
                "description": clean_text(cells[2].get_text())
            }
        
        if param:
            params.append(param)
    
    # 如果使用BeautifulSoup未能提取到参数，尝试使用正则表达式
    if not params:
        return extract_params_from_table_regex(table_html, table_type)
    
    return params

def extract_params_from_table_regex(table_html, table_type):
    """使用正则表达式从HTML表格中提取参数信息（备用方法）"""
    import re
    params = []
    
    # 提取表格行
    rows = re.findall(r'<tr class="el-table__row[^>]*>(.*?)</tr>', table_html, re.DOTALL)
    
    for row in rows:
        # 提取单元格
        cells = re.findall(r'<div class="cell">(.*?)</div>', row, re.DOTALL)
        
        if len(cells) < 3:
            continue
            
        param = {}
        
        if table_type == "request" and len(cells) >= 4:
            param = {
                "name": clean_html(cells[0]),
                "type": clean_html(cells[1]),
                "required": "必选" in clean_html(cells[2]),
                "option": clean_html(cells[2]),
                "description": clean_html(cells[3])
            }
        elif table_type == "response" and len(cells) >= 3:
            param = {
                "name": clean_html(cells[0]),
                "type": clean_html(cells[1]),
                "description": clean_html(cells[2])
            }
        
        if param:
            params.append(param)
    
    return params

def clean_html(html_text):
    """清理HTML标签并规范化文本"""
    import re
    if not html_text:
        return ""
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', ' ', html_text)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_python_example(python_code):
    """清理和格式化Python示例代码"""
    import re
    if not python_code:
        return ""
    
    # 清理代码中的多余空格和换行
    code = python_code.strip()
    
    # 修复常见问题：缺少空格的import语句、url赋值等
    code = re.sub(r'import(\w+)', r'import \1', code)
    code = re.sub(r'url=f"', r'url = f"', code)
    code = re.sub(r'data=requests', r'data = requests', code)
    code = re.sub(r'print\(', r'print(', code)
    
    return code

async def crawl_with_table_navigation(indices: List[str]):
    # 创建输出目录
    output_dir = "tsanghi_docs"
    os.makedirs(output_dir, exist_ok=True)
    
    # 配置浏览器
    browser_config = BrowserConfig(
        headless=True,  # 设置为True提高性能
        java_script_enabled=True,
        viewport_width=1280,
        viewport_height=800,
        # 尝试在浏览器配置中设置用户代理
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    
    # 初始化爬虫
    async with AsyncWebCrawler(config=browser_config, default_timeout=120000) as crawler:
        results = {}
        
        # 添加进度跟踪
        total = len(indices)
        completed = 0
        
        # 使用信号量控制并发数量，避免过多请求导致被封
        semaphore = asyncio.Semaphore(3)  # 进一步降低并发数量到2
        
        async def process_index(index):
            nonlocal completed
            async with semaphore:
                try:
                    # 尝试爬取页面，最多重试3次
                    for attempt in range(3):  # 增加到4次尝试
                        try:
                            # 增加随机延迟，避免被检测为爬虫
                            delay = 3 + random.random() * 5  # 5-10秒的随机延迟
                            await asyncio.sleep(delay)
                            
                            result = await crawl_doc_page(crawler, index, output_dir)
                            
                            # 检查是否为空页面标记
                            if result and isinstance(result, dict) and result.get("is_empty_page"):
                                logger.info(f"确认索引 {index} 为空页面，不再重试")
                                # 可选：创建一个标记文件表示此页面已检查但为空
                                empty_file = os.path.join(output_dir, f"empty_{index}.json")
                                with open(empty_file, "w", encoding="utf-8") as f:
                                    json.dump({"index": index, "status": "empty", "checked_time": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
                                break  # 跳出重试循环
                            
                            if result:
                                results[index] = result
                                break
                            elif attempt < 3:  # 如果失败且不是最后一次尝试
                                print(f"重试爬取索引 {index}...")
                                await asyncio.sleep(10)  # 等待10秒后重试
                        except Exception as e:
                            print(f"尝试 {attempt+1} 爬取索引 {index} 失败: {str(e)}")
                            if attempt < 3:
                                await asyncio.sleep(10)
                except Exception as e:
                    print(f"处理索引 {index} 时发生错误: {str(e)}")
                finally:
                    completed += 1
                    print(f"进度: {completed}/{total} ({completed/total*100:.2f}%)")
        
        # 创建所有任务
        tasks = [process_index(index) for index in indices]
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
        
        print(f"爬取完成，共爬取 {len(results)} 个页面")

async def main():
    indices = generate_indices()
    
    # 添加命令行参数支持，方便调试
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='爬取Tsanghi文档')
    parser.add_argument('--test', action='store_true', help='测试模式，只爬取少量页面')
    parser.add_argument('--resume', action='store_true', help='从上次中断的地方继续爬取')
    args = parser.parse_args()
    
    if args.test:
        # 测试模式，只爬取少量页面
        test_indices = indices[:5]
        logger.info(f"测试模式：仅爬取 {len(test_indices)} 个页面")
        await crawl_with_table_navigation(test_indices)
    elif args.resume:
        # 断点续传模式
        output_dir = "tsanghi_docs"
        completed_indices = set()
        
        # 检查已经完成的索引
        if os.path.exists(os.path.join(output_dir, "all_results.json")):
            try:
                with open(os.path.join(output_dir, "all_results.json"), "r", encoding="utf-8") as f:
                    completed_results = json.load(f)
                    completed_indices = set(completed_results.keys())
                    logger.info(f"找到 {len(completed_indices)} 个已完成的索引")
            except Exception as e:
                logger.error(f"读取已完成索引时出错: {str(e)}")
        
        # 过滤出未完成的索引
        remaining_indices = [idx for idx in indices if idx not in completed_indices]
        logger.info(f"继续爬取剩余的 {len(remaining_indices)} 个索引")
        await crawl_with_table_navigation(remaining_indices)
    else:
        await crawl_with_table_navigation(indices)

    # 在爬取完成后调用清理函数
    if not args.test:
        print("开始清理空文件...")
        removed_count = cleanup_empty_files("tsanghi_docs")
        print(f"清理完成，删除了 {removed_count} 个空文件")

def cleanup_empty_files(output_dir):
    """删除空的或无效的JSON文件"""
    count_removed = 0
    for filename in os.listdir(output_dir):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(output_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)
                
                # 检查文件是否为空或没有有效内容
                is_empty = False
                
                if not content:
                    is_empty = True
                elif isinstance(content, list):
                    if len(content) == 0:
                        is_empty = True
                    elif len(content) == 1 and not content[0].get("request_params"):
                        is_empty = True
                
                if is_empty:
                    os.remove(filepath)
                    count_removed += 1
                    logger.info(f"已删除空文件: {filename}")
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果文件不是有效的JSON或不存在，也删除
            try:
                os.remove(filepath)
                count_removed += 1
                logger.info(f"已删除无效文件: {filename}")
            except FileNotFoundError:
                pass
    
    logger.info(f"清理完成，共删除 {count_removed} 个空文件")
    return count_removed

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}") 