import os
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from .api import router
from .settings import settings

# Fix for SSL: Unset variables pointing to missing certificate files
# so that libraries like curl_cffi fall back to system defaults.
for var in ["CURL_CA_BUNDLE", "REQUESTS_CA_BUNDLE"]:
    if var in os.environ and not os.path.exists(os.environ[var]):
        os.environ.pop(var)

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

Instrumentator().instrument(app).expose(app)

@app.get("/health")
def health():
    return {"status": "ok"}

