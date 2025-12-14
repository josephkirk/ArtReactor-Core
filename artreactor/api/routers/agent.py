from fastapi import APIRouter, Depends

from artreactor.api.dependencies import get_agent_manager
from artreactor.core.managers.agent_manager import AgentManager
from artreactor.models.api import ChatRequest, ChatResponse

# We need a way to get the global agent manager.
# For now, we'll instantiate one or get it from main if we updated main.
# Let's update main.py to expose get_agent_manager first.
# But I can't update main.py easily here without circular imports if main imports this router.
# So I'll define a dependency here that imports from main inside the function or use a singleton.

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, am: AgentManager = Depends(get_agent_manager)):
    response = await am.run_agent(request.prompt, request.context)
    return ChatResponse(response=response)
