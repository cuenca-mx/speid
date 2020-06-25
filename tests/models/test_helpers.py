from datetime import datetime

from mongoengine import (
    BooleanField,
    ComplexDateTimeField,
    DateTimeField,
    DecimalField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    StringField,
)

from speid.models.base import BaseModel


def test_doc_to_dict():
    """
    Este test es temporal lo copié del PR original, cuando se haya mezclado:
      - https://github.com/MongoEngine/mongoengine/pull/2349
      - https://github.com/MongoEngine/mongoengine/pull/2348
    Estos helpers ya no serán necesarios
    """

    class Character(EmbeddedDocument):
        name = StringField()
        age = IntField()
        appears = ListField()

        meta = {"allow_inheritance": False}

    class DataSheet(EmbeddedDocument):
        year = StringField()
        author = StringField()
        rank = DecimalField()

        meta = {"allow_inheritance": False}

    class Series(Document, BaseModel):
        title = StringField()
        number_of_chapters = IntField()
        active = BooleanField()
        rating = FloatField()
        info = EmbeddedDocumentField(DataSheet)
        characters = ListField()
        secret_code = StringField()
        extras = StringField()
        additional_info = DictField()
        created_at = DateTimeField(default=datetime.now)
        updated_at = ComplexDateTimeField(default=datetime.now)

    serie = Series(
        title="Some Random Series",
        number_of_chapters=12,
        active=True,
        rating=4.8,
        characters=[
            Character(
                name="Emma",
                age=11,
                appears=["chapter 1", "chapter 2", "chapter 3"],
            ),
            Character(
                name="Ray",
                age=12,
                appears=["chapter 1", "chapter 2", "chapter 3"],
            ),
            Character(
                name="Norman",
                age=11,
                appears=["chapter 1", "chapter 2", "chapter 3"],
            ),
        ],
        info=DataSheet(year="2019", author="Kaiu", rank=4.4),
        secret_code="super_secret_code",
        additional_info={"data": "he63oc48r5jv"},
    )

    serie.save()

    res = serie.to_dict(exclude_fields=["secret_code"])

    assert type(res["title"]) is str
    assert type(res["number_of_chapters"]) is int
    assert type(res["active"]) is bool
    assert type(res["characters"]) is list
    assert type(res["characters"][0]) is dict
    assert type(res["characters"][0]["name"]) is str
    assert type(res["characters"][0]["age"]) is int
    assert type(res["characters"][0]["appears"]) is list
    assert type(res["info"]) is dict
    assert type(res["info"]["author"]) is str
    assert "secret_code" not in res
    assert type(res["additional_info"]) is dict
    assert type(res["created_at"]) is str
    assert type(res["updated_at"]) is str
