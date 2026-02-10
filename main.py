from __future__ import annotations
import asyncio
import sys
from src.core import create_app, change_scene, main_loop
from src.scenes.menu import MenuScene

async def main():
    app = create_app()
    change_scene(app, MenuScene(app))
    await main_loop(app)

if __name__ == "__main__":
    # Platform detection for pygbag compatibility
    if sys.platform == "emscripten":
        # Running in browser via pygbag
        asyncio.run(main())
    else:
        # Running locally with Python
        asyncio.run(main())
