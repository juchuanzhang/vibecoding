"""
Simple Agent - ReAct Pattern Implementation
============================================

这是 Agent 最核心的工作原理 —— ReAct (Reason + Act) 模式：

    Question → Thought → Action → Observation → Thought → ... → Answer

与传统 ChatBot 的区别：
    ChatBot: Question → Answer (直接生成文本)
    Agent:   Question → 思考 → 行动 → 观察 → 再思考 → ... → 最终答案

ReAct 循环的每一步：
1. Thought (思考): Agent 分析当前情况，决定下一步做什么
2. Action (行动): Agent 选择并调用一个工具
3. Observation (观察): 工具返回结果，Agent 获得新信息
4. 重复1-3，直到 Agent 认为可以给出最终答案

这种"思考-行动-观察"的循环，就是 Agent 的本质。
就像人类解决问题一样：想一下 → 做一步 → 看结果 → 再想 → 再做 → ...

"""

import re
import os
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from tools import TOOL_REGISTRY, execute_tool


class SimpleAgent:
    """
    一个基于 ReAct 模式的简单 Agent

    Agent vs ChatBot 的关键差异：
    - ChatBot 只能生成文本，无法与外部交互
    - Agent 可以使用工具（计算器、搜索、API等）来获取信息和执行操作
    - Agent 有自主决策能力：根据观察结果决定下一步做什么
    """

    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo", max_iterations: int = 5):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.max_iterations = max_iterations
        self.history = []  # Agent 的记忆：记录所有 Thought/Action/Observation

    def _build_system_prompt(self) -> str:
        """
        构建 System Prompt —— Agent 的"规则手册"

        这告诉 LLM 它是一个 Agent（而不是普通 ChatBot），
        并且规定了它必须遵循的输出格式：
        - 必须先思考(Thought)，再行动(Action)
        - Action 必须是注册表中的工具之一
        - 格式必须是 Action: tool_name[tool_input]
        - 得到足够信息后用 Action: finish[answer] 结束
        """
        tool_descriptions = "\n".join(
            f"  - {t['name']}: {t['description']}"
            for t in TOOL_REGISTRY.values()
        )

        return f"""你是一个智能 Agent，使用 ReAct (Reason+Act) 模式来解决问题。

你必须严格按以下格式回答，每一步包含 Thought 和 Action：

Thought: 你的思考过程，分析当前情况，决定下一步行动
Action: 工具名称[工具输入]

可用工具：
{tool_descriptions}

当你已经收集到足够信息可以回答问题时，使用：
Action: finish[你的最终答案]

重要规则：
1. 每一步必须先思考(Thought)，再行动(Action)
2. 只能使用上面列出的工具
3. 不要跳过 Thought 直接给出 Action
4. 如果一次行动没有得到足够信息，继续思考并采取新的行动
"""

    def _build_user_prompt(self, question: str) -> str:
        """
        构建 User Prompt —— 把问题 + 历史记忆拼接起来

        这是 Agent 的"上下文管理"：
        每次调用 LLM 时，不仅要告诉它当前问题，
        还要告诉它之前所有的思考、行动和观察结果，
        这样 LLM 才能基于完整上下文做出下一步决策。
        """
        prompt = f"Question: {question}\n"

        for step in self.history:
            prompt += f"Thought: {step['thought']}\n"
            prompt += f"Action: {step['action']}\n"
            prompt += f"Observation: {step['observation']}\n"

        prompt += "Thought:"
        return prompt

    def _parse_response(self, response: str) -> dict:
        """
        解析 LLM 的响应 —— 提取 Thought 和 Action

        这是 Agent 框架的"输出解析器"：
        LLM 返回的是自然语言文本，Agent 框架需要从中提取出：
        - Thought: 思考内容
        - Action: 工具名称和输入参数

        解析 Action 的格式：Action: tool_name[tool_input]
        例如：Action: calculator[2+3] → tool_name="calculator", tool_input="2+3"
        例如：Action: finish[答案是5] → tool_name="finish", tool_input="答案是5"
        """
        thought_match = re.search(r"Thought:\s*(.+?)(?:\n|Action:)", response, re.DOTALL)
        action_match = re.search(r"Action:\s*(\w+)\[([^\]]+)\]", response)

        thought = thought_match.group(1).strip() if thought_match else response.strip()
        action = action_match.group(1).strip() if action_match else "finish"
        action_input = action_match.group(2).strip() if action_match else thought

        return {
            "thought": thought,
            "action": action,
            "action_input": action_input,
        }

    def _call_llm(self, question: str) -> str:
        """
        调用 LLM —— Agent 的"大脑"

        Agent 的核心架构：
        LLM 是决策层（大脑），负责思考和选择行动
        Tools 是执行层（手脚），负责实际操作和获取信息
        Agent 框架是协调层（中枢），负责把大脑的指令传递给手脚，再把结果反馈给大脑
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            messages = [
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user", "content": self._build_user_prompt(question)},
            ]

            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,  # temperature=0 让输出更稳定、更遵循格式
                max_tokens=500,
            )
            return completion.choices[0].message.content
        except ImportError:
            print("\n[提示] openai 包未安装，使用模拟推理引擎演示 Agent 流程")
            print("[提示] 安装方法: pip install openai\n")
            return self._mock_reasoning(question)
        except Exception as e:
            print(f"\n[提示] LLM API 调用失败: {e}，使用模拟推理引擎\n")
            return self._mock_reasoning(question)

    def _mock_reasoning(self, question: str) -> str:
        """
        模拟推理引擎 -- 不依赖 LLM API 也能演示 Agent 流程

        这个模拟引擎展示了 Agent 的工作流程:
        即使没有真正的 LLM, ReAct 循环的结构是完全一样的
        Thought -> Action -> Observation 的循环机制才是 Agent 的核心,
        LLM 只是负责填充 Thought 和选择 Action 的具体内容
        """
        search_keywords = {
            "北京": "北京人口",
            "上海": "上海人口",
            "深圳": "深圳人口",
            "人口": "中国人口",
            "面积": "北京面积",
            "月球": "地球到月球",
            "光速": "光速",
            "光年": "光年到公里",
            "比邻星": "比邻星距离",
        }

        def has_data(keyword):
            all_obs = "".join(step["observation"] for step in self.history)
            return keyword in all_obs

        def get_num(keyword):
            all_obs = "".join(step["observation"] for step in self.history)
            idx = all_obs.index(keyword)
            match = re.search(r'约为\s*(\d+)', all_obs[idx:])
            return match.group(1) if match else None

        if not self.history:
            matched_search = None
            for kw, search_key in search_keywords.items():
                if kw in question:
                    matched_search = search_key
                    break

            if matched_search:
                return f"Thought: 我需要搜索相关信息来回答这个问题\nAction: search[{matched_search}]"
            elif any(kw in question for kw in ["时间", "日期", "几点", "什么时候"]):
                return "Thought: 我需要查询当前时间\nAction: get_time[]"
            elif any(kw in question for kw in ["计算", "算", "+", "-", "*", "/", "乘", "除"]):
                math_expr = re.findall(r'[\d+\-*/().]+', question)
                if math_expr:
                    return f"Thought: 这需要数学计算\nAction: calculator[{math_expr[0]}]"
                return f"Thought: 我需要先搜索数据再计算\nAction: search[{question}]"
            else:
                return f"Thought: 我需要搜索相关信息\nAction: search[{question}]"
        else:
            last_action = self.history[-1]["action"]
            last_obs = self.history[-1]["observation"]

            # 优先: 如果上一步是计算器,给出最终答案
            if "calculator" in last_action:
                calc_result = last_obs.strip()
                if "光速" in question or "月球" in question:
                    try:
                        seconds = float(calc_result)
                        answer = f"光速飞行从地球到月球约需 {seconds:.2f} 秒 (约 {seconds/60:.4f} 分钟)"
                    except ValueError:
                        answer = calc_result
                elif "总和" in question or "多少" in question:
                    answer = f"经过搜索和计算,答案是: {calc_result}万"
                else:
                    answer = f"答案是: {calc_result}"
                return f"Thought: 计算完成,我可以给出最终答案\nAction: finish[{answer}]"

            if "未找到" in last_obs:
                for kw, search_key in search_keywords.items():
                    if kw in question and not has_data(search_key):
                        return f"Thought: 尝试搜索更具体的关键词\nAction: search[{search_key}]"
                return f"Thought: 无法找到相关信息\nAction: finish[抱歉,我无法找到足够的信息来回答这个问题]"

            # 北京+上海人口总和问题
            if "总和" in question or "之和" in question:
                has_bj = has_data("北京") and re.search(r'2189', "".join(step["observation"] for step in self.history))
                has_sh = has_data("上海") and re.search(r'2487', "".join(step["observation"] for step in self.history))
                if has_bj and not has_sh:
                    return "Thought: 找到了北京数据,现在需要搜索上海数据\nAction: search[上海人口]"
                if has_sh and not has_bj:
                    return "Thought: 找到了上海数据,现在需要搜索北京数据\nAction: search[北京人口]"
                if has_bj and has_sh:
                    bj_num = get_num("北京")
                    sh_num = get_num("上海")
                    if bj_num and sh_num:
                        return f"Thought: 找到了两个城市的数据,计算总和\nAction: calculator[{bj_num}+{sh_num}]"

            # 光速飞行到月球问题
            has_dist = has_data("地球到月球") and re.search(r'384400', "".join(step["observation"] for step in self.history))
            has_speed = has_data("光速") and re.search(r'30', "".join(step["observation"] for step in self.history))
            if has_dist and not has_speed:
                return "Thought: 找到了距离数据,还需要光速来计算时间\nAction: search[光速]"
            if has_speed and not has_dist:
                return "Thought: 找到了光速数据,还需要距离来计算时间\nAction: search[地球到月球]"
            if has_dist and has_speed:
                dist_num = get_num("地球到月球")
                return f"Thought: 找到了距离和光速数据,计算飞行时间(秒)\nAction: calculator[{dist_num}/300000]"

            # 其他情况: 基于搜索结果给出答案
            return f"Thought: 基于搜索结果,我可以给出答案\nAction: finish[{last_obs}]"

    def run(self, question: str) -> str:
        """
        Agent 主循环 —— ReAct 的核心执行流程

        这就是 Agent 的"灵魂"：
        循环执行 Thought → Action → Observation，
        直到 Agent 决定给出最终答案（Action: finish），
        或者达到最大迭代次数（防止无限循环）。

        对比传统 ChatBot：
        ChatBot: question → LLM → answer (一步完成)
        Agent:  question → [思考→行动→观察] × N → answer (多步循环)

        这个循环使得 Agent 能够：
        1. 分步解决复杂问题（而不是一次给出可能错误的答案）
        2. 通过工具获取真实数据（而不是凭记忆猜测）
        3. 根据观察结果调整策略（而不是固守初始判断）
        """
        print(f"\n{'='*60}")
        print(f"  Agent 开始处理问题: {question}")
        print(f"{'='*60}\n")

        for i in range(self.max_iterations):
            print(f"--- 第 {i+1} 步 (最多 {self.max_iterations} 步) ---")

            # Step 1: 调用 LLM 进行推理 (Thought + Action)
            print("[推理] 调用 Agent 大脑(LLM)进行思考...")
            response = self._call_llm(question)
            parsed = self._parse_response(response)

            print(f"Thought: {parsed['thought']}")
            print(f"Action: {parsed['action']}[{parsed['action_input']}]")

            # Step 2: 检查是否要结束（finish 是特殊的终止 Action）
            if parsed['action'] == "finish":
                print(f"\n{'='*60}")
                print(f"  [完成] Agent 最终答案: {parsed['action_input']}")
                print(f"{'='*60}")
                return parsed['action_input']

            # Step 3: 执行工具 (Action → Observation)
            print("[执行] 调用工具获取信息...")
            observation = execute_tool(parsed['action'], parsed['action_input'])
            print(f"Observation: {observation}\n")

            # Step 4: 记录到历史 (Agent 的记忆机制)
            # 每一步的结果都保存下来，下次推理时 LLM 能看到完整历史
            self.history.append({
                "thought": parsed['thought'],
                "action": f"{parsed['action']}[{parsed['action_input']}]",
                "observation": observation,
            })

        # 达到最大迭代次数，强制结束
        print(f"\n[警告] Agent 达到最大迭代次数({self.max_iterations})，强制结束")
        print(f"最后一轮观察: {self.history[-1]['observation']}")
        return self.history[-1]['observation']

    def reset(self):
        """重置 Agent 记忆 —— 开始处理新问题时清空历史"""
        self.history = []


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║        Simple Agent Demo - ReAct Pattern                     ║
║                                                              ║
║  Agent 工作原理:                                              ║
║  Question → Thought → Action → Observation → Thought → ...   ║
║                                                              ║
║  与普通 ChatBot 的区别:                                       ║
║  ChatBot: Question → Answer (一步直接回答)                     ║
║  Agent:   思考→行动→观察→再思考 (多步循环解决问题)               ║
║                                                              ║
║  支持 OpenAI API 和模拟推理两种模式                             ║
╚══════════════════════════════════════════════════════════════╝
""")

    agent = SimpleAgent()

    demo_questions = [
        "北京和上海的人口总和是多少？",
        "从地球到月球需要多长时间？光速飞行的话。",
    ]

    for q in demo_questions:
        answer = agent.run(q)
        agent.reset()
        print()

    print("\n[提示] 设置 OPENAI_API_KEY 环境变量可使用真实 LLM 推理")
    print("   例如: set OPENAI_API_KEY=sk-xxx  (Windows)")
    print("   或:   export OPENAI_API_KEY=sk-xxx  (Linux/Mac)")