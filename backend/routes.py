from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import json

router = APIRouter()
RULES_PATH = Path(__file__).parent / "ngc" / "rules.json"

@router.get("/rules")
def get_rules():
    if not RULES_PATH.exists():
        raise HTTPException(status_code=404, detail=f"rules.json introuvable: {RULES_PATH}")

    try:
        # utf-8-sig handles both plain UTF-8 and UTF-8 with BOM.
        with RULES_PATH.open("r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
