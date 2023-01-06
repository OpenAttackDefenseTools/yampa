import secrets
import string

from fastapi import FastAPI

app = FastAPI()


def gen_flag():
    return f"TESTFLAG_{''.join([secrets.choice(string.ascii_uppercase) for _ in range(20)])}"


@app.get("/")
async def hello():
    return {"hello": "world"}


@app.get("/legitimate")
async def legitimate():
    return {"flag": gen_flag()}


@app.get("/exploit/AAAAAAAAAAAAAAAAAAAAAAA")
async def exploit():
    return {"flag": gen_flag()}

@app.get("/genericwebsite/login")
async def genericwebsite_login():
    return {"loggedin": True}

@app.get("/genericwebsite/flagstore")
async def genericwebsite_flagstore():
    return {"flag": gen_flag()}
