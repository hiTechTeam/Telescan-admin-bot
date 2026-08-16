from aiohttp import web


async def start_health_server(host: str, port: int) -> web.AppRunner:
    async def liveness(_: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    application = web.Application()
    application.router.add_get("/health/live", liveness)
    runner = web.AppRunner(application, access_log=None)
    await runner.setup()
    await web.TCPSite(runner, host, port).start()
    return runner
