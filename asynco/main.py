from contextlib import  asynccontextmanager # new
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler #new
from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from .database import Base, engine
from routers import posts, users



@asynccontextmanager
async def lifespan(_app= FastAPI):
    #start up 
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app =  FastAPI(lifespan= lifespan)

@app.get('/', include_in_schema= False)
def home (): 
    return {"message": "Hello World"}

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    return await http_exception_handler(request, exception)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    return await request_validation_exception_handler(request, exception)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("asynco.main:app", host="127.0.0.1", port=8000, reload=True)