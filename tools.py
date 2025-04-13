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
FIN_API_TOKEN = os.environ.get("FIN_API_TOKEN", "your_api_token")
FIN_API_BASE = "https://api.tsanghi.com/fin"

# 辅助函数
async def make_fin_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
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

async def get_exchange_list(exchange_code: str = None, country_code: str = None) -> Dict[str, Any]:
    """获取交易所清单
    
    Args:
        exchange_code: 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），可选
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (List[Dict]): 交易所数据列表，每个交易所包含以下字段:
                - exchange_code (str): 交易所代码
                - exchange_name (str): 交易所名称
                - exchange_name_short (str): 交易所简称
                - country_code (str): 国家/地区代码
                - currency_code (str): 币种代码
                - local_open (str): 开盘时间(当地)
                - local_close (str): 收盘时间(当地)
                - beijing_open (str): 开盘时间(北京)
                - beijing_close (str): 收盘时间(北京)
                - timezone (str): 时区
                - delay (str): 延时
                - notes (str): 备注
    """
    try:
        # 构建请求参数
        params = {}
        if exchange_code:
            params["exchange_code"] = exchange_code
        if country_code:
            params["country_code"] = country_code
        
        # 调用 API
        response = await make_fin_request("stock/exchange", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取交易所清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到交易所数据",
            "data": []
        }
    except Exception as e:
        logger.error(f"获取交易所清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取交易所清单时发生错误: {str(e)}",
            "data": []
        }


