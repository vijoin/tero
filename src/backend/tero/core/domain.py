from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import SQLModel


class CamelCaseModel(SQLModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel) # type: ignore # sqlmodel defines model_config as SQLModelConfig but when used the attributes setting give type errors
