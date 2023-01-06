import logging
from typing import Union

import crud
import schemas
import utils
import uvicorn
from database import SessionLocal
from fastapi import Depends
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from sqlalchemy.orm import Session


description = """
DigidexApi is a simple side project about Digimons. It's a serverless application
backed by AWS lambda and an API gateway. It use fastApi and Mangum for simplicity.

So basically you can get data about Digimons. I'm not a Digimons expert and I just
get data from the Digimon wikia. So some data can be missing or outdated.
"""

app = FastAPI(
    title="DigidexApi",
    description=description,
    version="0.0.1",
    contact={
        "name": "Rémi Pépin",
        "url": "https://www.linkedin.com/in/remi-pepin/",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/digimon", response_model=schemas.Page,
description="""Return all the Digimon of the application

""")
def get_all_digimons(
    page_size: int = 10,
    page: int = 1,
    xantibody: Union[bool, None] = None,
    name_contains: Union[str, None] = None,
    id_type: Union[int, None] = None,
    id_field: Union[int, None] = None,
    id_level: Union[int, None] = None,
    id_attribute: Union[int, None] = None,
    digivolved_from: Union[int, None] = None,
    digivolve_to: Union[int, None] = None,
    db: Session = Depends(get_db),
):
    digimons = crud.get_digimons(
        page_size=page_size,
        page=page,
        xantibody=xantibody,
        name_contains=name_contains,
        id_type=id_type,
        id_field=id_field,
        id_level=id_level,
        id_attribute=id_attribute,
        digivolved_from=digivolved_from,
        digivolve_to=digivolve_to,
        db=db,
    )

    path = "/digimon?"
    count_digimons = crud.count_digimons(db=db)
    pagination = utils.paginaton(
        path,
        count_digimons,
        page,
        page_size,
        len(digimons),
        xantibody=xantibody,
        id_field=id_field,
        id_level=id_level,
        id_type=id_type,
        name_contains=name_contains,
        id_attribute=id_attribute,
        digivolved_from=digivolved_from,
        digivolve_to=digivolve_to,
    )

    return schemas.Page(content=digimons, pagination=pagination)


@app.get("/digimon/{id_or_name}", response_model=schemas.DigimonSchema)
def get_digmon_by_name_or_id(
    id_or_name: Union[int, str], db: Session = Depends(get_db)
):
    if isinstance(id_or_name, int):
        digimon = crud.get_digimon_by_id(id_or_name, db)
    else:
        digimon = crud.get_digimon_by_name(id_or_name, db)

    digivolutions = []
    for digivolution in digimon.digivolve_to:
        digivolutions.append(
            schemas.Digivolution(
                name=digivolution.digimon_next.name, condition=digivolution.condition
            )
        )
    pre_digivolutions = []
    for pre_digivolution in digimon.digivolved_from:
        pre_digivolutions.append(
            schemas.Digivolution(
                name=pre_digivolution.digimon_prior.name,
                condition=pre_digivolution.condition,
            )
        )

    digimon_out = schemas.DigimonSchema(
        id=digimon.id,
        name=digimon.name,
        xantibody=digimon.xantibody,
        release_date=digimon.release_date,
        descriptions=digimon.descriptions,
        levels=digimon.levels,
        fields=digimon.fields,
        attributes=digimon.attributes,
        types=digimon.types,
        skills=digimon.skills,
        digivolved_from=pre_digivolutions,
        digivolve_to=digivolutions,
    )
    return digimon_out


@app.get("/level", response_model=schemas.Page)
def get_all_levels(page_size: int = 5, page: int = 1, db: Session = Depends(get_db)):
    levels, count_levels = crud.get_levels(page_size=page_size, page=page, db=db)

    path = "/level"
    pagination = utils.paginaton(path, count_levels, page, page_size, len(levels))
    return schemas.Page(content=levels, pagination=pagination)


@app.get("/attribute", response_model=schemas.Page)
def get_all_attributes(
    page_size: int = 5, page: int = 1, db: Session = Depends(get_db)
):
    attributes, count_attributes = crud.get_attributes(
        page_size=page_size, page=page, db=db
    )

    path = "/attribute"
    pagination = utils.paginaton(
        path, count_attributes, page, page_size, len(attributes)
    )
    return schemas.Page(content=attributes, pagination=pagination)


@app.get("/field", response_model=schemas.Page)
def get_all_fields(page_size: int = 5, page: int = 1, db: Session = Depends(get_db)):
    fields, count_fields = crud.get_fields(page_size=page_size, page=page, db=db)

    path = "/field"
    pagination = utils.paginaton(path, count_fields, page, page_size, len(fields))
    return schemas.Page(content=fields, pagination=pagination)


@app.get("/type", response_model=schemas.Page)
def get_all_types(page_size: int = 5, page: int = 1, db: Session = Depends(get_db)):
    types, count_types = crud.get_types(page_size=page_size, page=page, db=db)

    path = "/type"
    pagination = utils.paginaton(path, count_types, page, page_size, len(types))
    return schemas.Page(content=types, pagination=pagination)


@app.get("/skill", response_model=schemas.Page)
def get_all_skills(
    page_size: int = 10,
    page: int = 1,
    name_contains: Union[str, None] = None,
    description_contains: Union[str, None] = None,
    db: Session = Depends(get_db),
):
    skills, count_skills = crud.get_skills(
        page_size=page_size,
        page=page,
        name_contains=name_contains,
        description_contains=description_contains,
        db=db,
    )

    path = "/skill"
    pagination = utils.paginaton(path, count_skills, page, page_size, len(skills))
    return schemas.Page(content=skills, pagination=pagination)


handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
