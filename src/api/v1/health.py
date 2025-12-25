from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/", summary="Health Check", description="Check if the API is running properly")
async def health_check():
    """Health check endpoint to verify the API is running properly.
    
    Returns:
        dict: A dictionary with the status of the API
    """
    return {"status": "healthy", "version": "1.0.0"}
