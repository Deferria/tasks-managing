import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientError

# 模拟一组 API 端点
API_URLS = [
    "https://jsonplaceholder.typicode.com/posts/1",
    "https://jsonplaceholder.typicode.com/posts/2",
    "https://jsonplaceholder.typicode.com/posts/3",
    "https://jsonplaceholder.typicode.com/invalid-endpoint",  # 故意放一个错误的 URL
]

async def fetch_url(session: aiohttp.ClientSession, url: str) -> dict:
    """
    异步获取单个 API 的响应数据，包含重试和错误处理。
    """
    retries = 2  # 重试次数
    for attempt in range(retries + 1):
        try:
            # 设置超时，避免长时间阻塞
            timeout = ClientTimeout(total=10)
            async with session.get(url, timeout=timeout) as response:
                # 检查 HTTP 状态码
                response.raise_for_status()
                data = await response.json()
                return {
                    "url": url,
                    "status": response.status,
                    "data": data,
                    "error": None
                }
        except ClientError as e:
            error_msg = f"HTTP 错误: {e}"
        except asyncio.TimeoutError:
            error_msg = f"请求超时 (尝试 {attempt+1}/{retries+1})"
        except Exception as e:
            error_msg = f"其他错误: {type(e).__name__} - {e}"
        
        # 最后一次尝试失败则返回错误信息
        if attempt == retries:
            return {
                "url": url,
                "status": None,
                "data": None,
                "error": error_msg
            }
        # 重试前等待一小段时间
        await asyncio.sleep(0.5 * (attempt + 1))
    # 理论上不会执行到这里，但保留 return 防止语法警告
    return {"url": url, "error": "未知错误"}

async def fetch_all(urls: list) -> list:
    """
    并发请求多个 API，使用连接池优化。
    """
    # 设置连接器，限制最大连接数
    connector = aiohttp.TCPConnector(limit=10)  # 同一时间最多 10 个连接
    async with aiohttp.ClientSession(connector=connector) as session:
        # 创建所有任务
        tasks = [fetch_url(session, url) for url in urls]
        # 等待所有任务完成（如果某个任务失败不会影响其他任务）
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

async def main():
    print(f"开始异步请求 {len(API_URLS)} 个 API...")
    results = await fetch_all(API_URLS)
    
    # 打印结果
    for res in results:
        if res.get("error"):
            print(f"❌ 失败: {res['url']} - 错误: {res['error']}")
        else:
            # 仅显示部分数据，避免输出太长
            print(f"✅ 成功: {res['url']} (状态码 {res['status']})")
            # 例如：显示返回的标题
            if "title" in res["data"]:
                print(f"   标题: {res['data']['title']}")
            elif "name" in res["data"]:
                print(f"   名称: {res['data']['name']}")
            else:
                print(f"   数据: {str(res['data'])[:100]}...")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())