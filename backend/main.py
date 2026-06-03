from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import routes_calibrate, routes_export, routes_extract, routes_project
from storage.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="SciPlot Extractor API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_project.router)
app.include_router(routes_extract.router)
app.include_router(routes_calibrate.router)
app.include_router(routes_export.router)


@app.get("/health")
def health():
    return {"status": "ok"}
