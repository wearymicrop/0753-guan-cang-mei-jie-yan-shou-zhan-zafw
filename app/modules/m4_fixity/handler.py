from fastapi import APIRouter

from app.pipeline import preview

router = APIRouter(prefix="/api/fixity")


@router.get("/{sample}")
def inspect(sample: str):
    return preview(sample, "fixity")
