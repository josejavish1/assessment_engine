import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Importar el módulo que queremos probar
from assessment_engine.scripts.bootstrap import bootstrap_tower_from_matrix

TEST_DIR = Path(__file__).parent

@pytest.fixture
def mock_paragraphs():
    """Provides a list of strings simulating the paragraphs extracted from a docx."""
    paragraphs_path = TEST_DIR / "test_data" / "bootstrap_test_paragraphs.txt"
    return paragraphs_path.read_text(encoding="utf-8").splitlines()

@pytest.fixture
def expected_definition():
    """Provides the expected JSON output."""
    json_path = TEST_DIR / "test_data" / "expected_bootstrap_output.json"
    return json.loads(json_path.read_text(encoding="utf-8"))

@pytest.fixture
def mock_base_definition():
    """Provides a base definition to be merged."""
    return {
        "schema_name": "tower_definition",
        "schema_version": "1.0",
        "reusable": False,
        "maturity_scale": [],
        "score_bands": [],
        "validation_states": [],
        "working_rules": {},
    }

def test_bootstrap_logic_with_mocked_docx_read(mocker, mock_paragraphs, expected_definition, mock_base_definition):
    """
    This is a focused integration test. It tests the bootstrap_tower function,
    but it mocks the file-reading part to avoid dealing with actual docx files.
    This provides a robust test of the entire parsing and validation logic.
    """
    # Arrange
    mocker.patch(
        'assessment_engine.scripts.bootstrap.bootstrap_tower_from_matrix.extract_docx_paragraphs',
        return_value=mock_paragraphs
    )
    mocker.patch(
        'assessment_engine.scripts.bootstrap.bootstrap_tower_from_matrix.load_json',
        return_value=mock_base_definition
    )
    
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_out_dir = Path(temp_dir_str)

        # Act
        tower_def, manifest, warnings = bootstrap_tower_from_matrix.bootstrap_tower(
            tower_id="T99",
            matrix_file=MagicMock(),
            out_dir=temp_out_dir
        )

        # Assert
        # The generated 'tower_def' contains the merged data. We need to compare
        # it against our 'expected' which should also be merged.
        full_expected = {**mock_base_definition, **expected_definition}
        
        assert tower_def == full_expected
        assert len(warnings) == 0
