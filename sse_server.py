# sse_server.py
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute
import asyncio
import uvicorn
import json

# 模拟的烹饪步骤数据库
RECIPES = {
    "番茄炒蛋": [
        "1. 准备2个番茄和3个鸡蛋",
        "2. 番茄切块，鸡蛋打散",
        "3. 热锅倒油，先炒鸡蛋至凝固",
        "4. 加入番茄翻炒至出汁",
        "5. 加盐调味，出锅"
    ],
    "红烧肉": [
        "1. 五花肉切块焯水",
        "2. 炒糖色至金黄色",
        "3. 加入肉块翻炒上色",
        "4. 加料酒、生抽、老抽、香料",
        "5. 小火炖煮40分钟",
        "6. 收汁装盘"
    ]
}

async def homepage(request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>烹饪助手</title></head>
    <body>
        <h1>实时烹饪助手</h1>
        <input id="dish" placeholder="输入菜名(如:番茄炒蛋)" />
        <button onclick="startCooking()">开始烹饪</button>
        <div id="steps"></div>
        <script>
            function startCooking() {
                const dish = document.getElementById('dish').value;
                const eventSource = new EventSource(`/cook?dish=${encodeURIComponent(dish)}`);
                eventSource.onmessage = function(e) {
                    document.getElementById('steps').innerHTML += `<p>${e.data}</p>`;
                };
            }
        </script>
    </body>
    </html>
    """)

async def cook(request):
    dish = request.query_params.get("dish", "")
    steps = RECIPES.get(dish, [f"抱歉，我不会做{dish}"])

    async def generate_steps():
        for step in steps:
            yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
            await asyncio.sleep(2)  # 模拟处理延迟
        yield "data: [END]\n\n"  # 结束标记

    return StreamingResponse(
        generate_steps(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )

app = Starlette(debug=True, routes=[
    Route("/", homepage),
    Route("/cook", cook),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)