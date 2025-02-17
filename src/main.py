from fastapi import FastAPI
from src.services.cache_service import CacheManager
import gc

app = FastAPI()

@app.on_event("startup")
async def startup():
    # Initialize different caches for different purposes
    CacheManager.init_cache("db_cache", max_size=1000)
    CacheManager.init_cache("file_cache", max_size=1000)
    CacheManager.init_cache("differences_cache", max_size=500)

@app.on_event("shutdown")
async def shutdown():
    CacheManager.clear_all() 