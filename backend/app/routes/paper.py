import logging
from fastapi import APIRouter, HTTPException
from bson import ObjectId

from app.database import final_question_paper_collection, question_blueprint_collection
from app.models.schemas import AssemblePaperRequest
from app.services.paper_assembler import assemble_paper, format_paper_out

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/assemble")
async def assemble_final_paper(body: AssemblePaperRequest):
    """Assemble a final question paper from approved questions."""
    try:
        paper = await assemble_paper(body.blueprint_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Paper assembly failed: {e}")
        raise HTTPException(500, f"Paper assembly failed: {str(e)}")

    return format_paper_out(paper)


@router.get("/{paper_id}")
async def get_paper(paper_id: str):
    """Get a final question paper by ID."""
    try:
        doc = await final_question_paper_collection.find_one({"_id": ObjectId(paper_id)})
    except Exception:
        raise HTTPException(400, "Invalid paper ID")

    if not doc:
        raise HTTPException(404, "Question paper not found")

    return format_paper_out(doc)


@router.get("/by-blueprint/{blueprint_id}")
async def list_papers_by_blueprint(blueprint_id: str):
    """List all assembled papers for a blueprint."""
    try:
        cursor = final_question_paper_collection.find({"blueprint_id": blueprint_id})
        docs = await cursor.to_list(length=20)
    except Exception as e:
        logger.error(f"Failed to list papers: {e}")
        raise HTTPException(500, "Failed to list papers")

    return [format_paper_out(d) for d in docs]