async def get_historical_balance_sheet_annual(
    exchange_code: str,
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    fmt: str = "json",
    columns: str = None,
    order: int = 0
) -> Dict[str, Any]:
    """获取股票历史资产负债表（年度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str, optional): 起始日期（报告期），格式 "yyyy-mm-dd"，默认：最早日期
        end_date (str, optional): 终止日期（报告期），格式 "yyyy-mm-dd"，默认：最新日期
        limit (int, optional): 输出数量
        fmt (str, optional): 输出格式，支持 "json" 和 "csv" 两种，默认：json
        columns (str, optional): 输出字段，多个字段以半角逗号分隔
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认：0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 历史资产负债表数据，包含多个财务字段
    """
    try:
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt,
            "order": order
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/balance/sheet/yearly", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史资产负债表（年度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史资产负债表数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史资产负债表（年度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史资产负债表（年度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_realtime_5min(country_code: str, ticker: str, limit: int = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数实时5分钟行情数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        limit (int, optional): 输出数量，默认返回全部数据
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数实时5分钟行情数据，包含以下主要字段:
                - ticker (str): 指数代码
                - date (str): 日期时间，格式为 "yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如有）
                - pre_close (float): 昨收价（如有）
    """
    try:
        # 验证必填参数
        if not country_code or not ticker:
            return {
                "success": False,
                "message": "缺少必填参数：country_code 或 ticker",
                "data": {}
            }
        
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "country_code": country_code,
            "ticker": ticker
        }
        
        if limit is not None:
            params["limit"] = limit
        if fmt in ["json", "csv"]:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/5min/realtime", params)
        
        if "error" in response:
            return {
                "success": False,
                "message": f"API 错误: {response['error']}",
                "data": {}
            }
        
        return {
            "success": True,
            "message": "获取指数实时5分钟行情成功",
            "data": response.get("data", {})
        }
    
    except Exception as e:
        logger.error(f"获取指数实时5分钟行情错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时5分钟行情时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_yearly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时年线数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date (str, optional): 起始日期，格式"yyyy-mm-dd"，可选
        end_date (str, optional): 终止日期，格式"yyyy-mm-dd"，可选
        limit (int, optional): 输出数量，默认：1，可选
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认：json，可选
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇实时年线数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期，格式"yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（默认不输出，可以用参数columns指定输出）
    """
    try:
        # 构建请求参数
        params = {
            "ticker": ticker
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/yearly/realtime", params)
        
        if "data" in response and isinstance(response["data"], dict):
            return {
                "success": True,
                "message": "获取外汇实时年线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇实时年线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇实时年线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇实时年线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_country_list(country_code: str = None) -> Dict[str, Any]:
    """获取国家/地区清单
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 国家/地区数据，包含以下字段:
                - country_code (str): 国家/地区代码
                - country_name (str): 国家/地区名称
    """
    try:
        # 构建请求参数
        params = {}
        if country_code:
            params["country_code"] = country_code
        
        # 调用 API
        response = await make_fin_request("country", params)
        
        if "data" in response and isinstance(response["data"], dict):
            return {
                "success": True,
                "message": "获取国家/地区清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到国家/地区数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取国家/地区清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取国家/地区清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_monthly_realtime_data(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票实时月线数据
    
    Args:
        exchange_code (str): 必选，交易所代码。例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）。
        ticker (str): 必选，股票代码。例如：600519（贵州茅台）、AAPL（苹果）。
        fmt (str): 可选，输出格式，默认为 "json"。支持 "json" 和 "csv" 格式。
        columns (str): 可选，自定义输出字段，多个字段以半角逗号分隔。
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 股票实时月线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中指定输出）
                - pre_close (float): 昨收价（如果请求中指定输出）
    """
    try:
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/monthly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取股票实时月线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到股票实时月线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取股票实时月线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票实时月线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_monthly_realtime(country_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数实时月线数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国）
        ticker (str): 指数代码，例如 "000001"（上证指数）
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数实时月线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float, optional): 成交额（如果请求中包含该字段）
                - pre_close (float, optional): 昨收价（如果请求中包含该字段）
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/monthly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数实时月线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数实时月线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数实时月线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时月线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_list(ticker: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取外汇清单
    
    Args:
        ticker: 外汇代码，例如 "USDCNY"（美元/人民币）。支持多只代码以逗号分隔，最多100只，可选
        fmt: 输出格式，支持 "json" 和 "csv"，默认为 "json"，可选
        columns: 输出字段，支持自定义输出字段，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇数据字典，包含以下字段:
                - ticker (str): 外汇代码
                - name (str): 外汇名称
    """
    try:
        # 构建请求参数
        params = {}
        if ticker:
            params["ticker"] = ticker
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/list", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_15min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情实时15分钟数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date (str, optional): 起始日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最早日期
        end_date (str, optional): 终止日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最新日期
        limit (int, optional): 输出数量，默认：1
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认：json
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇数据字典，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期时间（UTC时间），格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, 可选): 昨收价
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/15min/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇日内行情实时15分钟数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇日内行情实时15分钟数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇日内行情实时15分钟数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇日内行情实时15分钟数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_30min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情的实时30分钟数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币）
        start_date (str, optional): 起始日期，格式为 "yyyy-mm-dd" 或 "yyyy-mm-dd hh:mm:ss"
        end_date (str, optional): 终止日期，格式为 "yyyy-mm-dd" 或 "yyyy-mm-dd hh:mm:ss"
        limit (int, optional): 输出数量，默认为 1
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 输出字段，多个字段以半角逗号分隔，默认输出所有字段
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇日内行情的实时30分钟数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期时间（UTC时间），格式 "yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（需要通过columns参数指定输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/30min/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇日内行情的实时30分钟数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇日内行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇日内行情的实时30分钟数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇日内行情的实时30分钟数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_weekly_realtime(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票实时周线数据
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）
        fmt (str): 输出格式，默认为 "json"，可选 "csv"
        columns (str): 自定义输出字段，多个字段以逗号分隔，例如 "ticker,date,open,close"
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 实时周线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中包含）
                - pre_close (float): 昨收价（如果请求中包含）
    """
    try:
        # 验证必填参数
        if not exchange_code or not ticker:
            return {
                "success": False,
                "message": "参数错误：exchange_code 和 ticker 是必填项",
                "data": {}
            }
        
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        endpoint = f"stock/{exchange_code}/weekly/realtime"
        response = await make_fin_request(endpoint, params)
        
        if "error" in response:
            return {
                "success": False,
                "message": f"API 错误: {response['error']}",
                "data": {}
            }
        
        # 处理返回数据
        if isinstance(response, dict) and response:
            return {
                "success": True,
                "message": "获取股票实时周线数据成功",
                "data": response
            }
        
        return {
            "success": False,
            "message": "未获取到股票实时周线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取股票实时周线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票实时周线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_weekly_realtime(country_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数实时周线数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        fmt (str): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str): 自定义输出字段，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数实时周线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中指定了该字段）
                - pre_close (float): 昨收价（如果请求中指定了该字段）
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/weekly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数实时周线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数实时周线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数实时周线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时周线数据时发生错误: {str(e)}",
            "data": {}
        }

async def search_financial_instruments(token: str, keywords: str, type: str = None, where: str = None, match_whole: int = 0, match_case: int = 0, exchange_code: str = None, country_code: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """搜索金融工具（股票、指数、ETF基金、外汇、加密货币等）
    
    Args:
        token (str): API Token，登录后获取，必选
        keywords (str): 搜索关键词，至少1个字符，必选
        type (str, optional): 类型。STOCK：股票，INDEX：指数，ETF：ETF基金，FOREX：外汇，CRYPTO：加密货币，默认：所有
        where (str, optional): 搜索位置。TICKER：从代码中搜索，NAME：从名称中搜索，默认：所有
        match_whole (int, optional): 匹配全词。0：不匹配全词，1：匹配全词，默认：0
        match_case (int, optional): 区分大小写。0：不区分大小写，1：区分大小写，默认：0
        exchange_code (str, optional): 交易所代码，例如：XSHG（上交所）、XSHE（深交所）、XNAS（纳斯达克）
        country_code (str, optional): 国家/地区代码，例如：CHN（中国）、USA（美国）
        fmt (str, optional): 输出格式。支持json和csv两种标准输出格式，默认：json
        columns (str, optional): 输出字段，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 搜索结果数据，包含以下字段:
                - ticker (str): 代码
                - name (str): 名称
                - exchange_code (str): 交易所代码
                - country_code (str): 国家/地区代码
                - type (str): 类型（STOCK、INDEX、ETF、FOREX、CRYPTO）
    """
    try:
        # 构建请求参数
        params = {
            "token": token,
            "keywords": keywords,
            "match_whole": match_whole,
            "match_case": match_case
        }
        
        if type:
            params["type"] = type
        if where:
            params["where"] = where
        if exchange_code:
            params["exchange_code"] = exchange_code
        if country_code:
            params["country_code"] = country_code
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("search/list", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "搜索金融工具成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未找到相关金融工具",
            "data": {}
        }
    except Exception as e:
        logger.error(f"搜索金融工具错误: {str(e)}")
        return {
            "success": False,
            "message": f"搜索金融工具时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_realtime(ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取外汇实时行情
    
    Args:
        ticker: 外汇代码，例如 "USDCNY"（美元人民币），必选
        fmt: 输出格式，支持 "json" 和 "csv" 两种，默认为 "json"
        columns: 自定义输出字段，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 实时行情数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期时间（UTC时间），格式 "yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价（最新价）
                - pre_close (float): 昨收价（如果请求中指定输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker, "fmt": fmt}
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/realtime", params)
        
        if "ticker" in response and response["ticker"]:
            return {
                "success": True,
                "message": "获取外汇实时行情成功",
                "data": response
            }
        
        return {
            "success": False,
            "message": "未获取到外汇实时行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇实时行情错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇实时行情时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_weekly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时周线数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date (str, optional): 起始日期，格式 "yyyy-mm-dd"，可选
        end_date (str, optional): 终止日期，格式 "yyyy-mm-dd"，可选
        limit (int, optional): 输出数量，默认 1，可选
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认 "json"，可选
        columns (str, optional): 输出字段，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇实时周线数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（默认不输出，可以用参数 columns 指定输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/weekly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇实时周线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇实时周线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇实时周线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇实时周线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_60min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情实时60分钟数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date (str, optional): 起始日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最早日期
        end_date (str, optional): 终止日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最新日期
        limit (int, optional): 输出数量，默认：1
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认：json
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇60分钟实时行情数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期时间（UTC时间），格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（需要指定columns参数才会返回）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/60min/realtime", params)
        
        if "data" in response and isinstance(response["data"], dict):
            return {
                "success": True,
                "message": "获取外汇60分钟实时行情成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇60分钟实时行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇60分钟实时行情错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇60分钟实时行情时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_dividends(exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, order: int = 0) -> Dict[str, Any]:
    """获取历史分红数据
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）
        start_date (str, optional): 起始日期，格式 "yyyy-mm-dd"，默认为最早日期
        end_date (str, optional): 终止日期，格式 "yyyy-mm-dd"，默认为最新日期
        limit (int, optional): 输出数量限制
        order (int, optional): 排序方式，0：不排序，1：升序，2：降序，默认：0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 分红数据，包含以下字段:
                - ticker (str): 股票代码
                - dividends (List[Dict]): 分红记录列表，每个记录包含:
                    - date (str): 分红日期，格式 "yyyy-mm-dd"
                    - dividend (float): 分红金额
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "order": order
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/dividend", params)
        
        # 处理响应数据
        if "data" in response and isinstance(response["data"], list):
            processed_data = {
                "ticker": ticker,
                "dividends": [
                    {
                        "date": item.get("date"),
                        "dividend": item.get("dividend")
                    }
                    for item in response["data"]
                ]
            }
            return {
                "success": True,
                "message": "获取历史分红数据成功",
                "data": processed_data
            }
        
        return {
            "success": False,
            "message": "未获取到分红数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史分红数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史分红数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_constituents(country_code: str, ticker: str = None, constituent: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数成分股信息
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker: 指数代码，例如 "000001"（上证指数），可选
        constituent: 成份股代码，例如 "600519"（贵州茅台），可选
        fmt: 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns: 自定义输出字段，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数成分股数据，包含以下字段:
                - ticker (str): 指数代码
                - constituent (str): 成分股代码
    """
    try:
        # 验证必填参数
        if not country_code:
            return {
                "success": False,
                "message": "缺少必填参数 country_code",
                "data": {}
            }
        
        # 至少需要提供 ticker 或 constituent 中的一个
        if not ticker and not constituent:
            return {
                "success": False,
                "message": "ticker 和 constituent 至少需要提供一个",
                "data": {}
            }
        
        # 构建请求参数
        params = {"country_code": country_code}
        if ticker:
            params["ticker"] = ticker
        if constituent:
            params["constituent"] = constituent
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/constituent", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数成分股信息成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数成分股数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数成分股信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数成分股信息时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_yearly_realtime(country_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数的实时年线数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 自定义输出字段，多个字段以半角逗号分隔，例如 "ticker,date,open,close"
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数实时年线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中指定了该字段）
                - pre_close (float): 昨收价（如果请求中指定了该字段）
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/yearly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数实时年线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数实时年线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数实时年线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时年线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_realtime_yearly_data(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票实时年线数据
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        fmt (str): 输出格式，支持 "json" 和 "csv" 两种标准输出格式，默认为 "json"，可选
        columns (str): 输出字段，支持自定义输出，多个字段以半角逗号分隔，例如 "ticker,date,open,close"，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 股票实时年线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中指定了该字段）
                - pre_close (float): 昨收价（如果请求中指定了该字段）
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/yearly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取股票实时年线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到股票实时年线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取股票实时年线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票实时年线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_exchange_info(exchange_code: str = None, country_code: str = None) -> Dict[str, Any]:
    """获取股票交易所信息
    
    Args:
        exchange_code (str, optional): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）。默认为 None。
        country_code (str, optional): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国）。默认为 None。
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - exchange_info (Dict): 交易所详细信息，包含以下字段:
                - exchange_code (str): 交易所代码
                - exchange_name (str): 交易所名称
                - exchange_name_short (str): 交易所简称
                - country_code (str): 国家/地区代码
                - currency_code (str): 币种代码
                - local_open (str): 开盘时间(当地)
                - local_close (str): 收盘时间(当地)
                - beijing_open (str): 开盘时间(北京)
                - beijing_close (str): 收盘时间(北京)
                - timezone (str): 时区
                - delay (str): 延时
                - notes (str): 备注
    """
    try:
        # 构建请求参数
        params = {}
        if exchange_code:
            params["exchange_code"] = exchange_code
        if country_code:
            params["country_code"] = country_code
        
        # 调用 API 获取交易所清单
        response = await make_fin_request("stock/exchange", params)
        
        if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
            # 提取第一个匹配的交易所信息
            exchange_data = response["data"][0]
            return {
                "success": True,
                "message": "获取交易所信息成功",
                "exchange_info": {
                    "exchange_code": exchange_data.get("exchange_code", ""),
                    "exchange_name": exchange_data.get("exchange_name", ""),
                    "exchange_name_short": exchange_data.get("exchange_name_short", ""),
                    "country_code": exchange_data.get("country_code", ""),
                    "currency_code": exchange_data.get("currency_code", ""),
                    "local_open": exchange_data.get("local_open", ""),
                    "local_close": exchange_data.get("local_close", ""),
                    "beijing_open": exchange_data.get("beijing_open", ""),
                    "beijing_close": exchange_data.get("beijing_close", ""),
                    "timezone": exchange_data.get("timezone", ""),
                    "delay": exchange_data.get("delay", ""),
                    "notes": exchange_data.get("notes", "")
                }
            }
        
        return {
            "success": False,
            "message": "未找到对应的交易所信息",
            "exchange_info": {}
        }
    except Exception as e:
        logger.error(f"获取交易所信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取交易所信息时发生错误: {str(e)}",
            "exchange_info": {}
        }

async def get_index_list(country_code: str, ticker: str = None, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数清单
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker: 指数代码，例如 "000001"（上证指数），可选，支持多个代码以逗号分隔，最多100个
        fmt: 输出格式，默认为 "json"，可选值为 "json" 或 "csv"
        columns: 输出字段，支持自定义输出，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数数据，包含以下字段:
                - ticker (str): 指数代码
                - name (str): 指数名称
                - country_code (str): 国家/地区代码
    """
    try:
        # 构建请求参数
        params = {"country_code": country_code}
        if ticker:
            params["ticker"] = ticker
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("index/list", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_monthly_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时月线数据
    
    Args:
        ticker (str): 外汇代码，例如 USDCNY（美元人民币），必选
        start_date (str, optional): 起始日期，格式"yyyy-mm-dd"，可选
        end_date (str, optional): 终止日期，格式"yyyy-mm-dd"，可选
        limit (int, optional): 输出数量，默认：1，可选
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认：json，可选
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇实时月线数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期，格式"yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（默认不输出，可以用参数columns指定输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/monthly/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇实时月线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇实时月线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇实时月线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇实时月线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_eps_quarterly(exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取股票的历史每股收益（季度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）。必选。
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）。必选。
        start_date (str, optional): 起始日期（报告期），格式为 "yyyy-mm-dd"。默认为最早日期。
        end_date (str, optional): 终止日期（报告期），格式为 "yyyy-mm-dd"。默认为最新日期。
        limit (int, optional): 输出数量。默认不限制。
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"。默认为 "json"。
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔。默认返回所有字段。
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序。默认为 0。
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 历史每股收益数据，包含以下字段:
                - ticker (str): 股票代码
                - report_date (str): 报告期，格式为 "yyyy-mm-dd"
                - eps (float): 每股收益
                - estimate_eps (float): 预期每股收益
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 调用 API
        endpoint = f"stock/{exchange_code}/earnings/quarterly"
        response = await make_fin_request(endpoint, params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史每股收益（季度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史每股收益数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史每股收益（季度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史每股收益（季度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_allotment(token: str, exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取股票历史配股信息
    
    Args:
        token (str): API Token，登录后获取
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）
        ticker (str): 股票代码，例如 "600081"（贵州茅台）
        start_date (str, optional): 起始日期，格式 "yyyy-mm-dd"，默认为最早日期
        end_date (str, optional): 终止日期，格式 "yyyy-mm-dd"，默认为最新日期
        limit (int, optional): 输出数量限制
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 自定义输出字段，多个字段用逗号分隔
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认为 0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 配股数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - allot_factor (float): 配股因子
                - allot_price (float): 配股价格
    """
    try:
        # 构建请求参数
        params = {
            "token": token,
            "exchange_code": exchange_code,
            "ticker": ticker
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        if order in [0, 1, 2]:
            params["order"] = order
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/allot", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史配股信息成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史配股信息",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史配股信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史配股信息时发生错误: {str(e)}",
            "data": {}
        }

async def get_country_list(country_code: str = None) -> Dict[str, Any]:
    """获取国家/地区清单
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 国家/地区数据，包含以下字段:
                - country_code (str): 国家/地区代码
                - country_name (str): 国家/地区名称
                - timezone (str): 时区
                - delay (str): 延时
                - notes (str): 备注
    """
    try:
        # 构建请求参数
        params = {}
        if country_code:
            params["country_code"] = country_code
        
        # 调用 API
        response = await make_fin_request("index/country", params)
        
        if "data" in response and isinstance(response["data"], dict):
            return {
                "success": True,
                "message": "获取国家/地区清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到国家/地区数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取国家/地区清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取国家/地区清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_list(exchange_code: str, ticker: str = None, is_active: int = 2, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票清单
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，支持多只以逗号分隔，最多100只，可选
        is_active (int): 是否活跃，0：不活跃，1：活跃，2：所有，默认为2，可选
        fmt (str): 输出格式，支持 "json" 和 "csv"，默认为 "json"，可选
        columns (str): 输出字段，支持自定义输出，多个字段以逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 股票数据，每个股票包含以下字段:
                - ticker (str): 股票代码
                - name (str): 股票名称
                - is_active (int): 是否活跃，1：活跃，0：不活跃
                - exchange_code (str): 交易所代码
                - country_code (str): 国家或地区代码
                - currency_code (str): 币种代码
    """
    try:
        # 构建请求参数
        params = {"exchange_code": exchange_code}
        if ticker:
            params["ticker"] = ticker
        if is_active in [0, 1, 2]:
            params["is_active"] = is_active
        if fmt in ["json", "csv"]:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/list", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取股票清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到股票数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取股票清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_cash_flow_annual(exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取股票的历史现金流量表（年度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str, optional): 起始日期（报告期），格式"yyyy-mm-dd"，默认：最早日期
        end_date (str, optional): 终止日期（报告期），格式"yyyy-mm-dd"，默认：最新日期
        limit (int, optional): 输出数量
        fmt (str, optional): 输出格式，支持 "json" 和 "csv" 两种，默认：json
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认：0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 财务数据，包含以下字段:
                - ticker (str): 股票代码
                - report_date (str): 报告期，格式"yyyy-mm-dd"
                - currency_code (str): 币种代码
                - net_cash_flow_operating (float): 经营活动产生的现金流量净额
                - net_cash_flow_invest (float): 投资活动产生的现金流量净额
                - net_cash_flow_finance (float): 筹资活动产生的现金流量净额
                - cash_equivalent_increase (float): 现金及现金等价物净增加额
                - cash_equivalents_begin_period (float): 期初现金及现金等价物余额
                - cash_equivalents_end_period (float): 期末现金及现金等价物余额
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/cash/flow/yearly", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史现金流量表（年度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史现金流量表（年度）数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史现金流量表（年度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史现金流量表（年度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_realtime_data(country_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数实时行情数据
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker: 指数代码，例如 "000001"（上证指数），必选。支持多只指数查询，以半角逗号分隔，最多100只
        fmt: 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns: 自定义输出字段，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 实时行情数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期时间，格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价（最新价）
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中包含该字段）
                - pre_close (float): 昨收价（如果请求中包含该字段）
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数实时行情数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数实时行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数实时行情数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时行情数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_eps_annual(exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取股票历史每股收益（年度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str, optional): 起始日期（报告期），格式 "yyyy-mm-dd"，默认：最早日期
        end_date (str, optional): 终止日期（报告期），格式 "yyyy-mm-dd"，默认：最新日期
        limit (int, optional): 输出数量
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认：json
        columns (str, optional): 输出字段，多个字段以半角逗号分隔
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认：0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 历史每股收益数据，包含以下字段:
                - ticker (str): 股票代码
                - report_date (str): 报告期，格式 "yyyy-mm-dd"
                - eps (float): 每股收益
                - estimate_eps (float): 预期每股收益
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "fmt": fmt,
            "columns": columns,
            "order": order
        }
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/earnings/yearly", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史每股收益（年度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史每股收益数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史每股收益（年度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史每股收益（年度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_income_statement(
    exchange_code: str,
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    fmt: str = "json",
    columns: str = None,
    order: int = 0
) -> Dict[str, Any]:
    """获取股票的历史利润表（季度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）
        start_date (str, optional): 起始日期（报告期），格式 "yyyy-mm-dd"
        end_date (str, optional): 终止日期（报告期），格式 "yyyy-mm-dd"
        limit (int, optional): 输出数量
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认 "json"
        columns (str, optional): 输出字段，多个字段以逗号分隔
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认 0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 利润表数据，包含多个财务指标
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
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
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/income/statement/quarterly", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史利润表成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史利润表数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史利润表错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史利润表时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_60min_realtime(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内行情实时60分钟数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        limit (int, optional): 输出数量，默认为 None
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 输出字段，多个字段以半角逗号分隔，默认为 None
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 实时60分钟行情数据，包含以下字段:
                - ticker (str): 指数代码
                - date (str): 日期时间，格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float, 可选): 成交额
                - pre_close (float, 可选): 昨收价
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker
        }
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/60min/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数日内行情实时60分钟数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数日内行情实时60分钟数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数日内行情实时60分钟数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数日内行情实时60分钟数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_daily_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇实时日线数据
    
    Args:
        ticker: 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date: 起始日期，格式 "yyyy-mm-dd"，可选
        end_date: 终止日期，格式 "yyyy-mm-dd"，可选
        limit: 输出数量，默认 1，可选
        fmt: 输出格式，支持 "json" 和 "csv"，默认 "json"，可选
        columns: 输出字段，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇实时日线数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float): 昨收价（如果请求中指定了输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/daily/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇实时日线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇实时日线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇实时日线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇实时日线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_country_list(country_code: str = None) -> Dict[str, Any]:
    """获取国家/地区清单
    
    Args:
        country_code: 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 国家/地区数据，包含以下字段:
                - country_code (str): 国家/地区代码
                - country_name (str): 国家/地区名称
    """
    try:
        # 构建请求参数
        params = {}
        if country_code:
            params["country_code"] = country_code
        
        # 调用 API
        response = await make_fin_request("stock/country", params)
        
        if "data" in response and isinstance(response["data"], dict):
            return {
                "success": True,
                "message": "获取国家/地区清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到国家/地区数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取国家/地区清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取国家/地区清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_stock_splits(exchange_code: str, ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = "json", columns: str = None, order: int = 0) -> Dict[str, Any]:
    """获取历史股票拆分信息
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str, optional): 起始日期，格式 "yyyy-mm-dd"，默认为最早日期
        end_date (str, optional): 终止日期，格式 "yyyy-mm-dd"，默认为最新日期
        limit (int, optional): 输出数量，可选
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认为 "json"
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选
        order (int, optional): 按日期排序，0：不排序，1：升序，2：降序，默认为 0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 股票拆分数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式 "yyyy-mm-dd"
                - split_factor (float): 拆分因子，例如：每10股转赠2股，拆分因子为1.2
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt,
            "order": order
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/split", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史股票拆分信息成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史股票拆分数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史股票拆分信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史股票拆分信息时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_realtime_daily(country_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取指数实时日线数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        fmt (str): 输出格式，支持 "json" 和 "csv" 两种，默认为 "json"，可选
        columns (str): 自定义输出字段，多个字段以半角逗号分隔，例如 "ticker,date,close"，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数实时日线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float): 成交额（如果请求中指定输出）
                - pre_close (float): 昨收价（如果请求中指定输出）
    """
    try:
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/daily/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数实时日线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数实时日线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数实时日线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数实时日线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_realtime_daily(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票实时日线数据
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）
        fmt (str, optional): 输出格式，默认为 "json"，支持 "json" 和 "csv"
        columns (str, optional): 自定义输出字段，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 股票实时日线数据，包含以下字段:
                - ticker (str): 股票代码
                - date (str): 日期，格式为 "yyyy-mm-dd"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float, 可选): 成交额
                - pre_close (float, 可选): 昨收价
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/daily/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取股票实时日线数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到股票实时日线数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取股票实时日线数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票实时日线数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_stock_company_info(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取股票企业信息
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克）
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果）
        fmt (str, optional): 输出格式，支持 "json" 或 "csv"，默认为 "json"
        columns (str, optional): 自定义输出字段，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 企业信息数据，包含以下主要字段:
                - ticker (str): 股票代码
                - name (str): 股票名称
                - company_name (str): 公司名称
                - exchange_code (str): 交易所代码
                - country_code (str): 国家/地区代码
                - currency_code (str): 币种代码
                - isin_code (str): 国际证券识别代码
                - lei_code (str): 全球法人识别代码
                - gics_sector_name (str): GICS行业部门名称
                - ipo_date (str): 上市日期，格式 "yyyy-mm-dd"
                - description (str): 简介
                - business_scope (str): 经营范围
                - address (str): 地址
                - phone (str): 电话
                - email (str): 电子邮箱
                - website (str): 网址
                - employee (int): 员工人数
    """
    try:
        # 参数验证
        if not exchange_code or not ticker:
            return {
                "success": False,
                "message": "exchange_code 和 ticker 是必填参数",
                "data": {}
            }
        
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt
        }
        
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/company/info", params)
        
        if "error" in response:
            return {
                "success": False,
                "message": f"获取企业信息失败: {response['error']}",
                "data": {}
            }
        
        return {
            "success": True,
            "message": "获取企业信息成功",
            "data": response.get("data", {})
        }
    
    except Exception as e:
        logger.error(f"获取股票企业信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取股票企业信息时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_realtime_30min(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内行情实时30分钟数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        limit (int, optional): 输出数量，可选
        fmt (str, optional): 输出格式，支持 "json" 和 "csv" 两种，默认为 "json"，可选
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 指数日内行情实时30分钟数据，包含以下字段:
                - ticker (str): 指数代码
                - date (str): 日期时间，格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float, 可选): 成交额
                - pre_close (float, 可选): 昨收价
    """
    try:
        # 构建请求参数
        params = {
            "token": FIN_API_TOKEN,
            "country_code": country_code,
            "ticker": ticker
        }
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/30min/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取指数日内行情实时30分钟数据成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到指数日内行情实时30分钟数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数日内行情实时30分钟数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数日内行情实时30分钟数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_income_statement_annual(
    exchange_code: str,
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    fmt: str = "json",
    columns: str = None,
    order: int = 0
) -> Dict[str, Any]:
    """获取股票的历史利润表（年度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str): 起始日期（报告期），格式"yyyy-mm-dd"，默认：最早日期，可选
        end_date (str): 终止日期（报告期），格式"yyyy-mm-dd"，默认：最新日期，可选
        limit (int): 输出数量，可选
        fmt (str): 输出格式，支持 "json" 和 "csv" 两种标准输出格式，默认：json，可选
        columns (str): 输出字段，支持自定义输出，多个字段以半角逗号分隔，可选
        order (int): 按日期排序，0：不排序，1：升序，2：降序，默认：0，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 利润表数据，包含多个字段如 ticker, report_date, currency_code 等
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt,
            "order": order
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/income/statement/yearly", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史利润表（年度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史利润表（年度）数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史利润表（年度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史利润表（年度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_index_realtime_15min(country_code: str, ticker: str, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取指数日内行情实时15分钟数据
    
    Args:
        country_code (str): 国家/地区代码，例如 "CHN"（中国）、"USA"（美国），必选
        ticker (str): 指数代码，例如 "000001"（上证指数），必选
        limit (int, optional): 输出数量，默认不限制
        fmt (str, optional): 输出格式，支持 "json" 和 "csv"，默认 "json"
        columns (str, optional): 自定义输出字段，多个字段以逗号分隔，默认全部字段
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 行情数据，包含以下字段:
                - ticker (str): 指数代码
                - date (str): 日期时间，格式为 "yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - volume (float): 成交量
                - amount (float, optional): 成交额（如果请求中指定）
                - pre_close (float, optional): 昨收价（如果请求中指定）
    """
    try:
        # 验证必填参数
        if not country_code or not ticker:
            return {
                "success": False,
                "message": "缺少必填参数：country_code 或 ticker",
                "data": {}
            }
        
        # 构建请求参数
        params = {
            "country_code": country_code,
            "ticker": ticker
        }
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"index/{country_code}/15min/realtime", params)
        
        if "error" in response:
            return {
                "success": False,
                "message": f"API 错误: {response['error']}",
                "data": {}
            }
        
        if "data" in response and isinstance(response["data"], list) and len(response["data"]) > 0:
            return {
                "success": True,
                "message": "获取指数日内行情实时15分钟数据成功",
                "data": response["data"][0]
            }
        
        return {
            "success": False,
            "message": "未获取到有效的行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取指数日内行情实时15分钟数据错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取指数日内行情实时15分钟数据时发生错误: {str(e)}",
            "data": {}
        }

async def get_historical_balance_sheet_quarterly(
    exchange_code: str,
    ticker: str,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    fmt: str = None,
    columns: str = None,
    order: int = None
) -> Dict[str, Any]:
    """获取历史资产负债表（季度）
    
    Args:
        exchange_code (str): 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker (str): 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        start_date (str, optional): 起始日期（报告期）。格式"yyyy-mm-dd"，默认：最早日期
        end_date (str, optional): 终止日期（报告期）。格式"yyyy-mm-dd"，默认：最新日期
        limit (int, optional): 输出数量
        fmt (str, optional): 输出格式。支持json和csv两种标准输出格式，默认：json
        columns (str, optional): 输出字段。支持自定义输出，多个字段以半角逗号分隔
        order (int, optional): 按日期排序。0：不排序，1：升序，2：降序，默认：0
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 财务报表数据，包含多个字段如:
                - ticker (str): 股票代码
                - report_date (str): 报告期。格式"yyyy-mm-dd"
                - currency_code (str): 币种代码
                - total_current_assets (float): 流动资产合计
                - cash_equivalents (float): 货币资金
                - total_non_current_assets (float): 非流动资产合计
                - total_assets (float): 资产总计
                - total_current_liability (float): 流动负债合计
                - total_non_current_liability (float): 非流动负债合计
                - total_liability (float): 负债合计
                - paidin_capital (float): 实收资本（或股本）
                - equities_parent_company_owners (float): 归属于母公司股东权益合计
                - total_owner_equities (float): 股东权益合计
                - total_liability_and_owner_equities (float): 负债和股东权益合计
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        if order is not None:
            params["order"] = order
        
        # 调用 API
        endpoint = f"stock/{exchange_code}/balance/sheet/quarterly"
        response = await make_fin_request(endpoint, params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取历史资产负债表（季度）成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到历史资产负债表（季度）数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取历史资产负债表（季度）错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取历史资产负债表（季度）时发生错误: {str(e)}",
            "data": {}
        }

