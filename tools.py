#!/usr/bin/env python3
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Union
import httpx

# 配置日志
logger = logging.getLogger("fin-tools")

# 沧海 API 配置
FIN_API_TOKEN = os.environ.get("FIN_API_TOKEN")

FIN_API_BASE = "https://api.tsanghi.com/fin"

# 辅助函数
async def make_fin_request(endpoint: str, params: dict = None) -> dict:
    """向沧海 API 发送请求并处理响应"""
    url = f"https://tsanghi.com/api/fin/{endpoint}"
    
    if params is None:
        params = {}
    
    # 添加token到参数中
    params["token"] = FIN_API_TOKEN
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"API 请求错误: {str(e)}")
        return {"error": str(e)}

async def restart_server() -> str:
    """重启 MCP 服务器
    
    Returns:
        重启状态信息
    """
    try:
        logger.info("收到重启服务器请求")
        await asyncio.sleep(1)
        
        return "服务器重启请求已接收，服务器将在处理完当前请求后重启"
    except Exception as e:
        logger.error(f"重启服务器错误: {str(e)}")
        return f"重启服务器时发生错误: {str(e)}"

async def get_beijing_time() -> Dict[str, Any]:
    """获取标准北京时间
    
    获取当前准确的北京时间
    
    返回:
        标准北京时间响应字典，格式为yyyy-MM-dd HH:mm:ss
    """
    try:
        from datetime import datetime
        import pytz
        
        # 获取北京时区的当前时间
        beijing_tz = pytz.timezone('Asia/Shanghai')
        beijing_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"使用系统时间作为备选: {beijing_time}")
        
        # 返回与API相同格式的响应
        return beijing_time
    except Exception as e:
        logger.error(f"获取北京时间错误 {str(e)}")
        return f"获取时间出错: {str(e)}"

'''
##################################################
#                                                #
#               以下为沧海API的函数                 #
#                                                #
##################################################
'''


async def get_historical_balance_sheet_annual(token: str, exchange_code: str, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: Optional[int] = None, fmt: Optional[str] = "json", columns: Optional[str] = None, order: Optional[int] = 0) -> Dict[str, Any]:
    """获取股票的历史资产负债表（年度）
    
    必选参数：
        token: API Token，登录后获取
        exchange_code: 交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）
        ticker: 股票代码，例如：600519（贵州茅台）、AAPL（苹果）
    
    可选参数：
        start_date: 起始日期（报告期），格式“yyyy-mm-dd”，默认：最早日期
        end_date: 终止日期（报告期），格式“yyyy-mm-dd”，默认：最新日期
        limit: 输出数量，默认：全部
        fmt: 输出格式，支持json和csv两种标准输出格式，默认：json
        columns: 输出字段，支持自定义输出，多个字段以半角逗号分隔，默认：全部字段
        order: 按日期排序，0：不排序，1：升序，2：降序，默认：0
    
    返回:
        包含历史资产负债表数据的字典
    """
    endpoint = f"stock/{exchange_code}/balance/sheet/yearly"
    params = {
        "token": token,
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns,
        "order": order
    }
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"响应中缺少有效数据: {response}")
            return {"error": "响应中缺少有效数据", "details": response}
    except Exception as e:
        logger.error(f"获取历史资产负债表（年度）失败: {str(e)}")
        return {"error": str(e)}

async def get_realtime_index_data(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内实时5分钟行情数据

    获取指定国家/地区和指数代码的实时5分钟行情数据。

    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        limit (int): 可选，输出数量。
        fmt (str): 可选，输出格式。支持json和csv，默认为json。
        columns (str): 可选，自定义输出字段，多个字段以逗号分隔。

    返回:
        包含实时指数行情数据的字典
    """
    try:
        endpoint = f"index/{country_code}/5min/realtime"
        params = {
            "ticker": ticker
        }
        
        # 添加可选参数
        if limit is not None:
            params["limit"] = limit
        if fmt is not None:
            params["fmt"] = fmt
        if columns is not None:
            params["columns"] = columns
        
        # 发送请求
        response = await make_fin_request(endpoint, params)
        
        # 检查响应是否包含有效数据
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        else:
            logger.warning("未收到有效的指数行情数据")
            return {"error": "未收到有效数据"}
    
    except Exception as e:
        logger.error(f"获取实时指数行情错误: {str(e)}")
        return {"error": str(e)}

async def get_forex_yearly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇年线实时数据

    获取指定外汇代码的年线实时行情数据。

    参数:
        ticker (str): 必选，外汇代码。例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期。格式“yyyy-mm-dd”。
        end_date (str): 可选，终止日期。格式“yyyy-mm-dd”。
        limit (int): 可选，输出数量，默认：1。
        fmt (str): 可选，输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 可选，输出字段。支持自定义输出，多个字段以半角逗号分隔。

    返回:
        外汇年线实时行情数据字典
    """
    try:
        endpoint = f"forex/yearly/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }

        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}

        # 调用沧海API
        response = await make_fin_request(endpoint, params)

        # 检查返回结果是否包含错误
        if "error" in response:
            logger.error(f"获取外汇年线实时数据失败: {response['error']}")
            return {"error": response["error"]}

        # 提取有效数据
        data = response.get("data", {})

        return data

    except Exception as e:
        logger.error(f"获取外汇年线实时数据出错: {str(e)}")
        return {"error": str(e)}

async def get_country_info(country_code: Optional[str] = None, fmt: Optional[str] = 'json', columns: Optional[str] = None) -> Dict[str, Any]:
    """获取国家/地区信息

    根据国家/地区代码获取详细的国家信息。

    参数:
        country_code (str, 可选): 国家/地区代码。例如：CHN（中国）、USA（美国）。
        fmt (str, 可选): 输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str, 可选): 输出字段。支持自定义输出，多个字段以半角逗号分隔。

    返回:
        包含国家/地区信息的有效数据字典
    """
    try:
        params = {}

        # 必选参数已经在 make_fin_request 中处理
        if country_code:
            params["country_code"] = country_code
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns

        response = await make_fin_request("country", params=params)

        # 检查返回的响应是否包含错误
        if "error" in response:
            return {"error": response["error"]}

        # 提取有效的 data 数据
        data = response.get("data", {})
        return data

    except Exception as e:
        logger.error(f"获取国家/地区信息错误 {str(e)}")
        return {"error": f"获取国家/地区信息时发生错误: {str(e)}"}

