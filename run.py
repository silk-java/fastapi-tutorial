#!/usr/bin/python3
# -*- coding:utf-8 -*-
# __author__ = '__Jack__'

import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

import tutorial.chapter03
from coronavirus import application
from tutorial import app03, app04, app05, app06, app07, app08

from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse,JSONResponse
# from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(
    title='FastAPI Tutorial and Coronavirus Tracker API Docs',
    description='FastAPI教程 新冠病毒疫情跟踪器API接口文档，项目代码：https://github.com/liaogx/fastapi-tutorial',
    version='1.0.0',
    docs_url=None,
    redoc_url=None,
)

# mount表示将某个目录下一个完全独立的应用挂载过来，这个不会在API交互文档中显示
# app.mount(path='/static', app=StaticFiles(directory='./coronavirus/static'), name='static')  # .mount()不要在分路由APIRouter().mount()调用，模板会报错

# ========设置docs文档为本地文件=========
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
# ========设置docs文档为本地文件=========

# @app.exception_handler(StarletteHTTPException)  # 重写HTTPException异常处理器
# async def http_exception_handler(request, exc):
#     """
#     :param request: 这个参数不能省
#     :param exc:
#     :return:
#     """
#     return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
#
#


@app.exception_handler(RequestValidationError)  # 重写请求验证异常处理器
async def validation_exception_handler(request, exc):

    """
    :param request: 这个参数不能省
    :param exc:
    :return:
    """
    errors = []
    for error in exc.errors():
        print(error)
        print(type(error))
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    # raise HTTPException(status_code=422, detail=errors)
    return JSONResponse({"code":402,"msg":errors[0]['msg'],"errors":errors})

    # return PlainTextResponse(str(errors), status_code=400)


# @app.middleware('http')
# async def add_process_time_header(request: Request, call_next):  # call_next将接收request请求做为参数
#     start_time = time.time()
#     response = await call_next(request)
#     process_time = time.time() - start_time
#     response.headers['X-Process-Time'] = str(process_time)  # 添加自定义的以“X-”开头的请求头
#     return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app03, prefix='/chapter03', tags=['第三章 请求参数和验证'])
app.include_router(app04, prefix='/chapter04', tags=['第四章 响应处理和FastAPI配置'])
app.include_router(app05, prefix='/chapter05', tags=['第五章 FastAPI的依赖注入系统'])
app.include_router(app06, prefix='/chapter06', tags=['第六章 安全、认证和授权'])
app.include_router(app07, prefix='/chapter07', tags=['第七章 FastAPI的数据库操作和多应用的目录结构设计'])
app.include_router(app08, prefix='/chapter08', tags=['第八章 中间件、CORS、后台任务、测试用例'])
app.include_router(application, prefix='/coronavirus', tags=['新冠病毒疫情跟踪器API'])

if __name__ == '__main__':
    uvicorn.run('run:app', host='0.0.0.0', port=8000, reload=True, debug=True, workers=1)
