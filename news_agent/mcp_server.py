from mcp.server.fastmcp import FastMCP
from news_agent.tools.news_tool import fetch_news

# Create an MCP server
mcp = FastMCP("NewsAgentServer")

@mcp.tool()
def get_latest_news(query: str, count: int = 5) -> str:
    """
    Fetches and returns the latest news articles for a given topic.
    """
    results = fetch_news(query, page_size=count)
    if isinstance(results, str):
        return results
    
    output = []
    for i, art in enumerate(results, 1):
        output.append(f"{i}. {art['title']} ({art['source']})\n   {art['description']}\n   Link: {art['url']}\n")
    
    return "\n".join(output)

if __name__ == "__main__":
    mcp.run()
