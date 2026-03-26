from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import upload, csv_analysis, merge, image_linking, text_enhancement, review, catalog

app = FastAPI(
    title="Katalog API",
    description="Backend für Produktkatalog-Generierung",
    version="0.7.0"  # Phase 7: Professional HTML Catalog Output
)

# CORS für Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(csv_analysis.router, prefix="/api", tags=["analysis"])
app.include_router(merge.router, prefix="/api", tags=["merge"])
app.include_router(image_linking.router, tags=["images"])
app.include_router(text_enhancement.router, tags=["texts"])
app.include_router(review.router, tags=["review"])
app.include_router(catalog.router, tags=["catalog"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "katalog-api"}
