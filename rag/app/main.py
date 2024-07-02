from fastapi import FastAPI,APIRouter

from rag.app import book,laws,manual,naive,one,paper,presentation

import uvicorn


# Create FastAPI app
app = FastAPI()

api_router = APIRouter()
api_router.include_router(book.router, tags=["book_chunk"])
api_router.include_router(laws.router, tags=["laws_chunk"])
api_router.include_router(manual.router, tags=["manual_chunk"])
api_router.include_router(naive.router, tags=["naive_chunk"])
api_router.include_router(one.router, tags=["one_chunk"])
api_router.include_router(paper.router, tags=["paper_chunk"])
api_router.include_router(presentation.router, tags=["presentation_chunk"])

# Include your API router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)