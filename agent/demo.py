"""
Demo Script - Agent 工作原理演示
=================================
运行此脚本可以看到 Agent 的完整工作流程：
Thought → Action → Observation 的循环过程

对比 ChatBot 模式和 Agent 模式的差异
"""

from agent import SimpleAgent


def demo_chatbot_vs_agent():
    """
    对比演示：ChatBot vs Agent

    ChatBot 模式 (传统):
        用户: "北京和上海的人口总和是多少？"
        ChatBot: "大约4600万吧" ← 可能不准确，因为是凭记忆回答

    Agent 模式 (ReAct):
        用户: "北京和上海的人口总和是多少？"
        Thought: 我需要分别搜索北京和上海的人口数据
        Action: search[北京人口]
        Observation: 北京市常住人口约为2189万
        Thought: 获得了北京数据，现在搜索上海数据
        Action: search[上海人口]
        Observation: 上海市常住人口约为2487万
        Thought: 现在我有足够数据，计算总和
        Action: calculator[2189+2487]
        Observation: 4676
        Thought: 得到了精确结果
        Action: finish[北京和上海人口总和约为4676万]
        ← 精确答案！因为使用了搜索工具和计算器
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║   ChatBot vs Agent 对比演示                                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  问题: "北京和上海的人口总和是多少？"                            ║
║                                                              ║
║  ChatBot 模式 (一步回答):                                     ║
║    Question ──→ Answer                                       ║
║    "大约4600万" ← 不精确，靠记忆猜测                            ║
║                                                              ║
║  Agent 模式 (多步循环):                                       ║
║    Question ──→ Thought ──→ Action ──→ Observation            ║
║           ──→ Thought ──→ Action ──→ Observation              ║
║           ──→ Thought ──→ Action ──→ Observation              ║
║           ──→ Final Answer                                   ║
║    "4676万" ← 精确，因为用了工具                                ║
║                                                              ║
║  Agent 的优势:                                                ║
║  [+] 通过工具获取真实数据，而不是凭记忆猜测                      ║
║  [+] 分步解决复杂问题，而不是一步给出可能错误的答案               ║
║  [+] 根据观察结果调整策略，而不是固守初始判断                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    agent = SimpleAgent()
    answer = agent.run("北京和上海的人口总和是多少？")
    agent.reset()

    print("""
╔══════════════════════════════════════════════════════════════╗
║   Agent 的三个核心组件                                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. LLM (大脑) - 决策层                                       ║
║     负责: 思考(Thought)和选择行动(Action)                      ║
║     也就是: "现在该做什么？"                                    ║
║                                                              ║
║  2. Tools (工具) - 执行层                                     ║
║     负责: 执行具体操作，获取信息                                ║
║     例如: 搜索、计算、查询数据库、调用API                        ║
║                                                              ║
║  3. Agent Loop (循环) - 协调层                                 ║
║     负责: 把大脑的指令传递给工具，把结果反馈给大脑                 ║
║     也就是: Thought → Action → Observation 的循环              ║
║                                                              ║
║  这三层架构构成了所有 Agent 系统的基础！                         ║
║  无论是 LangChain、AutoGPT 还是其他框架，核心都是这个模式        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")

    agent.run("光速飞行从地球到月球需要多长时间？")


if __name__ == "__main__":
    demo_chatbot_vs_agent()