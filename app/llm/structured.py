import json

from pydantic import BaseModel, ValidationError

from app.llm.exceptions import LLMProviderError
from app.llm.schemas import LLMResponseFormat


def _make_strict_schema(schema: dict) -> dict:
    schema = schema.copy()

    schema.pop("minItems", None)
    schema.pop("maxItems", None)
    schema.pop("minLength", None)
    schema.pop("maxLength", None)

    if schema.get("type") == "object":
        schema["additionalProperties"] = False
        schema["properties"] = {
            name: _make_strict_schema(property_schema)
            for name, property_schema in schema.get("properties", {}).items()
        }

    if "items" in schema:
        schema["items"] = _make_strict_schema(schema["items"])

    if "$defs" in schema:
        schema["$defs"] = {
            name: _make_strict_schema(definition)
            for name, definition in schema["$defs"].items()
        }

    return schema




def build_json_schema_response_format(
    schema: type[BaseModel],
) -> LLMResponseFormat:
    json_schema = schema.model_json_schema()
    json_schema = _make_strict_schema(json_schema)

    return LLMResponseFormat(
        type="json_schema",
        json_schema={
            "name": schema.__name__,
            "schema": json_schema,
            "strict": True,
        },
    )


def parse_structured_response(
    content: str,
    schema: type[BaseModel],
) -> BaseModel:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise LLMProviderError(
            "LLM returned invalid JSON."
        ) from e

    try:
        return schema.model_validate(data)
    except ValidationError as e:
        raise LLMProviderError(
            "LLM returned data that does not match the expected schema."
        ) from e