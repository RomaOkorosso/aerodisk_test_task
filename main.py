import datetime

from fastapi import FastAPI, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from urllib.parse import quote
import os

from app.src import auth_router
from app.src.auth.service import auth_service
from app.src.base.exceptions import Unauthorized
from app.src.disk_manager import disk_manager_router
from app.src.base import get_session
from logger import logger
from app.src import disk_manager_init_db

app = FastAPI()
templates = Jinja2Templates(directory="templates")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(disk_manager_router.router)


@app.exception_handler(Unauthorized)
async def unauthorized_exception_handler(request, exc):
    logger.log("Unauthorized request")
    return RedirectResponse(url="/auth/login" + "?next=" + quote(request.url.path))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.log(f"ErrorL {exc}")
    return PlainTextResponse(str(exc), status_code=400)


# add action on app startup
@app.on_event("startup")
async def init_disks_in_db():
    # create if no /logs and create today log file
    if not os.path.exists("logs"):
        os.mkdir("logs")
    if not os.path.exists(f"logs/{datetime.datetime.now().date()}.log"):
        with open(f"logs/{datetime.datetime.now().date()}.log", "w") as f:
            f.write(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Log file created for {datetime.datetime.now().date()}\n"
            )

    await disk_manager_init_db.init_disks_in_db()

    logger.log("On app startup action completed")

    return


async def get_context(request: Request, session: AsyncSession = Depends(get_session)):
    token_cooke = request.cookies.get("access_token")
    access_token = await auth_service.get_access_token_from_cookie(token_cooke)
    print("access", access_token)
    if access_token:
        username = await auth_service.get_username_from_token(
            session=session, access_token=access_token
        )
    else:
        username = None

    logger.log(f"Context (main.py): {request} {access_token} {username}")

    return {"request": request, "access_token": access_token, "username": username}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, context: dict = Depends(get_context)):
    logger.log(f"Home (GET): {request} {context}")
    return templates.TemplateResponse("home.html", context)


@app.post("/", response_class=HTMLResponse)
async def home_post(request: Request, context: dict = Depends(get_context)):
    logger.log(f"Home (POST): {request} {context}")
    return templates.TemplateResponse("home.html", context)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
