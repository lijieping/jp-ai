from pydantic import BaseModel

class KbSpaceIn(BaseModel):
    name : str
    desc : str
    collection : str

class KbSpaceOut(KbSpaceIn):
    id :int