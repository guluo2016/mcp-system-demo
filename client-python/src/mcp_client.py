from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
import os

server_params = StdioServerParameters(
    command="java",
    args=["-jar", os.path.join(os.path.dirname(__file__), "..", "..", "server-java", "target", "server-java-1.0.jar")],
    env=None
)

class McpClientDemo:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def __aenter__(self):
        await self.connect_mcp_server()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    async def connect_mcp_server(self):
        try:
            # 使用 AsyncExitStack 来管理异步上下文
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.read, self.write = stdio_transport
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.read, self.write)
            )
            
            await self.session.initialize()
            print("已成功连接到MCP服务器")
        except Exception as e:
            print(f"连接MCP服务器失败: {e}")
            await self.exit_stack.aclose()
            raise

    async def list_mcp_tools(self):
        if self.session is None:
            raise Exception("请先连接到MCP服务器")
        response = await self.session.list_tools()
        return response.tools
    
    async def call_mcp_tool(self, part):
        try:
            if self.session is None:
                raise Exception("请先连接到MCP服务器")
            
            result = await self.session.call_tool(
                name=part.function_call.name,
                arguments=part.function_call.args,   
            )
            return result.content
        except Exception as e:
            print(f"调用MCP工具时出错: {e}")
            raise

    async def close(self):
        try:
            if self.exit_stack:
                await self.exit_stack.aclose()
                print("已断开MCP服务器连接")
        except Exception as e:
            print(f"关闭连接时出错: {e}")
        finally:
            # 确保资源被标记为已清理
            self.session = None
