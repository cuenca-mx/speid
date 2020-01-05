from typing import Union

from speid.models.helpers import mongo_to_dict


class BaseModel:
    def to_dict(self) -> Union[dict, None]:
        return mongo_to_dict(self, [])

    def __repr__(self):
        return str(self.to_dict())
