# App entry point here.
from fastapi import FastAPI, status, Depends
from .routers import auth, user
from starlette.middleware.sessions import SessionMiddleware
from .config import settings
from .oauth2 import get_current_supabase_user
from fastapi.middleware.cors import CORSMiddleware

# models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)    #for google auth 

origins = ["http://192.168.100.34:3000", "http://localhost:3000", "https://captionino-frontend.pages.dev"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth.router)
app.include_router(user.router)

@app.get("/home", status_code=status.HTTP_200_OK)
def home_page(current_user: dict = Depends(get_current_supabase_user)):
    return ({"Welcome to Captionino by Timi"})
