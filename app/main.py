from fastapi import FastAPI, status
from .routers import auth, user

app = FastAPI()


app.include_router(auth.router)
app.include_router(user.router)


@app.get("/home", status_code=status.HTTP_200_OK)
def home_page():
    return ({"Welcome to Captionino by Timi"})
