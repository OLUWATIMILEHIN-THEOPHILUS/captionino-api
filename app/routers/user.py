from fastapi import APIRouter, status

router = APIRouter(
    prefix="/user",
    tags=["User"]
)


@router.post("/create_user", status_code=status.HTTP_201_CREATED)
def create_user():
    return ({"User created successfully!"})


@router.delete("/delete_user", status_code=status.HTTP_404_NOT_FOUND)
def delete_user():
    return ({"User deleted successfully!"})