from database import Base
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy.orm import registry
from sqlalchemy.orm import relationship

mapper_registry = registry()
digimon_attribute = Table(
    "digimon_attribute",
    Base.metadata,
    Column("id_digimon", ForeignKey("digimon.id"), primary_key=True),
    Column("id_attribute", ForeignKey("attribute.id"), primary_key=True),
)

digimon_field = Table(
    "digimon_field",
    Base.metadata,
    Column("id_digimon", ForeignKey("digimon.id"), primary_key=True),
    Column("id_field", ForeignKey("field.id"), primary_key=True),
)

digimon_type = Table(
    "digimon_type",
    Base.metadata,
    Column("id_digimon", ForeignKey("digimon.id"), primary_key=True),
    Column("id_type", ForeignKey("type.id"), primary_key=True),
)

digimon_skill = Table(
    "digimon_skill",
    Base.metadata,
    Column("id_digimon", ForeignKey("digimon.id"), primary_key=True),
    Column("id_skill", ForeignKey("skill.id"), primary_key=True),
)

digimon_level = Table(
    "digimon_level",
    Base.metadata,
    Column("id_digimon", ForeignKey("digimon.id"), primary_key=True),
    Column("id_level", ForeignKey("level.id"), primary_key=True),
)


# digivolution = Table(
#     "digivolution",
#     Base.metadata,
#     Column("id_digimon_prior", ForeignKey("digimon.id"), primary_key=True),
#     Column("id_digimon_next", ForeignKey("digimon.id"), primary_key=True),
#     Column("description", String)
# )


class Field(Base):
    __tablename__ = "field"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Level(Base):
    __tablename__ = "level"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Type(Base):
    __tablename__ = "type"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Attribute(Base):
    __tablename__ = "attribute"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Skill(Base):
    __tablename__ = "skill"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)


class DigimonDescription(Base):
    __tablename__ = "digimon_description"

    id = Column(Integer, primary_key=True)
    id_digimon = Column(Integer, ForeignKey("digimon.id"))
    origin = Column(String)
    language = Column(String)
    description = Column(String)


class SimpleDigimon(Base):
    __tablename__ = "digimon"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    xantibody = Column(Boolean)
    release_date = Column(String)


class Digivolution(Base):
    __tablename__ = "digivolution"

    id_digimon_prior = Column(String, ForeignKey("digimon.id"), primary_key=True)
    id_digimon_next = Column(String, ForeignKey("digimon.id"), primary_key=True)
    digimon_prior = relationship("SimpleDigimon", foreign_keys=[id_digimon_prior])
    digimon_next = relationship("SimpleDigimon", foreign_keys=[id_digimon_next])
    condition = Column(String)


class Digimon(SimpleDigimon):
    __tablename__ = "digimon"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True)
    name = Column(String)
    xantibody = Column(Boolean)
    release_date = Column(String)
    levels = relationship("Level", secondary=digimon_level)
    skills = relationship("Skill", secondary=digimon_skill)
    attributes = relationship("Attribute", secondary=digimon_attribute)
    fields = relationship("Field", secondary=digimon_field)
    types = relationship("Type", secondary=digimon_type)
    descriptions = relationship("DigimonDescription")
    digivolved_from = relationship(
        "Digivolution",
        primaryjoin=(Digivolution.id_digimon_next == id),
        overlaps="digimon_next",
    )
    digivolve_to = relationship(
        "Digivolution",
        primaryjoin=(Digivolution.id_digimon_prior == id),
        overlaps="digimon_prior",
    )
