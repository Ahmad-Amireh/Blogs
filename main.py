from fastapi import FastAPI, status, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse

app =  FastAPI()

posts: list[dict] = [{
    "id": 1, 
    "author": "ahmad", 
    "title": "TFT Game",
    "content": "it's a nice game!!",
    "date_posted": "February 27, 2026" 
},
{
    "id":2, 
    "author": "yazan",
    "title": "League of Legends", 
    "content": "I love this game, it makes me feel awesome!",
    "date_posted": "February 28, 2026"
}]


@app.get('/')
def home (): 
    return {"message": "Hello World"}

@app.get("/api/posts") 
def get_posts (): 
    return posts

@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    for post in posts : 
        if post.get("id") == post_id:
            return post
    raise HTTPException (status_code= status.HTTP_404_NOT_FOUND, detail="Post not found")

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occured. Please check your request and try again"
    )

    return JSONResponse(
        status_code= exception.status_code,
        content= {"detail": message}
    )
