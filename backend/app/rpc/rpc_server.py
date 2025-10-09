from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
from app.core.auth.session_manager import get_current_user
from app.db import models as m
from app.rpc.registry import rpc_registry

from app.core.auth.guards import disallow_roles

router = APIRouter(prefix="/rpc", tags=["rpc"], dependencies=[Depends(disallow_roles("cliente"))])

class RpcRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = None

@router.post("/")
async def rpc_endpoint(req: RpcRequest, user: m.User = Depends(get_current_user)):
    try:
        result = await rpc_registry.call(req.method, req.params)
        return {"ok": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="RPC error") from e
