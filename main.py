from fastapi import FastAPI, status, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from schemas import PostResponse, PostCreate


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


@app.get('/', include_in_schema= False)
def home (): 
    return {"message": "Hello World"}

@app.get("/api/posts", response_model= list[PostResponse]) 
def get_posts (): 
    return posts

@app.post("/api/posts", status_code=status.HTTP_201_CREATED, response_model=PostResponse)

def create_post(post: PostCreate):
    new_id = max(p["id"] for p in posts) + 1 if posts else 1
    new_post = {
        "id": new_id,
        "author": post.author,
        "title": post.title,
        "content": post.content,
        "date_posted": "April 23, 2025"
    }
    posts.append(new_post)
    return new_post

@app.get("/api/posts/{post_id}", response_model=PostResponse)
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

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Invalid input. Check your path parameters or request body."}
    )
