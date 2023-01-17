from typing import List, Union

import utils
from pydantic import BaseModel
from pydantic import validator


class Pagination(BaseModel):
    next_page: str
    previous_page: str
    page_size: int
    total_page: int


class DigimonBase(BaseModel):
    id: int
    name: str
    xantibody: bool
    release_date: str
    href: str = None
    image_href: str = None

    @validator("href", always=True)
    def create_href(cls, v, values, **kwargs):
        return f"digimon/{values['id']}"

    @validator("image_href", always=True)
    def create_presign_rul(cls, v, values, **kwargs):
        return utils.create_presigned_url(digimon_name=values["name"], thumbnail=True)

    class Config:
        orm_mode = True


class LevelBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class FieldBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class AttributeBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class SkillBase(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        orm_mode = True


class TypeBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class Digivolution(BaseModel):
    name: str
    condition: str

    class Config:
        orm_mode = True


class Description(BaseModel):
    origin: str
    language: str
    description: str

    class Config:
        orm_mode = True


class DigimonSchema(DigimonBase):
    levels: List[LevelBase]
    fields: List[FieldBase]
    attributes: List[AttributeBase]
    descriptions: List[Description]
    types: List[TypeBase]
    skills: List[SkillBase]
    digivolved_from: List[Digivolution]
    digivolve_to: List[Digivolution]

    @validator("image_href", always=True)
    def create_presign_url(cls, v, values, **kwargs):
        return utils.create_presigned_url(digimon_name=values["name"], thumbnail=False)

    class Config:
        orm_mode = True


class Page(BaseModel):
    content: List[
        Union[DigimonBase, SkillBase, LevelBase, FieldBase, AttributeBase, BaseModel]
    ]
    pagination: Pagination
