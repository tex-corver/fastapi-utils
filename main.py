from fastapi import FastAPI
from fastapi_utils.prometheus_instrument import PrometheusInstrumentator


app = FastAPI()

instrumentator = PrometheusInstrumentator()
instrumentator.instrument(app).expose(app)


@app.get("/")
async def main():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
