from __future__ import annotations
from routes.router import router, database
import logging
from fastapi.responses import JSONResponse
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException

logging.basicConfig(filename='app.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

logging.info('API is starting up')

app = FastAPI(
    title='Yet Another YDisk Api',
    version='1.0',
)


@app.exception_handler(RequestValidationError)
async def custom_request_validation_exception_handler(request, exc):
    logging.info(f"ERROR {400} {request.url} - {request.method} - {exc}")
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": "Validation Failed"},
    )


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    logging.info(f"ERROR {exc.status_code} {request.url} - {request.method} - {exc}")
    code = exc.status_code
    return JSONResponse(
        status_code=code,
        content={"code": code, "message": exc.detail},
    )


@app.on_event("startup")
async def startup_database():
    await database.connect()


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()

app.include_router(router)