async def get_company_executives(exchange_code: str, ticker: str, fmt: str = "json", columns: str = None) -> Dict[str, Any]:
    """获取企业高管信息
    
    Args:
        exchange_code: 交易所代码，例如 "XSHG"（上交所）、"XSHE"（深交所）、"XNAS"（纳斯达克），必选
        ticker: 股票代码，例如 "600519"（贵州茅台）、"AAPL"（苹果），必选
        fmt: 输出格式，支持 "json" 和 "csv"，默认为 "json"，可选
        columns: 自定义输出字段，多个字段以逗号分隔，例如 "ticker,name,title"，可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 高管数据，包含以下字段:
                - ticker (str): 股票代码
                - name (str): 姓名
                - title (str): 职务
    """
    try:
        # 构建请求参数
        params = {
            "exchange_code": exchange_code,
            "ticker": ticker,
            "fmt": fmt
        }
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request(f"stock/{exchange_code}/company/officer", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取企业高管信息成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到企业高管数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取企业高管信息错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取企业高管信息时发生错误: {str(e)}",
            "data": {}
        }

async def get_currency_list(currency_code: str = None) -> Dict[str, Any]:
    """获取币种清单
    
    Args:
        currency_code: 币种代码，例如 "CNY"（人民币）、"USD"（美元），可选
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict[str, Any]): 币种数据，包含以下字段:
                - currency_code (str): 币种代码
                - currency_name (str): 币种名称
    """
    try:
        # 构建请求参数
        params = {}
        if currency_code:
            params["currency_code"] = currency_code
        
        # 调用 API
        response = await make_fin_request("currency", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取币种清单成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到币种数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取币种清单错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取币种清单时发生错误: {str(e)}",
            "data": {}
        }

