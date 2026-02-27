from fastapi import FastAPI


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
    return {"message": "Post not found"}