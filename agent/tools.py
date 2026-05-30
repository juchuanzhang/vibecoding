"""
Agent Tools Module
==================
Agent 的核心概念之一是"工具使用"(Tool Use)。
Agent 不像普通 ChatBot 只能生成文本，它能调用外部工具来完成具体任务。

工具的定义包含三个要素：
1. name: 工具名称，Agent 在推理时会用这个名称来选择工具
2. description: 工具描述，帮助 Agent 理解何时应该使用该工具
3. function: 工具的实际执行函数，接收参数并返回结果
"""

import math
import datetime


def calculator(expression: str) -> str:
    """
    计算器工具：执行数学表达式计算

    Agent 使用场景：当需要精确计算数学问题时，比让 LLM 直接算更可靠
    例如：LLM 算 1234 * 5678 可能出错，但 calculator 能给出精确结果
    """
    allowed_names = {
        "abs": abs, "round": round, "min": min, "max": max,
        "sqrt": math.sqrt, "pow": math.pow, "log": math.log,
        "sin": math.sin, "cos": math.cos, "pi": math.pi,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


def search(query: str) -> str:
    """
    搜索工具：模拟知识库/网络搜索

    Agent 使用场景：当需要获取自己不知道的事实性信息时
    真实场景中，这可以是调用搜索引擎API、查询数据库、检索文档等
    这里用模拟数据来演示原理
    """
    knowledge_base = {
        "北京人口": "北京市常住人口约为 2189 万（2023年数据）",
        "上海人口": "上海市常住人口约为 2487 万（2023年数据）",
        "深圳人口": "深圳市常住人口约为 1768 万（2023年数据）",
        "中国人口": "中国总人口约为 14.1 亿（2023年数据）",
        "北京面积": "北京市总面积约为 16410 平方公里",
        "上海面积": "上海市总面积约为 6340 平方公里",
        "深圳面积": "深圳市总面积约为 1997 平方公里",
        "中国面积": "中国总面积约为 960 万平方公里",
        "地球到月球": "地球到月球的平均距离约为 384400 公里",
        "光速": "光速约为 299792458 米/秒，即约 30 万公里/秒",
        "一年秒数": "一年约有 365 * 24 * 60 * 60 = 31536000 秒",
        "光年到公里": "一光年约等于 9.461 × 10^12 公里，即约 9.461万亿公里",
        "比邻星距离": "比邻星（离太阳最近的恒星）距离约为 4.24 光年",
        "太阳到比邻星": "太阳到比邻星的距离约为 4.24 光年，约 40.15万亿公里",
    }

    keywords = query.replace("？", "").replace("的", " ").replace("和", " ").split()
    keywords = [k for k in keywords if len(k) >= 2]

    results = []
    for key, value in knowledge_base.items():
        if any(kw in key for kw in keywords):
            results.append(value)

    if results:
        return "找到以下信息:\n" + "\n".join(results)
    else:
        all_keys = ", ".join(knowledge_base.keys())
        return f"未找到关于 '{query}' 的信息。\n可用查询关键词: {all_keys}"


def get_time(city: str = "") -> str:
    """
    时间工具：获取当前时间

    Agent 使用场景：当需要知道当前日期时间时
    LLM 本身不知道"现在"是什么时间，需要通过工具获取
    """
    now = datetime.datetime.now()
    if city:
        return f"{city}当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"
    return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"


# ---- 工具注册表 ----
# 这是 Agent 框架的关键设计：将所有工具统一注册到一个表中
# Agent 在推理时，会看到这个注册表，知道有哪些工具可用
TOOL_REGISTRY = {
    "calculator": {
        "name": "calculator",
        "description": "执行数学表达式计算，支持基本运算和数学函数(sqrt, sin, cos, log, pi等)。输入是一个数学表达式字符串。",
        "function": calculator,
    },
    "search": {
        "name": "search",
        "description": "搜索知识库获取事实性信息，如城市人口、面积、天文数据等。输入是搜索关键词。",
        "function": search,
    },
    "get_time": {
        "name": "get_time",
        "description": "获取当前日期和时间。输入可选城市名称。",
        "function": get_time,
    },
}


def execute_tool(tool_name: str, tool_input: str) -> str:
    """
    工具执行器：根据工具名称调用对应函数

    这是 Agent 与外部世界交互的桥梁：
    Agent 输出 "Action: calculator[2+3]" → 执行器解析后调用 calculator("2+3") → 返回 "5"
    """
    if tool_name not in TOOL_REGISTRY:
        return f"错误：未知工具 '{tool_name}'，可用工具: {list(TOOL_REGISTRY.keys())}"

    tool = TOOL_REGISTRY[tool_name]
    try:
        result = tool["function"](tool_input)
        return result
    except Exception as e:
        return f"工具执行错误: {e}"