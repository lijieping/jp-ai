from pydantic import BaseModel

class LoginReq(BaseModel):
    username: str
    password: str

class UserInfo(BaseModel):
    userId:int
    username: str

class LoginResp(BaseModel):
    token: str
    userInfo: UserInfo

