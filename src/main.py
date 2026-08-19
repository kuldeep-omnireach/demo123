from fastapi import FastAPI

app = FastAPI()


@app.get("/hello", status_code=200)
def handle_hello():
    return {"msg": "Hello World"}


@app.get("/healthcheck", status_code=200)
def handle_healthcheck():
    return {}
