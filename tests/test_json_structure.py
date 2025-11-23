import pytest
import json
import os
from pathlib import Path
from module_utils.GitLab.models import Repository, Group


class TestRepositoryJSONStructure:

    # Opret data med den forventede struktur
    @pytest.fixture
    def sample_repository_data(self):
        return {
            "id": 12345,
            "name": "test-repo",
            "description": "Test repository",
            "visibility": "private",
            "last_activity_at": "2025-11-18T10:30:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo"
        }
    
    # Opret data med den minimale struktur (uden optional felter)
    @pytest.fixture
    def sample_repository_minimal_structure(self):
        return {
            "id": 12345,
            "name": "test-repo",
            "last_activity_at": "2025-11-18T10:30:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo",
        }
    
    # Test at påkrævede felter håndteres korrekt
    def test_json_has_required_fields(self, sample_repository_data):
        repo = Repository.from_api(sample_repository_data)
        repo_dict = repo.to_dict()
        
        required_fields = ["id", "name", "last_activity_at", "web_url"]
        
        for field in required_fields:
            assert field in repo_dict, f"Missing required field: {field}"
            assert repo_dict[field] is not None, f"Field {field} should not be None"
    
    # Test at optional fields håndteres korrekt
    def test_json_optional_fields(self, sample_repository_data):
        repo = Repository.from_api(sample_repository_data)
        repo_dict = repo.to_dict()
        
        optional_fields = ["description", "visibility"]
        
        for field in optional_fields:
            assert field in repo_dict, f"Optional field {field} should exist in dict"
    
    # Test at field types er korrekte
    def test_json_field_types(self, sample_repository_data):
        repo = Repository.from_api(sample_repository_data)
        repo_dict = repo.to_dict()
        
        assert isinstance(repo_dict["id"], int), "id should be int"
        assert isinstance(repo_dict["name"], str), "name should be str"
        assert isinstance(repo_dict["web_url"], str), "web_url should be str"
        assert isinstance(repo_dict["last_activity_at"], str), "last_activity_at should be str"
        
        if repo_dict["description"] is not None:
            assert isinstance(repo_dict["description"], str), "description should be str or None"
        
        if repo_dict["visibility"] is not None:
            assert isinstance(repo_dict["visibility"], str), "visibility should be str or None"
    
    # Test at Repository kan serialiseres til JSON uden fejl
    def test_repository_json_serializable(self, sample_repository_data):
        repo = Repository.from_api(sample_repository_data)
        repo_dict = repo.to_dict()
        
        try:
            json_string = json.dumps(repo_dict, ensure_ascii=False)
            assert json_string is not None
            
            # Test at vi kan parse det igen
            parsed = json.loads(json_string)
            assert parsed == repo_dict
        except Exception as e:
            pytest.fail(f"JSON serialization failed: {e}")
    
    # Test at Repository fungerer med minimal data
    def test_repository_minimal_data(self, sample_repository_minimal_structure):
        repo = Repository.from_api(sample_repository_minimal_structure)
        repo_dict = repo.to_dict()
        
        assert repo_dict["description"] is None
        assert repo_dict["visibility"] is None
        assert repo_dict["id"] == 12345
        assert repo_dict["name"] == "test-repo"
    
    # Test at visibility har gyldige værdier
    def test_repository_visibility_values(self):
        valid_visibilities = ["private", "internal", "public", None]
        
        for visibility in valid_visibilities:
            data = {
                "id": 123,
                "name": "test",
                "visibility": visibility,
                "last_activity_at": "2025-11-18T10:00:00Z",
                "web_url": "https://example.com",
            }
            repo = Repository.from_api(data)
            assert repo.visibility == visibility
