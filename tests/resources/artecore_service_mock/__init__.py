from fastapi import APIRouter

router = APIRouter(prefix="/mock", tags=["mock"])


@router.get("/hello")
def hello():
    return {"message": "Hello from Mock Service"}
