from typing import Union

import models
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload


def get_digimons(
    page_size: int,
    page: int,
    xantibody: Union[bool, None],
    name_contains: Union[str, None],
    id_type: Union[int, None],
    id_field: Union[int, None],
    id_level: Union[int, None],
    id_attribute: Union[int, None],
    digivolved_from: Union[int, None],
    digivolve_to: Union[int, None],
    db: Session,
):
    query = db.query(models.SimpleDigimon)
    if xantibody is not None:
        query = query.where(models.Digimon.xantibody == xantibody)
    if id_type is not None:
        query = query.filter(models.Digimon.types.any(models.Type.id.__eq__(id_type)))
    if id_field is not None:
        query = query.filter(
            models.Digimon.fields.any(models.Field.id.__eq__(id_field))
        )
    if id_level is not None:
        query = query.filter(
            models.Digimon.levels.any(models.Level.id.__eq__(id_level))
        )
    if id_attribute is not None:
        query = query.filter(
            models.Digimon.attributes.any(models.Attribute.id.__eq__(id_attribute))
        )
    if name_contains:
        query = query.filter(models.Digimon.name.like(f"%{name_contains}%"))

    if digivolved_from is not None:
        query = query.filter(
            models.Digimon.digivolve_to.any(
                models.Digivolution.id_digimon_prior.__eq__(digivolved_from)
            )
        )
    if digivolve_to is not None:
        query = query.filter(
            models.Digimon.digivolved_from.any(
                models.Digivolution.id_digimon_next.__eq__(digivolve_to)
            )
        )

    return query.limit(page_size).offset((page - 1) * page_size).all()


def count_digimons(db: Session):
    return db.query(models.SimpleDigimon).count()


def get_digimon_by_name(digimon_name: str, db: Session):
    return (
        db.query(models.Digimon)
        .options(joinedload(models.Digimon.levels))
        .options(joinedload(models.Digimon.fields))
        .options(joinedload(models.Digimon.attributes))
        .options(joinedload(models.Digimon.skills))
        .options(joinedload(models.Digimon.types))
        .options(joinedload(models.Digimon.descriptions))
        .options(joinedload(models.Digimon.digivolved_from))
        .options(joinedload(models.Digimon.digivolve_to))
        .filter(models.Digimon.name.like(digimon_name))
        .one()
    )


def get_digimon_by_id(digimon_id: int, db: Session):
    return (
        db.query(models.Digimon)
        .options(joinedload(models.Digimon.levels))
        .options(joinedload(models.Digimon.fields))
        .options(joinedload(models.Digimon.attributes))
        .options(joinedload(models.Digimon.skills))
        .options(joinedload(models.Digimon.types))
        .options(joinedload(models.Digimon.descriptions))
        .options(joinedload(models.Digimon.digivolved_from))
        .options(joinedload(models.Digimon.digivolve_to))
        .filter(models.Digimon.id.__eq__(digimon_id))
        .one()
    )


def get_digivolution(db: Session, id_digimon):
    return (
        db.query(models.Digimon)
        .join(models.Digimon.digivolve_to)
        .where(models.Digivolution.id_digimon_prior == id_digimon)
        .all()
    )


def get_fields(page_size: int, page: int, db: Session):
    query = db.query(models.Field)
    return query.limit(page_size).offset((page - 1) * page_size).all(), query.count()


def get_levels(page_size: int, page: int, db: Session):
    query = db.query(models.Level)
    return query.limit(page_size).offset((page - 1) * page_size).all(), query.count()


def get_attributes(page_size: int, page: int, db: Session):
    query = db.query(models.Attribute)
    return query.limit(page_size).offset((page - 1) * page_size).all(), query.count()


def get_types(page_size: int, page: int, db: Session):
    query = db.query(models.Type)
    return query.limit(page_size).offset((page - 1) * page_size).all(), query.count()


def get_skills(
    page_size: int,
    page: int,
    description_contains: Union[str, None],
    name_contains: Union[str, None],
    db: Session,
):
    query = db.query(models.Skill)
    if name_contains:
        query = query.filter(models.Skill.name.like(f"%{name_contains}%"))
    if description_contains:
        query = query.filter(models.Skill.description.like(f"%{description_contains}%"))
    return query.limit(page_size).offset((page - 1) * page_size).all(), query.count()
