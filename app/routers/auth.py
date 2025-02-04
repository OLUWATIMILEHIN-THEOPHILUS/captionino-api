from fastapi import APIRouter, status

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.post("/signin", status_code=status.HTTP_200_OK)
def signin():
    return ({"User signed in successfully!"})
