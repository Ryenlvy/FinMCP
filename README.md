# 金融数据MCP

## 项目概述

[沧海数据](https://tsanghi.com)是一个专业的金融数据API服务，提供全面的股票、指数、债券等金融市场数据。主要是提供按量付费，比较方便

本项目基于该API，并包含完整的服务端实现

## 核心功能

- **股票数据查询**：实时行情、历史K线、财务报表、分红配股等
- **指数数据查询**：成分股、实时指数、历史走势等
- **市场数据**：交易所信息、股票列表、公司信息等
- **财务数据**：资产负债表、现金流量表、利润表等
- **企业信息**：公司概况、股东结构、管理层信息等

## 快速开始

### 安装依赖

```bash
uv pip install -r requirements.txt
```

### 启动服务器

```bash
python server.py --transport fastapi --host 0.0.0.0 --port 8000
```

### 服务器启动选项

- `--transport`：传输模式，支持`stdio`、`sse`或`fastapi`
- `--host`：服务器绑定的主机地址
- `--port`：服务器监听的端口

## API示例

### 获取股票实时行情

```python
async def get_stock_realtime_daily(exchange_code: str, ticker: str):
    """获取股票实时日线数据"""
    url = f"https://tsanghi.com/api/fin/stock/{exchange_code}/daily/realtime"
    params = {
        "token": FIN_API_TOKEN,
        "ticker": ticker,
        "fmt": "json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
```

### 获取公司信息

```python
async def get_stock_company_info(exchange_code: str, ticker: str):
    """获取股票公司信息"""
    url = f"https://tsanghi.com/api/fin/stock/{exchange_code}/company/info"
    params = {
        "token": FIN_API_TOKEN,
        "exchange_code": exchange_code,
        "ticker": ticker
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        return response.json()
```

## 文档爬虫系统

项目包含一个专门的文档爬虫系统，用于自动化获取API文档并生成相应的工具函数：

- `crawl_tsanghi_docs.py`：爬取沧海API文档
- `code_creater.py`：基于文档自动生成工具函数代码

## 项目结构

```
├── server.py           # 主服务器实现
├── tools.py            # 工具函数集合
├── crawl_tsanghi_docs.py  # API文档爬虫
├── code_creater.py     # 代码生成器
├── tsanghi_docs/       # 爬取的文档存储目录
└── tools_code/         # 生成的工具函数代码
```

## 健康检查与调试

- `/health`：健康检查端点
- `/tools/list`：列出所有可用工具函数

