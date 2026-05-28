from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="自然语言查询问题",
        json_schema_extra={"examples": ["各分行存款余额是多少？"]},
    )
