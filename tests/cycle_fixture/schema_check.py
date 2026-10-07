"""Small JSON Schema checker for core/state.schema.json, so the fixture needs no extra packages.

It supports only the keywords that the state schema uses: type, enum, properties, required,
additionalProperties, patternProperties, propertyNames and local $ref.
"""

import re

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "null": type(None),
}


def _is_type(value, name):
    if name in ("integer", "number"):
        if isinstance(value, bool):
            return False
        return isinstance(value, int) if name == "integer" else isinstance(value, (int, float))
    return isinstance(value, _TYPES[name])


def schema_errors(instance, schema):
    """Return a list of error strings. An empty list means the instance is valid."""
    errors = []
    _check(instance, schema, schema, "$", errors)
    return errors


def _check(value, schema, root, path, errors):
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported $ref {ref}")
        target = root
        for part in ref[2:].split("/"):
            target = target[part]
        _check(value, target, root, path, errors)
        return

    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, n) for n in names):
            errors.append(f"{path}: expected type {schema['type']}, got {type(value).__name__}")
            return

    if "enum" in schema and not any(value == e and type(value) is type(e) for e in schema["enum"]):
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")

    if not isinstance(value, dict):
        return

    for key in schema.get("required", []):
        if key not in value:
            errors.append(f"{path}: missing required key {key!r}")

    properties = schema.get("properties", {})
    patterns = schema.get("patternProperties", {})
    for key, item in value.items():
        child = f"{path}.{key}"
        if "propertyNames" in schema:
            _check(key, schema["propertyNames"], root, f"{child} (key)", errors)
        matched = False
        if key in properties:
            matched = True
            _check(item, properties[key], root, child, errors)
        for pattern, sub in patterns.items():
            if re.search(pattern, key):
                matched = True
                _check(item, sub, root, child, errors)
        if matched:
            continue
        extra = schema.get("additionalProperties", True)
        if extra is False:
            errors.append(f"{path}: unexpected key {key!r}")
        elif isinstance(extra, dict):
            _check(item, extra, root, child, errors)
