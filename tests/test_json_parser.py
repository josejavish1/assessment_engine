import pytest

from assessment_engine.scripts.lib.json_from_model import parse_json_from_text


def test_parse_clean_json():
    """Prueba que parsea un JSON limpio sin markdown."""
    raw_text = '{"clave": "valor"}'
    result = parse_json_from_text(raw_text)
    assert result == {"clave": "valor"}

def test_parse_markdown_json():
    """Prueba que parsea un JSON envuelto en bloques markdown."""
    raw_text = '''```json
{
  "clave": "valor_markdown"
}
```'''
    result = parse_json_from_text(raw_text)
    assert result == {"clave": "valor_markdown"}

def test_parse_json_with_leading_trailing_text():
    """Prueba que extrae el JSON aunque haya texto alrededor."""
    raw_text = '''Aquí tienes la respuesta:
```json
{"resultado": 123}
```
Espero que te sirva.'''
    result = parse_json_from_text(raw_text)
    assert result == {"resultado": 123}

def test_parse_json_invalid():
    """Prueba que maneja errores de parseo correctamente."""
    raw_text = '{"clave": "falta cerrar comillas}'
    with pytest.raises(ValueError):
        parse_json_from_text(raw_text)
