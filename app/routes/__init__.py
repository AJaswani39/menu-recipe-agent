from fastapi import FastAPI

from app.routes import agent, core, history, menu, uploads


def register_routes(api: FastAPI, *, production: bool) -> None:
    core.register(api, production=production)
    menu.register(api)
    agent.register(api)
    uploads.register(api)
    history.register(api)