async def get_forex_5min_realtime(ticker: str, start_date: str = None, end_date: str = None, limit: int = None, fmt: str = None, columns: str = None) -> Dict[str, Any]:
    """获取外汇日内行情的实时5分钟数据
    
    Args:
        ticker (str): 外汇代码，例如 "USDCNY"（美元人民币），必选
        start_date (str, optional): 起始日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最早日期
        end_date (str, optional): 终止日期，格式"yyyy-mm-dd"或"yyyy-mm-dd hh:mm:ss"，默认：最新日期
        limit (int, optional): 输出数量，默认：1
        fmt (str, optional): 输出格式，支持json和csv两种标准输出格式，默认：json
        columns (str, optional): 输出字段，支持自定义输出，多个字段以半角逗号分隔
    
    Returns:
        Dict[str, Any]: 包含以下字段的字典:
            - success (bool): 请求是否成功
            - message (str): 成功或错误信息
            - data (Dict): 外汇5分钟实时行情数据，包含以下字段:
                - ticker (str): 外汇代码
                - date (str): 日期时间（UTC时间），格式"yyyy-mm-dd hh:mm:ss"
                - open (float): 开盘价
                - high (float): 最高价
                - low (float): 最低价
                - close (float): 收盘价
                - pre_close (float, optional): 昨收价（默认不输出，可以用参数columns指定输出）
    """
    try:
        # 构建请求参数
        params = {"ticker": ticker}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit is not None:
            params["limit"] = limit
        if fmt:
            params["fmt"] = fmt
        if columns:
            params["columns"] = columns
        
        # 调用 API
        response = await make_fin_request("forex/5min/realtime", params)
        
        if "data" in response and response["data"]:
            return {
                "success": True,
                "message": "获取外汇5分钟实时行情成功",
                "data": response["data"]
            }
        
        return {
            "success": False,
            "message": "未获取到外汇5分钟实时行情数据",
            "data": {}
        }
    except Exception as e:
        logger.error(f"获取外汇5分钟实时行情错误: {str(e)}")
        return {
            "success": False,
            "message": f"获取外汇5分钟实时行情时发生错误: {str(e)}",
            "data": {}
        }

