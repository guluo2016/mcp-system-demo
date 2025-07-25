from mcp_client import McpClientDemo
from google import genai
from google.genai import types
from google.genai.types import Tool, FunctionDeclaration

import asyncio

gemini_model = genai.Client()

async def main():
    # 使用上下文管理器确保资源自动清理
    async with McpClientDemo() as mcp_client:
        try:
            tools = await mcp_client.list_mcp_tools()
            gemini_tools = []
            for tool in tools:
                function_declaration = FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema
                )
                gemini_tools.append(Tool(function_declarations=[function_declaration]))
            await chat(mcp_client, gemini_tools)
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()

async def call_llm(mcp_client: McpClientDemo, question: str="Hello!", tools: list = None):
    print()
    print("==================================================================================")
    print("Gemini模型开始处理问题:", question)
    print("==================================================================================")
    print()
    response = gemini_model.models.generate_content(
        model="gemini-2.5-flash", contents=question,
        config=types.GenerateContentConfig(
            tools=tools
        )
    )
    for part in response.candidates[0].content.parts:
        if part.function_call:
            print("Gemini判断该问题需要进行函数调用")
            print(f"Gemini判断需要调用MCP Tool名称: {part.function_call.name}, 需要传入的参数: {part.function_call.args}")
            mcp_tool_response = await mcp_client.call_mcp_tool(part)
            print()
            print("==================================================================================")
            print("Gemini模型调用MCP Tool返回的结果:", mcp_tool_response)
            print("==================================================================================")
            print()

            prompt = f"""
            经函数调用获得问题结果是：{mcp_tool_response}, 请你总结这个结果，并返回。
"""
            r = gemini_model.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            print("*********************************************************************************")
            print("最终，Gemini模型返回的内容:")
            print(r.candidates[0].content.parts[0].text)
            print("*********************************************************************************")
            print()
        else:
            print("不需要进行函数调用")
            print()
            print("**********************************************************************************")
            print("Gemini模型直接返回的内容:")
            print(part.text)
            print("**********************************************************************************")
            print()

async def chat(mcp_client: McpClientDemo = None, tools: list = None):
    question = """
    你是一个AI助手,我现在有两个数a和b,a=10,b=2,请计算两数之和
"""
    await call_llm(mcp_client, question, tools)

if __name__ == "__main__":
    asyncio.run(main())