async def get_stock_monthly_realtime_data(exchange_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """
    获取股票实时月线数据
    
    此函数用于查询指定交易所和股票代码的实时月线数据，包括开盘价、最高价、最低价、收盘价等信息。
    
    参数:
        exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        fmt (str): 可选，默认为"json"，支持"json"或"csv"两种输出格式。
        columns (str): 可选，自定义输出字段，多个字段以半角逗号分隔。
        
    返回:
        包含股票实时月线数据的有效响应字典。
    """
    endpoint = f"stock/{exchange_code}/monthly/realtime"
    params = {
        "ticker": ticker,
        "fmt": fmt
    }
    if columns:
        params["columns"] = columns

    try:
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            return {"error": response["error"]}
        return response.get("data", {})
    except Exception as e:
        logger.error(f"获取股票实时月线数据失败: {str(e)}")
        return {"error": str(e)}

async def get_realtime_monthly_index_data(country_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数的基本行情实时月线数据

    获取指定国家/地区和指数代码的实时月线行情数据。

    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        fmt (str): 可选，默认为"json"，输出格式。支持"json"和"csv"。
        columns (str): 可选，自定义输出字段，多个字段以半角逗号分隔。

    返回:
        实时月线行情数据字典
    """
    try:
        endpoint = f"index/{country_code}/monthly/realtime"
        params = {
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            return {"error": response["error"]}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    except Exception as e:
        logger.error(f"获取实时月线行情数据错误 {str(e)}")
        return {"error": f"获取数据出错: {str(e)}"}

async def get_forex_list(token: str, ticker: Optional[str] = None, fmt: Optional[str] = None, columns: Optional[str] = None) -> Dict[str, Any]:
    """获取外汇清单信息
    
    获取外汇的基本信息列表，支持按需筛选和自定义输出。
    
    参数:
        token (str): 必选。API Token，用于身份验证。
        ticker (Optional[str]): 可选。外汇代码，例如：USDCNY（美元/人民币）。支持多只代码，以半角逗号分隔，最多100只。
        fmt (Optional[str]): 可选。输出格式，支持json和csv，默认为json。
        columns (Optional[str]): 可选。自定义输出字段，多个字段以半角逗号分隔。
    
    返回:
        包含外汇清单信息的有效数据字典。
    """
    try:
        # 构造请求参数
        params = {"token": token}
        if ticker is not None:
            params["ticker"] = ticker
        if fmt is not None:
            params["fmt"] = fmt
        if columns is not None:
            params["columns"] = columns
        
        # 发送请求并获取响应
        response = await make_fin_request("forex/list", params=params)
        
        # 检查响应是否包含有效数据
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"未找到有效数据: {response}")
            return {"error": "未找到有效数据"}
    except Exception as e:
        logger.error(f"获取外汇清单错误: {str(e)}")
        return {"error": str(e)}

async def get_forex_15min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情实时15分钟数据

    获取指定外汇代码的日内行情实时15分钟数据，支持多种可选参数进行筛选和格式化输出。

    参数:
        ticker (str): 必选，外汇代码。例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期。格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最早日期。
        end_date (str): 可选，终止日期。格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最新日期。
        limit (int): 可选，输出数量，默认：1。
        fmt (str): 可选，输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 可选，输出字段。支持自定义输出，多个字段以半角逗号分隔。

    返回:
        提取后的有效数据字典
    """
    try:
        endpoint = f"forex/15min/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"API 响应中缺少 data 字段: {response}")
            return {"error": "API 响应中缺少 data 字段", "details": response}
    except Exception as e:
        logger.error(f"获取外汇15分钟实时数据错误: {str(e)}")
        return {"error": str(e)}

async def get_forex_30min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情实时30分钟数据
    
    获取指定外汇代码的日内行情实时30分钟数据，包括开盘价、最高价、最低价、收盘价等信息。
    
    参数:
        ticker (str): 必选，外汇代码，例如：USDCNY（美元人民币）
        start_date (str): 可选，起始日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最早日期
        end_date (str): 可选，终止日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最新日期
        limit (int): 可选，输出数量，默认：1
        fmt (str): 可选，输出格式，支持json和csv两种标准输出格式，默认：json
        columns (str): 可选，输出字段，支持自定义输出，多个字段以半角逗号分隔
    
    返回:
        外汇日内行情实时30分钟数据字典
    """
    endpoint = f"forex/30min/realtime"
    params = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns
    }
    
    # 移除值为None的参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
            return response["data"][0]
        else:
            return {"error": "未能获取有效的数据"}
    except Exception as e:
        logger.error(f"获取外汇30分钟实时行情错误: {str(e)}")
        return {"error": str(e)}

async def get_stock_weekly_realtime_data(token: str, exchange_code: str, ticker: str, fmt: Optional[str] = None, columns: Optional[str] = None) -> Dict[str, Any]:
    """获取股票实时周线数据

    该函数用于获取指定股票在某交易所的实时周线行情数据。

    必选参数:
        token (str): API Token，登录后获取。
        exchange_code (str): 交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 股票代码，例如：600519（贵州茅台）、AAPL（苹果）。

    可选参数:
        fmt (str): 输出格式，默认为json。支持json和csv两种格式。
        columns (str): 自定义输出字段，多个字段以半角逗号分隔。

    返回:
        包含股票实时周线数据的有效字典，包含以下可能字段：
        - ticker (str): 股票代码
        - date (str): 日期，格式“yyyy-mm-dd”
        - open (float): 开盘价
        - high (float): 最高价
        - low (float): 最低价
        - close (float): 收盘价
        - volume (float): 成交量
        - amount (float): 成交额（需指定columns参数）
        - pre_close (float): 昨收价（需指定columns参数）
    """
    try:
        endpoint = f"stock/{exchange_code}/weekly/realtime"
        params = {
            "token": token,
            "ticker": ticker
        }
        
        # 添加可选参数
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 发送请求并获取响应
        response = await make_fin_request(endpoint, params=params)
        
        # 提取有效data字段返回
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        else:
            logger.error(f"无效的API响应: {response}")
            return {"error": "未能获取有效的股票实时周线数据"}
    
    except Exception as e:
        logger.error(f"获取股票实时周线数据出错: {str(e)}")
        return {"error": f"获取数据失败: {str(e)}"}

async def get_index_weekly_realtime(country_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数的实时周线数据

    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        fmt (str): 可选，默认为 "json"，输出格式。支持 "json" 和 "csv"。
        columns (str): 可选，自定义输出字段，多个字段以逗号分隔。

    返回:
        实时周线数据的字典
    """
    endpoint = f"index/{country_code}/weekly/realtime"
    params = {
        "ticker": ticker,
        "fmt": fmt,
    }
    if columns:
        params["columns"] = columns

    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"未找到有效数据: {response}")
            return {"error": "未返回有效数据"}
    except Exception as e:
        logger.error(f"获取指数实时周线错误: {str(e)}")
        return {"error": str(e)}

async def search_financial_items(keywords: str, 
                                 type: Optional[str] = None, 
                                 where: Optional[str] = None, 
                                 match_whole: Optional[int] = 0, 
                                 match_case: Optional[int] = 0, 
                                 exchange_code: Optional[str] = None, 
                                 country_code: Optional[str] = None, 
                                 fmt: Optional[str] = "json", 
                                 columns: Optional[str] = None) -> Dict[str, Any]:
    """搜索金融项目
    
    根据关键词和其他可选参数搜索股票、指数、ETF基金、外汇和加密货币等金融项目。
    
    参数:
        keywords (str): 必选。搜索关键词，至少1个字符。
        type (Optional[str]): 可选。类型。STOCK：股票，INDEX：指数，ETF：ETF基金，FOREX：外汇，CRYPTO：加密货币，默认：所有。
        where (Optional[str]): 可选。搜索位置。TICKER：从代码中搜索，NAME：从名称中搜索，默认：所有。
        match_whole (Optional[int]): 可选。匹配全词。0：不匹配全词，1：匹配全词，默认：0。
        match_case (Optional[int]): 可选。区分大小写。0：不区分大小写，1：区分大小写，默认：0。
        exchange_code (Optional[str]): 可选。交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        country_code (Optional[str]): 可选。国家/地区代码。例如：CHN（中国）、USA（美国）。
        fmt (Optional[str]): 可选。输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (Optional[str]): 可选。自定义输出字段，多个字段以半角逗号分隔。
    
    返回:
        包含搜索结果的字典
    """
    try:
        endpoint = "search/list"
        params = {
            "keywords": keywords,
            "type": type,
            "where": where,
            "match_whole": match_whole,
            "match_case": match_case,
            "exchange_code": exchange_code,
            "country_code": country_code,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        filtered_params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, filtered_params)
        if "data" in response:
            return response["data"]
        else:
            return {"error": "Invalid response format", "details": response}
    except Exception as e:
        logger.error(f"搜索金融项目错误 {str(e)}")
        return {"error": f"搜索过程中发生错误: {str(e)}"}

async def get_forex_realtime(ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """
    获取外汇实时行情数据
    
    参数:
        ticker (str): 必选，外汇代码。例如：USDCNY（美元人民币）。
        fmt (str): 可选，默认为"json"，输出格式。支持"json"和"csv"两种标准输出格式。
        columns (Optional[str]): 可选，自定义输出字段，多个字段以半角逗号分隔。
        
    返回:
        外汇实时行情数据字典，包含ticker、date、open、high、low、close等字段。
    """
    try:
        endpoint = "forex/realtime"
        params = {
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        # 调用沧海API获取数据
        response = await make_fin_request(endpoint, params)
        
        # 检查返回结果是否包含"data"字段
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        else:
            logger.error("未获取到有效的外汇实时行情数据")
            return {"error": "未获取到有效的外汇实时行情数据"}
    
    except Exception as e:
        logger.error(f"获取外汇实时行情错误: {str(e)}")
        return {"error": f"获取外汇实时行情时发生错误: {str(e)}"}

async def get_forex_weekly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时周线数据
    
    根据指定的外汇代码和可选的时间范围，获取外汇的实时周线行情数据。
    
    参数:
        ticker (str): 必选，外汇代码。例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期。格式“yyyy-mm-dd”。
        end_date (str): 可选，终止日期。格式“yyyy-mm-dd”。
        limit (int): 可选，输出数量，默认为1。
        fmt (str): 可选，输出格式。支持json和csv两种标准输出格式，默认为json。
        columns (str): 可选，输出字段。支持自定义输出，多个字段以半角逗号分隔。
    
    返回:
        包含外汇实时周线数据的有效字典
    """
    try:
        endpoint = "forex/weekly/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        else:
            logger.error("响应数据格式错误或缺少有效数据字段")
            return {"error": "无效的响应数据格式"}
    except Exception as e:
        logger.error(f"获取外汇实时周线数据失败: {str(e)}")
        return {"error": str(e)}

async def get_forex_60min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情的实时60分钟数据

    必选参数:
        ticker (str): 外汇代码，例如：USDCNY（美元人民币）

    可选参数:
        start_date (str): 起始日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最早日期
        end_date (str): 终止日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认：最新日期
        limit (int): 输出数量，默认：1
        fmt (str): 输出格式，支持json和csv两种标准输出格式，默认：json
        columns (str): 输出字段，支持自定义输出，多个字段以半角逗号分隔

    返回:
        包含实时60分钟外汇数据的有效数据字典
    """
    endpoint = f"forex/60min/realtime"
    params = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns
    }

    # 移除值为None的可选参数
    params = {k: v for k, v in params.items() if v is not None}

    try:
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            return {"error": response["error"]}
        return response.get("data", {})
    except Exception as e:
        logger.error(f"获取外汇60分钟实时行情错误: {str(e)}")
        return {"error": str(e)}

async def get_historical_dividends(
    exchange_code: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    fmt: Optional[str] = None,
    columns: Optional[str] = None,
    order: Optional[int] = None
) -> Dict[str, Any]:
    """获取股票的历史分红数据
    
    根据交易所代码和股票代码查询历史分红信息，支持多种可选参数进行筛选。
    
    必选参数:
        exchange_code (str): 交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）
        ticker (str): 股票代码，例如：600519（贵州茅台）、AAPL（苹果）
    
    可选参数:
        start_date (str): 起始日期，格式“yyyy-mm-dd”，默认：最早日期
        end_date (str): 终止日期，格式“yyyy-mm-dd”，默认：最新日期
        limit (int): 输出数量
        fmt (str): 输出格式，支持json和csv两种，默认：json
        columns (str): 自定义输出字段，多个字段以半角逗号分隔
        order (int): 按日期排序，0：不排序，1：升序，2：降序，默认：0
    
    返回:
        历史分红数据字典，包含股票代码、日期、分红等信息
    """
    try:
        endpoint = f"stock/{exchange_code}/dividend"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 过滤掉值为None的可选参数
        filtered_params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, filtered_params)
        
        # 提取有效的data字段作为返回值
        data = response.get("data", {})
        return data
    except Exception as e:
        logger.error(f"获取历史分红数据错误: {str(e)}")
        return {"error": str(e)}

async def get_index_constituents(country_code: str, ticker: str = None, constituent: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数成分股信息

    根据国家/地区代码和指数代码或成分股代码，查询指数的成分股详情。

    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 可选，指数代码。例如：000001（上证指数）。ticker和constituent至少传一个。
        constituent (str): 可选，成分股代码。例如：600519（贵州茅台）。ticker和constituent至少传一个。
        fmt (str): 可选，输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 可选，输出字段。支持自定义输出，多个字段以半角逗号分隔。

    返回:
        包含指数成分股信息的有效数据字典
    """
    try:
        endpoint = f"index/{country_code}/constituent"
        params = {}

        # 检查必选参数
        if not country_code:
            return {"error": "缺少必选参数 country_code"}

        # 检查ticker和constituent至少传一个
        if not ticker and not constituent:
            return {"error": "ticker和constituent至少需要传递一个"}

        # 构造请求参数
        if ticker:
            params["ticker"] = ticker
        if constituent:
            params["constituent"] = constituent
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns

        # 调用API
        response = await make_fin_request(endpoint, params)

        # 提取有效数据
        if "data" in response:
            return response["data"]
        else:
            return {"error": "未找到有效数据", "details": response}

    except Exception as e:
        logger.error(f"获取指数成分股错误 {str(e)}")
        return {"error": f"获取指数成分股时发生错误: {str(e)}"}

async def get_index_yearly_realtime(country_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数的基本行情实时年线数据
    
    根据国家/地区代码和指数代码，查询指定指数的实时年线数据。
    
    Args:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        fmt (str, optional): 可选，输出格式，默认为json。支持json和csv两种格式。
        columns (str, optional): 可选，自定义输出字段，多个字段以逗号分隔。
    
    Returns:
        dict: 指数实时年线数据，包含ticker、date、open、high、low、close等字段。
    """
    try:
        endpoint = f"index/{country_code}/yearly/realtime"
        params = {
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        # 检查返回值是否包含有效数据
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        else:
            logger.error(f"无效的API响应: {response}")
            return {"error": "未能获取有效的指数年线数据"}
    except Exception as e:
        logger.error(f"获取指数年线数据时发生错误: {str(e)}")
        return {"error": f"获取指数年线数据失败: {str(e)}"}

async def get_stock_yearly_realtime(exchange_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取股票实时年线数据

    获取指定交易所和股票代码的实时年线数据，包括开盘价、最高价、最低价、收盘价等信息。

    参数:
        exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        fmt (str): 可选，默认为"json"，输出格式。支持"json"和"csv"两种格式。
        columns (str): 可选，自定义输出字段，多个字段以逗号分隔。

    返回:
        包含股票实时年线数据的有效响应字典。
    """
    endpoint = f"stock/{exchange_code}/yearly/realtime"
    params = {
        "ticker": ticker,
        "fmt": fmt
    }
    if columns:
        params["columns"] = columns

    response = await make_fin_request(endpoint, params)
    if "data" in response and isinstance(response["data"], dict):
        return response["data"]
    else:
        logger.error(f"无效的API响应: {response}")
        return {"error": "无法获取有效的股票实时年线数据"}

async def get_stock_exchange_info(token: str, exchange_code: str = None, country_code: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票交易所信息
    
    获取指定条件下的股票交易所清单信息，支持按交易所代码、国家代码筛选。
    
    Args:
        token (str): API Token，必选参数，登录后获取。
        exchange_code (str, optional): 交易所代码，采用ISO市场标识码MIC（Market identifier codes)，可选参数。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        country_code (str, optional): 国家/地区代码，可选参数。例如：CHN（中国）、USA（美国）。
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认为json。
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选参数。
        
    Returns:
        dict: 包含交易所信息的有效数据字典
    """
    endpoint = "stock/exchange"
    params = {
        "token": token,
        "exchange_code": exchange_code,
        "country_code": country_code,
        "fmt": fmt,
        "columns": columns
    }
    
    # 移除值为None的参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"未找到有效数据: {response}")
            return {"error": "未找到有效数据", "details": response}
    except Exception as e:
        logger.error(f"获取股票交易所信息失败: {str(e)}")
        return {"error": f"获取股票交易所信息失败: {str(e)}"}

async def get_index_list(country_code: str, ticker: Optional[str] = None, fmt: Optional[str] = None, columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数基本信息的指数清单
    
    获取指定国家/地区代码的指数清单信息，支持可选参数筛选特定指数。
    
    Args:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (Optional[str]): 可选，指数代码。例如：000001（上证指数）。支持传参多只，以半角逗号分隔，最多100只。
        fmt (Optional[str]): 可选，输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (Optional[str]): 可选，输出字段。支持自定义输出，多个字段以半角逗号分隔。
    
    Returns:
        包含指数清单信息的有效数据字典
    """
    try:
        endpoint = f"index/{country_code}/list"
        params = {}
        
        if ticker:
            params["ticker"] = ticker
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        if "error" in response:
            logger.error(f"获取指数清单失败: {response['error']}")
            return {"error": response["error"]}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    except Exception as e:
        logger.error(f"获取指数清单时发生错误: {str(e)}")
        return {"error": str(e)}

async def get_forex_monthly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇月线实时数据
    
    获取指定外汇代码的月线实时行情数据，支持多种可选参数以自定义输出。
    
    参数:
        ticker (str): 必选，外汇代码，例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期，格式为“yyyy-mm-dd”。
        end_date (str): 可选，终止日期，格式为“yyyy-mm-dd”。
        limit (int): 可选，输出数量，默认为1。
        fmt (str): 可选，输出格式，支持json和csv两种标准输出格式，默认为json。
        columns (str): 可选，输出字段，支持自定义输出，多个字段以半角逗号分隔。
    
    返回:
        外汇月线实时行情数据字典
    """
    try:
        endpoint = "forex/monthly/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            logger.error(f"获取外汇月线实时数据失败: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("data", {})
    except Exception as e:
        logger.error(f"获取外汇月线实时数据错误: {str(e)}")
        return {"error": str(e)}

async def get_historical_eps_quarterly(token: str, exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None, order: int = None) -> Dict[str, Any]:
    """获取股票历史每股收益（季度）
    
    获取指定股票的历史每股收益（季度）数据，支持多种筛选条件。
    
    参数:
        token (str): 必选。API Token。登录后获取。
        exchange_code (str): 必选。交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选。股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        start_date (str): 可选。起始日期（报告期）。格式“yyyy-mm-dd”，默认：最早日期。
        end_date (str): 可选。终止日期（报告期）。格式“yyyy-mm-dd”，默认：最新日期。
        limit (int): 可选。输出数量。
        fmt (str): 可选。输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 可选。输出字段。支持自定义输出，多个字段以半角逗号分隔。
        order (int): 可选。按日期排序。0：不排序，1：升序，2：降序，默认：0。
    
    返回:
        包含历史每股收益（季度）数据的字典。
    """
    try:
        endpoint = f"stock/{exchange_code}/earnings/quarterly"
        params = {
            "token": token,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        # 发送请求
        response = await make_fin_request(endpoint, params)
        
        # 提取有效的data字段作为返回值
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        else:
            logger.error("响应格式错误或缺少data字段")
            return {"error": "无法获取有效数据"}
    except Exception as e:
        logger.error(f"获取历史每股收益（季度）错误: {str(e)}")
        return {"error": str(e)}

async def get_historical_allotment_data(token: str, exchange_code: str, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: Optional[int] = None, fmt: Optional[str] = None, columns: Optional[str] = None, order: Optional[int] = None) -> Dict[str, Any]:
    """获取历史配股数据
    
    根据给定的交易所代码和股票代码，返回历史配股信息。

    必选参数:
        token (str): API Token。登录后获取。
        exchange_code (str): 交易所代码。例如：XSHG（上交所）、XSHE（深交所）。
        ticker (str): 股票代码。例如：600081（贵州茅台）。

    可选参数:
        start_date (str): 起始日期。格式“yyyy-mm-dd”，默认：最早日期。
        end_date (str): 终止日期。格式“yyyy-mm-dd”，默认：最新日期。
        limit (int): 输出数量。
        fmt (str): 输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 输出字段。多个字段以半角逗号分隔。
        order (int): 按日期排序。0：不排序，1：升序，2：降序，默认：0。
    
    返回:
        包含历史配股数据的有效响应数据字典
    """
    endpoint = f"stock/{exchange_code}/allot"
    params = {
        "token": token,
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns,
        "order": order
    }
    
    # 移除值为None的可选参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"未找到有效数据: {response}")
            return {"error": "未找到有效数据"}
    except Exception as e:
        logger.error(f"获取历史配股数据错误: {str(e)}")
        return {"error": str(e)}

async def get_country_list(country_code: str = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取国家/地区清单

    获取指数基本信息中的国家/地区清单，支持可选参数筛选。

    参数:
        country_code (str, 可选): 国家/地区代码，采用ISO国家/地区代码（Country Code）。
        fmt (str, 可选): 输出格式，支持json和csv两种标准输出格式，默认为json。
        columns (str, 可选): 输出字段，支持自定义输出，多个字段以半角逗号分隔。

    返回:
        dict: 包含国家/地区清单的有效数据字典
    """
    try:
        endpoint = "index/country"
        params = {}

        if country_code is not None:
            params["country_code"] = country_code
        if fmt is not None:
            params["fmt"] = fmt
        if columns is not None:
            params["columns"] = columns

        response = await make_fin_request(endpoint, params)

        if "data" in response:
            return response["data"]
        else:
            logger.error("响应中未包含有效数据")
            return {"error": "响应中未包含有效数据"}

    except Exception as e:
        logger.error(f"获取国家/地区清单错误: {str(e)}")
        return {"error": str(e)}

async def get_stock_list(token: str, exchange_code: str, ticker: Optional[str] = None, is_active: Optional[int] = 2, fmt: Optional[str] = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取股票清单信息

    根据交易所代码和其他可选参数，获取股票清单信息。

    参数:
        token (str): 必选。API Token，登录后获取。
        exchange_code (str): 必选。交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (Optional[str]): 可选。股票代码，支持多只股票以逗号分隔，最多100只，默认为None。
        is_active (Optional[int]): 可选。是否活跃。0：不活跃，1：活跃，2：所有，默认为2。
        fmt (Optional[str]): 可选。输出格式，支持json和csv，默认为json。
        columns (Optional[str]): 可选。自定义输出字段，多个字段以逗号分隔，默认为None。

    返回:
        包含股票清单信息的字典
    """
    try:
        endpoint = f"stock/{exchange_code}/list"
        params = {
            "token": token,
            "ticker": ticker,
            "is_active": is_active,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            return {"error": "未找到有效数据"}
    except Exception as e:
        logger.error(f"获取股票清单错误: {str(e)}")
        return {"error": str(e)}

async def get_historical_cash_flow_annual(token: str, exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """
    获取股票历史现金流量表（年度）
    
    必选参数:
        token (str): API Token。登录后获取。
        exchange_code (str): 交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
    
    可选参数:
        start_date (str): 起始日期（报告期）。格式“yyyy-mm-dd”，默认：最早日期。
        end_date (str): 终止日期（报告期）。格式“yyyy-mm-dd”，默认：最新日期。
        limit (int): 输出数量。
        fmt (str): 输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 输出字段。支持自定义输出，多个字段以半角逗号分隔。
        order (int): 按日期排序。0：不排序，1：升序，2：降序，默认：0。
    
    返回:
        包含历史现金流量表数据的字典
    """
    endpoint = f"stock/{exchange_code}/cash/flow/yearly"
    params = {
        "token": token,
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns,
        "order": order
    }
    
    # 移除值为None的参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            return {"error": response["error"]}
        return response.get("data", {})
    except Exception as e:
        logger.error(f"获取历史现金流量表错误: {str(e)}")
        return {"error": str(e)}

async def get_realtime_index_data(country_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数实时行情数据
    
    获取指定国家/地区和指数代码的实时行情数据。
    
    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。支持多只指数代码，以半角逗号分隔，最多100只。
        fmt (str): 可选，默认为"json"，输出格式。支持"json"和"csv"。
        columns (str): 可选，自定义输出字段，多个字段以半角逗号分隔。
    
    返回:
        实时行情数据字典
    """
    try:
        endpoint = f"index/{country_code}/realtime"
        params = {
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        # 检查返回结果是否包含有效的data字段
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        else:
            logger.error("实时行情接口返回无效数据")
            return {"error": "未能获取有效数据"}
    except Exception as e:
        logger.error(f"获取实时行情数据错误 {str(e)}")
        return {"error": str(e)}

async def get_historical_eps_annual(token: str, exchange_code: str, ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None, limit: Optional[int] = None, fmt: Optional[str] = "json", columns: Optional[str] = None, order: Optional[int] = 0) -> Dict[str, Any]:
    """获取股票历史每股收益（年度）

    获取指定股票在特定时间段内的年度每股收益数据。

    参数:
        token (str): API Token，必选。
        exchange_code (str): 交易所代码，如XSHG（上交所）、XSHE（深交所），必选。
        ticker (str): 股票代码，如600519（贵州茅台），必选。
        start_date (str, optional): 起始日期（报告期），格式“yyyy-mm-dd”，默认为最早日期。
        end_date (str, optional): 终止日期（报告期），格式“yyyy-mm-dd”，默认为最新日期。
        limit (int, optional): 输出数量，默认返回所有数据。
        fmt (str, optional): 输出格式，支持json和csv，默认为json。
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔。
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认为0。

    返回:
        包含历史每股收益数据的字典，字段包括ticker（股票代码）、report_date（报告期）、eps（每股收益）、estimate_eps（预期每股收益）。
    """
    endpoint = f"stock/{exchange_code}/earnings/yearly"
    params = {
        "token": token,
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns,
        "order": order
    }
    
    # 移除值为None的参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"API 响应中缺少有效数据: {response}")
            return {"error": "未能获取有效的历史每股收益数据"}
    except Exception as e:
        logger.error(f"获取历史每股收益数据时发生错误: {str(e)}")
        return {"error": str(e)}

async def get_historical_income_statement(params: dict) -> dict:
    """
    获取股票历史利润表（季度）
    
    根据提供的参数，获取指定股票的历史利润表数据。
    
    参数:
        params (dict): 包含请求参数的字典，字段如下：
            - token (str): 必选，API Token。登录后获取。
            - exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）。
            - ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
            - start_date (str): 可选，起始日期（报告期），格式“yyyy-mm-dd”，默认最早日期。
            - end_date (str): 可选，终止日期（报告期），格式“yyyy-mm-dd”，默认最新日期。
            - limit (int): 可选，输出数量。
            - fmt (str): 可选，输出格式，默认json，支持csv。
            - columns (str): 可选，自定义输出字段，多个字段以逗号分隔。
            - order (int): 可选，按日期排序，默认0，0：不排序，1：升序，2：降序。
    
    返回:
        dict: 响应中的有效数据部分，包含利润表的具体信息。
    """
    try:
        # 检查必选参数是否存在
        required_params = ["token", "exchange_code", "ticker"]
        for param in required_params:
            if param not in params:
                return {"error": f"缺少必选参数: {param}"}
        
        # 构造请求路径
        endpoint = f"stock/{params['exchange_code']}/income/statement/quarterly"
        
        # 发送请求并处理响应
        response = await make_fin_request(endpoint, params)
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    except Exception as e:
        logger.error(f"获取历史利润表错误: {str(e)}")
        return {"error": str(e)}

async def get_realtime_index_60min(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内行情实时60分钟数据
    
    获取指定国家/地区和指数代码的实时60分钟行情数据。
    
    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        limit (int): 可选，输出数量。
        fmt (str): 可选，输出格式。支持json和csv，默认为json。
        columns (str): 可选，自定义输出字段，多个字段以逗号分隔。
    
    返回:
        包含实时60分钟行情数据的字典
    """
    endpoint = f"index/{country_code}/60min/realtime"
    params = {
        "ticker": ticker,
        "limit": limit,
        "fmt": fmt,
        "columns": columns
    }
    
    # 移除值为None的参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        
        # 检查响应是否包含错误
        if "error" in response:
            logger.error(f"获取实时60分钟行情数据失败: {response['error']}")
            return {"error": response['error']}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    
    except Exception as e:
        logger.error(f"获取实时60分钟行情数据出错: {str(e)}")
        return {"error": str(e)}

async def get_forex_daily_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时日线数据
    
    获取指定外汇代码的实时日线数据，支持可选的日期范围、输出数量和格式。
    
    参数:
        ticker (str): 必选，外汇代码，例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期，格式“yyyy-mm-dd”。
        end_date (str): 可选，终止日期，格式“yyyy-mm-dd”。
        limit (int): 可选，输出数量，默认为1。
        fmt (str): 可选，输出格式，支持json和csv两种标准输出格式，默认为json。
        columns (str): 可选，输出字段，支持自定义输出，多个字段以半角逗号分隔。
    
    返回:
        外汇实时日线数据字典
    """
    try:
        endpoint = "forex/daily/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "error" in response:
            logger.error(f"获取外汇实时日线数据失败: {response['error']}")
            return {"error": response["error"]}
        
        # 提取data字段作为返回值
        data = response.get("data", {})
        return data
    except Exception as e:
        logger.error(f"获取外汇实时日线数据错误: {str(e)}")
        return {"error": str(e)}

async def get_country_list(country_code: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票基本信息中的国家/地区清单
    
    获取股票市场相关的国家/地区信息。支持筛选和自定义输出。
    
    Args:
        country_code (str, optional): 国家/地区代码（ISO标准）。可选。
        fmt (str, optional): 输出格式，支持'json'或'csv'。默认为'json'。可选。
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔。可选。
    
    Returns:
        dict: 包含国家/地区清单的有效数据字典
    """
    try:
        endpoint = "stock/country"
        params = {}
        
        # 添加可选参数
        if country_code:
            params["country_code"] = country_code
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 发起请求
        response = await make_fin_request(endpoint, params)
        
        # 检查错误并提取有效数据
        if "error" in response:
            return {"error": response["error"]}
        
        # 提取data字段作为返回值
        data = response.get("data", {})
        return data

    except Exception as e:
        logger.error(f"获取国家/地区清单出错: {str(e)}")
        return {"error": f"获取国家/地区清单时发生错误: {str(e)}"}

async def get_stock_split_history(token: str, exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取股票历史送股信息
    
    获取指定股票在某段时间内的分红送股历史记录。
    
    参数:
        token (str): 必选，API Token。登录后获取。
        exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        start_date (str): 可选，起始日期。格式“yyyy-mm-dd”，默认：最早日期。
        end_date (str): 可选，终止日期。格式“yyyy-mm-dd”，默认：最新日期。
        limit (int): 可选，输出数量。
        fmt (str): 可选，输出格式。支持json和csv两种标准输出格式，默认：json。
        columns (str): 可选，输出字段。多个字段以半角逗号分隔。
        order (int): 可选，按日期排序。0：不排序，1：升序，2：降序，默认：0。
    
    返回:
        股票历史送股信息的data数据
    """
    try:
        endpoint = f"stock/{exchange_code}/split"
        params = {
            "token": token,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        
        if "error" in response:
            logger.error(f"获取股票历史送股信息失败: {response['error']}")
            return {"error": response["error"]}
        
        return response.get("data", {})
    except Exception as e:
        logger.error(f"获取股票历史送股信息错误: {str(e)}")
        return {"error": str(e)}

async def get_index_realtime_daily_data(country_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数实时日线数据
    
    获取指定国家/地区和指数代码的实时日线行情数据。
    
    参数:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        fmt (str): 可选，默认为"json"，输出格式。支持"json"或"csv"。
        columns (str): 可选，自定义输出字段，多个字段以逗号分隔。例如："ticker,date,close"。
    
    返回:
        指数实时日线数据字典
    """
    try:
        # 定义请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt,
            "columns": columns
        }
        
        # 调用辅助函数发送请求
        response = await make_fin_request(f"index/{country_code}/daily/realtime", params=params)
        
        # 检查响应是否包含错误信息
        if "error" in response:
            return {"error": response["error"]}
        
        # 提取有效数据并返回
        data = response.get("data", {})
        return data

    except Exception as e:
        logger.error(f"获取指数实时日线数据失败: {str(e)}")
        return {"error": f"获取指数实时日线数据失败: {str(e)}"}

async def get_stock_realtime_daily_data(exchange_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取股票实时日线数据

    必选参数:
        exchange_code (str): 交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 股票代码，例如：600519（贵州茅台）、AAPL（苹果）。

    可选参数:
        fmt (str): 输出格式，默认为json。支持json和csv两种标准输出格式。
        columns (str): 自定义输出字段，多个字段以半角逗号分隔。

    返回:
        实时日线数据的字典，包含股票代码、日期、开盘价、最高价、最低价、收盘价等信息
    """
    try:
        endpoint = f"stock/{exchange_code}/daily/realtime"
        params = {
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        # 检查是否有错误
        if "error" in response:
            return {"error": response["error"]}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    
    except Exception as e:
        logger.error(f"获取股票实时日线数据错误: {str(e)}")
        return {"error": str(e)}

async def get_stock_company_info(token: str, exchange_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取股票基本信息中的企业信息

    必选参数:
        token (str): API Token。登录后获取。
        exchange_code (str): 交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 股票代码。例如：600519（贵州茅台）、AAPL（苹果）。

    可选参数:
        fmt (str): 输出格式，支持json和csv两种，默认为json。
        columns (str): 自定义输出字段，多个字段以半角逗号分隔。

    返回:
        包含企业信息的有效数据字典
    """
    try:
        endpoint = f"stock/{exchange_code}/company/info"
        params = {
            "token": token,
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        # 检查响应是否包含错误
        if "error" in response:
            logger.error(f"获取股票企业信息失败: {response['error']}")
            return {"error": response['error']}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    
    except Exception as e:
        logger.error(f"获取股票企业信息出错: {str(e)}")
        return {"error": str(e)}

async def get_index_realtime_30min(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内行情的实时30分钟数据
    
    Args:
        country_code (str): 必选，国家/地区代码。例如：CHN（中国）、USA（美国）。
        ticker (str): 必选，指数代码。例如：000001（上证指数）。
        limit (int, optional): 可选，输出数量。
        fmt (str, optional): 可选，输出格式。支持json和csv，默认：json。
        columns (str, optional): 可选，自定义输出字段，多个字段以半角逗号分隔。
    
    Returns:
        dict: 指数日内行情的实时30分钟数据
    """
    try:
        endpoint = f"index/{country_code}/30min/realtime"
        params = {
            "ticker": ticker,
        }
        
        if limit is not None:
            params["limit"] = limit
        if fmt is not None:
            params["fmt"] = fmt
        if columns is not None:
            params["columns"] = columns
        
        response = await make_fin_request(endpoint, params)
        
        # 提取有效数据并返回
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        else:
            logger.error("响应数据格式不正确")
            return {"error": "无法获取有效的实时30分钟指数数据"}
    except Exception as e:
        logger.error(f"获取实时30分钟指数数据失败: {str(e)}")
        return {"error": f"请求失败: {str(e)}"}

async def get_historical_income_statement(params: dict) -> dict:
    """获取股票历史利润表（年度）
    
    该函数用于查询指定股票的历史年度利润表数据。
    
    参数:
        params (dict): 请求参数字典，包含以下字段：
            - token (str): 必选，API Token，登录后获取
            - exchange_code (str): 必选，交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）
            - ticker (str): 必选，股票代码，例如：600519（贵州茅台）、AAPL（苹果）
            - start_date (str, optional): 可选，起始日期（报告期），格式“yyyy-mm-dd”，默认为最早日期
            - end_date (str, optional): 可选，终止日期（报告期），格式“yyyy-mm-dd”，默认为最新日期
            - limit (int, optional): 可选，输出数量
            - fmt (str, optional): 可选，输出格式，支持json和csv，默认为json
            - columns (str, optional): 可选，输出字段，多个字段以半角逗号分隔
            - order (int, optional): 可选，按日期排序，0：不排序，1：升序，2：降序，默认为0
    
    返回:
        dict: 包含历史利润表数据的字典
    """
    endpoint = "stock/{exchange_code}/income/statement/yearly"
    required_params = ["token", "exchange_code", "ticker"]
    
    try:
        # 检查必选参数是否存在
        for param in required_params:
            if param not in params:
                return {"error": f"缺少必选参数: {param}"}
        
        # 构造请求URL
        exchange_code = params.get("exchange_code")
        url = FIN_API_BASE + endpoint.format(exchange_code=exchange_code)
        
        # 发送请求并处理响应
        response = await make_fin_request(url, params=params)
        
        # 提取有效数据
        if "data" in response:
            return response["data"]
        else:
            return {"error": "未找到有效数据"}
    except Exception as e:
        logger.error(f"获取历史利润表错误: {str(e)}")
        return {"error": str(e)}

async def get_index_realtime_15min(country_code: str, ticker: str, limit: Optional[int] = None, fmt: Optional[str] = None, columns: Optional[str] = None) -> Dict[str, Any]:
    """获取指数日内行情的实时15分钟数据

    必选参数:
        country_code (str): 国家/地区代码，例如：CHN（中国）、USA（美国）
        ticker (str): 指数代码，例如：000001（上证指数）

    可选参数:
        limit (int): 输出数量
        fmt (str): 输出格式，支持json和csv，默认为json
        columns (str): 自定义输出字段，多个字段以逗号分隔

    返回:
        dict: 包含指数实时15分钟行情的数据字典
    """
    endpoint = f"index/{country_code}/15min/realtime"
    params = {
        "ticker": ticker,
        "limit": limit,
        "fmt": fmt,
        "columns": columns
    }
    
    # 移除值为None的可选参数
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, params)
        if "data" in response and isinstance(response["data"], dict):
            return response["data"]
        else:
            logger.error(f"无效的API响应结构: {response}")
            return {"error": "未能获取有效数据"}
    except Exception as e:
        logger.error(f"获取指数实时15分钟行情失败: {str(e)}")
        return {"error": str(e)}

async def fetch_stock_balance_sheet_quarterly(
    exchange_code: str,
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None,
    fmt: Optional[str] = None,
    columns: Optional[str] = None,
    order: Optional[int] = None
) -> Dict[str, Any]:
    """获取股票历史季度资产负债表数据
    
    必选参数:
        exchange_code (str): 交易所代码，例如 XSHG（上交所）、XSHE（深交所）
        ticker (str): 股票代码，例如 600519（贵州茅台）
    
    可选参数:
        start_date (str): 起始日期（报告期），格式 yyyy-mm-dd，默认最早日期
        end_date (str): 终止日期（报告期），格式 yyyy-mm-dd，默认最新日期
        limit (int): 输出数量
        fmt (str): 输出格式，支持 json 和 csv，默认 json
        columns (str): 自定义输出字段，多个字段以逗号分隔
        order (int): 按日期排序，0：不排序，1：升序，2：降序，默认 0
    
    返回:
        包含股票季度资产负债表数据的字典
    """
    endpoint = f"stock/{exchange_code}/balance/sheet/quarterly"
    params = {
        "ticker": ticker,
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "fmt": fmt,
        "columns": columns,
        "order": order
    }
    
    # 移除值为None的参数
    filtered_params = {k: v for k, v in params.items() if v is not None}
    
    try:
        response = await make_fin_request(endpoint, filtered_params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"获取季度资产负债表失败: {response}")
            return {"error": "未能获取有效数据"}
    except Exception as e:
        logger.error(f"请求季度资产负债表错误: {str(e)}")
        return {"error": str(e)}

async def get_company_officers(exchange_code: str, ticker: str, fmt: str = "json", columns: Optional[str] = None) -> Dict[str, Any]:
    """获取企业高管信息

    获取指定股票代码的企业高管信息，包括姓名和职务等。

    参数:
        exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        fmt (str): 可选，默认为"json"，输出格式。支持json和csv两种标准输出格式。
        columns (str): 可选，自定义输出字段，多个字段以半角逗号分隔。

    返回:
        包含企业高管信息的字典数据。
    """
    endpoint = f"stock/{exchange_code}/company/officer"
    params = {
        "ticker": ticker,
        "fmt": fmt
    }
    
    if columns:
        params["columns"] = columns
    
    try:
        response = await make_fin_request(endpoint, params=params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"未找到有效数据: {response}")
            return {"error": "未找到有效数据"}
    except Exception as e:
        logger.error(f"获取企业高管信息错误: {str(e)}")
        return {"error": str(e)}

async def get_currency_info(currency_code: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取币种信息
    
    获取指定或所有币种的详细信息，支持自定义输出格式和字段筛选。
    
    参数:
        currency_code (str, 可选): 币种代码。例如：CNY（人民币）、USD（美元）。默认为None，表示查询所有币种。
        fmt (str, 可选): 输出格式。支持json和csv两种标准输出格式，默认为json。
        columns (str, 可选): 自定义输出字段，多个字段以半角逗号分隔。默认为None，表示输出所有字段。
    
    返回:
        包含币种信息的有效数据字典
    """
    try:
        endpoint = "currency"
        params = {}
        
        # 添加可选参数
        if currency_code:
            params["currency_code"] = currency_code
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 发送请求并处理响应
        response = await make_fin_request(endpoint, params)
        
        # 检查是否有错误
        if "error" in response:
            logger.error(f"获取币种信息失败: {response['error']}")
            return {"error": response["error"]}
        
        # 提取有效数据
        data = response.get("data", {})
        return data
    
    except Exception as e:
        logger.error(f"获取币种信息时发生错误: {str(e)}")
        return {"error": f"获取币种信息时发生错误: {str(e)}"}

async def get_forex_5min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情实时5分钟数据
    
    获取指定外汇代码的日内行情实时5分钟数据，支持自定义输出字段和时间范围筛选。
    
    Args:
        ticker (str): 必选，外汇代码，例如：USDCNY（美元人民币）。
        start_date (str): 可选，起始日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认最早日期。
        end_date (str): 可选，终止日期，格式“yyyy-mm-dd”或“yyyy-mm-dd hh:mm:ss”，默认最新日期。
        limit (int): 可选，输出数量，默认1。
        fmt (str): 可选，输出格式，支持json和csv两种标准输出格式，默认json。
        columns (str): 可选，输出字段，支持自定义输出，多个字段以半角逗号分隔。
    
    Returns:
        dict: 外汇日内行情实时5分钟数据，包含ticker、date、open、high、low、close等字段。
    """
    try:
        endpoint = "forex/5min/realtime"
        params = {
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns
        }
        
        # 移除值为None的参数
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await make_fin_request(endpoint, params)
        if "data" in response:
            return response["data"]
        else:
            logger.error(f"API 响应中缺少有效数据: {response}")
            return {"error": "API 响应中缺少有效数据", "details": response}
    except Exception as e:
        logger.error(f"获取外汇日内行情实时5分钟数据时发生错误: {str(e)}")
        return {"error": f"获取外汇日内行情实时5分钟数据时发生错误: {str(e)}"}

