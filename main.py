from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.agencies import router as agencies_router
from src.api.v1.openlaws import router as openlaws_router
from src.services.cache_service import CacheManager
import gc

app = FastAPI(
    title="Iowa Regulatory Code API",
    description="API for accessing Iowa Regulatory Code data",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    agencies_router,
    prefix="/api/v1/agencies",
    tags=["agencies"]
)

app.include_router(
    openlaws_router,
    prefix="/api/v1/openlaws",
    tags=["openlaws"]
)

@app.on_event("startup")
async def startup():
    # Initialize different caches for different purposes
    CacheManager.init_cache("db_cache", max_size=1000)
    CacheManager.init_cache("file_cache", max_size=1000)
    CacheManager.init_cache("differences_cache", max_size=500)

@app.on_event("shutdown")
async def shutdown():
    CacheManager.clear_all()
    gc.collect()

@app.get("/")
async def root():
    """Root endpoint that returns API information"""
    return {
        "message": "Welcome to the Iowa Regulatory Code API",
        "version": "1.0.0",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)