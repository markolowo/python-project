# =====================================================================
# ФАЙЛ: tests/test_docs.py — ТЕСТЫ, ЧТО ДОКУМЕНТАЦИЯ СООТВЕТСТВУЕТ ЗАДАНИЮ
# ---------------------------------------------------------------------
# /openapi.json — описание API в формате OpenAPI, из него строятся /docs и /redoc.
# Тесты проходят по нему и проверяют пункты задания: title/description/version, summary и тег у КАЖДОГО
# эндпоинта, не меньше 2 тегов, description минимум у 3 эндпоинтов, description+examples минимум у 3 полей.
# =====================================================================

def test_docs_and_redoc_open(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_app_has_title_description_and_version(client):
    info = client.get("/openapi.json").json()["info"]

    assert info["title"]
    assert len(info["description"]) > 20
    assert info["version"]


def test_every_endpoint_has_summary_and_tag(client):
    paths = client.get("/openapi.json").json()["paths"]
    tags = set()

    for path, methods in paths.items():
        for method, operation in methods.items():
            assert operation.get("summary"), f"{method.upper()} {path} без summary"
            assert operation.get("tags"), f"{method.upper()} {path} без тега"
            tags.update(operation["tags"])

    assert len(tags) >= 2


def test_at_least_three_endpoints_have_description(client):
    paths = client.get("/openapi.json").json()["paths"]
    with_description = [
        operation for methods in paths.values() for operation in methods.values() if operation.get("description")
    ]

    assert len(with_description) >= 3


def test_at_least_three_model_fields_have_description_and_examples(client):
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    documented_fields = [
        field
        for schema in schemas.values()
        for field in schema.get("properties", {}).values()
        if field.get("description") and field.get("examples")
    ]

    assert len(documented_fields) >= 3
