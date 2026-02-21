# this is an example file, main.py is the actual API entryway

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# head to http://localhost:8000/docs to test the API (no Postman needed)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# example GET endpoint
@app.get("/helloworld")
def get_helloworld():
    return {"data": "Hello world!"}


class WelcomeNameBody(BaseModel):
    name: str


# endpoints that take a request body cannot be GET methods
@app.post("/welcomename")
def post_welcomename(body: WelcomeNameBody):
    return {"data": "Welcome " + body.name + "!"}


# endpoints are best declared in main.py, but try to organize
# helper functions into separate files/modules for readability
