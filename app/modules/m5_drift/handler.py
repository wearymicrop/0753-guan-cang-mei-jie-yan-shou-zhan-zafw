from fastapi import APIRouter

from app.pipeline import preview

router = APIRouter(prefix="/api/drift")


@router.get("/{sample}")
def inspect(sample: str):
    return preview(sample, "drift")
