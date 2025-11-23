import pytest
import json
import responses
from unittest.mock import Mock, patch, MagicMock
from module_utils.GitLab.query import GitLabAPI
from module_utils.GitLab.models import Repository, Group

# Test at vi henter korrekt data fra GitLab API
class TestGitLabAPIIntegration:

    @pytest.fixture
    def api_client(self):
        """Mock GitLab API client"""
        return GitLabAPI(
            base_url="https://gitlab.example.com",
            token="test-token-123"
        )
    
    @pytest.fixture
    def mock_group_response(self):
        """Mock gruppe response fra GitLab"""
        return {
            "id": 100,
            "name": "Test Group",
            "full_path": "test-group",
            "description": "Test description",
            "visibility": "private"
        }

    @pytest.fixture
    def mock_projects_response(self):
        """Mock projekter response fra GitLab"""
        return [
            {
                "id": 1,
                "name": "project-1",
                "web_url": "https://gitlab.example.com/test-group/project-1",
                "last_activity_at": "2025-11-18T10:00:00Z",
                "name_with_namespace": "Test Group / project-1",
                "description": "First project",
                "visibility": "private"
            },
            {
                "id": 2,
                "name": "project-2",
                "web_url": "https://gitlab.example.com/test-group/project-2",
                "last_activity_at": "2025-11-17T15:30:00Z",
                "name_with_namespace": "Test Group / project-2",
                "description": None,
                "visibility": "internal"
            }
        ]
    
    @pytest.fixture
    def mock_subgroups_response(self):
        """Mock undergrupper response fra GitLab"""
        return [
            {
                "id": 101,
                "name": "Subgroup 1",
                "full_path": "test-group/subgroup-1"
            }
        ]
    
    @responses.activate
    def test_get_repositories_returns_correct_data(self, api_client, mock_projects_response):
        """Test at get_repositories returnerer korrekt projekt data"""
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=mock_projects_response,
            status=200
        )
        
        repos = api_client.get_repositories(100)
        
        assert len(repos) == 2
        assert repos[0]["id"] == 1
        assert repos[0]["name"] == "project-1"
        assert repos[1]["id"] == 2
        assert repos[1]["name"] == "project-2"

    @responses.activate
    def test_get_group_tree_returns_complete_structure(
        self, api_client, mock_group_response, mock_projects_response, mock_subgroups_response
    ):
        """Test at get_group_tree returnerer komplet træ struktur"""
        # Mock gruppe data
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100",
            json=mock_group_response,
            status=200
        )
        
        # Mock projekter
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=mock_projects_response,
            status=200
        )
        
        # Mock undergrupper
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/subgroups?per_page=100",
            json=[],  # Ingen undergrupper for at forenkle test
            status=200
        )
        
        tree = api_client.get_group_tree(100, max_depth=1)
        
        # Verificer struktur
        assert tree is not None
        assert tree["id"] == 100
        assert tree["name"] == "Test Group"
        assert tree["full_path"] == "test-group"
        assert len(tree["projects"]) == 2
        assert len(tree["subgroups"]) == 0
        
        # Verificer projekt data
        assert tree["projects"][0]["id"] == 1
        assert tree["projects"][0]["name"] == "project-1"
        assert tree["projects"][1]["id"] == 2

    @responses.activate
    def test_pagination_handles_multiple_pages(self, api_client):
        """Test at pagination fungerer korrekt"""
        # Side 1
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=[{"id": 1, "name": "repo-1"}],
            status=200,
            headers={"Link": '<https://gitlab.example.com/api/v4/groups/100/projects?per_page=100&page=2>; rel="next"'}
        )
        
        # Side 2
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100&page=2",
            json=[{"id": 2, "name": "repo-2"}],
            status=200
        )
        
        repos = api_client.get_repositories(100)
        
        assert len(repos) == 2
        assert repos[0]["id"] == 1
        assert repos[1]["id"] == 2

    
class TestRepositoryDataMapping:
    """Test at Repository model mapper GitLab data korrekt"""
    
    def test_repository_maps_all_fields_from_api(self):
        """Test at alle felter fra API mappes korrekt til Repository"""
        api_data = {
            "id": 123,
            "name": "test-repo",
            "description": "Test description",
            "visibility": "private",
            "last_activity_at": "2025-11-18T10:00:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo",
        }
        
        repo = Repository.from_api(api_data)
        
        assert repo.id == 123
        assert repo.name == "test-repo"
        assert repo.description == "Test description"
        assert repo.visibility == "private"
        assert repo.last_activity_at == "2025-11-18T10:00:00Z"
        assert repo.web_url == "https://gitlab.example.com/group/test-repo"

    
    def test_repository_handles_missing_optional_fields(self):
        """Test at Repository håndterer manglende optional felter"""
        api_data = {
            "id": 123,
            "name": "test-repo",
            "last_activity_at": "2025-11-18T10:00:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo",
        }
        
        repo = Repository.from_api(api_data)
        
        assert repo.description is None
        assert repo.visibility is None

    def test_repository_preserves_data_types(self):
        """Test at data typer bevares korrekt"""
        api_data = {
            "id": 123,
            "name": "test-repo",
            "description": None,  # Explicit None
            "visibility": "private",
            "last_activity_at": "2025-11-18T10:00:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo",
            "name_with_namespace": "Group / test-repo"
        }
        
        repo = Repository.from_api(api_data)
        repo_dict = repo.to_dict()
        
        assert isinstance(repo_dict["id"], int)
        assert isinstance(repo_dict["name"], str)
        assert repo_dict["description"] is None
        assert isinstance(repo_dict["visibility"], str)

class TestGroupDataMapping:
    """Test at Group model mapper tree data korrekt"""
    
    def test_group_maps_all_fields_from_tree(self):
        """Test at alle felter fra tree mappes korrekt til Group"""
        tree_data = {
            "id": 100,
            "name": "Test Group",
            "full_path": "test-group",
            "projects": [{"id": 1}, {"id": 2}],
            "subgroups": [{"id": 101}]
        }
        
        group = Group.from_tree(tree_data)
        
        assert group.id == 100
        assert group.name == "Test Group"
        assert group.full_path == "test-group"
        assert group.project_count == 2
        assert group.subgroup_count == 1
    
    def test_group_counts_are_accurate(self):
        """Test at project/subgroup counts er præcise"""
        tree_data = {
            "id": 100,
            "name": "Test Group",
            "full_path": "test-group",
            "projects": [{"id": i} for i in range(5)],
            "subgroups": [{"id": i} for i in range(3)]
        }
        
        group = Group.from_tree(tree_data)
        
        assert group.project_count == 5
        assert group.subgroup_count == 3

        
class TestRealWorldScenarios:
    """Test realistiske scenarier med faktisk data struktur"""
    
    @responses.activate
    def test_empty_group_handling(self):
        """Test håndtering af tom gruppe (ingen projekter/subgroups)"""
        api = GitLabAPI("https://gitlab.example.com", "token")
        
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100",
            json={"id": 100, "name": "Empty Group", "full_path": "empty"},
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=[],
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/subgroups?per_page=100",
            json=[],
            status=200
        )
        
        tree = api.get_group_tree(100, max_depth=1)
        
        assert tree is not None
        assert len(tree["projects"]) == 0
        assert len(tree["subgroups"]) == 0
    
    @responses.activate
    def test_max_depth_limit_enforced(self):
        """Test at max_depth grænse overholdes"""
        api = GitLabAPI("https://gitlab.example.com", "token")
        
        # Setup deep nested structure
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100",
            json={"id": 100, "name": "Root", "full_path": "root"},
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=[],
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/subgroups?per_page=100",
            json=[{"id": 101, "name": "Level1"}],
            status=200
        )
        
        tree = api.get_group_tree(100, max_depth=1)
        
        # Med max_depth=1, subgroups burde være tomme
        assert tree is not None
        assert len(tree["subgroups"]) == 0
    
    @responses.activate
    def test_large_group_with_many_projects(self):
        """Test håndtering af gruppe med mange projekter"""
        api = GitLabAPI("https://gitlab.example.com", "token")
        
        # Simuler 150 projekter (over pagination limit) med alle required fields
        projects_page1 = [
            {
                "id": i,
                "name": f"repo-{i}",
                "web_url": f"https://gitlab.example.com/large/repo-{i}",
                "last_activity_at": "2025-11-18T10:00:00Z",
                "name_with_namespace": f"Large Group / repo-{i}",
                "description": f"Repository {i}",
                "visibility": "private"
            }
            for i in range(100)
        ]
        projects_page2 = [
            {
                "id": i,
                "name": f"repo-{i}",
                "web_url": f"https://gitlab.example.com/large/repo-{i}",
                "last_activity_at": "2025-11-18T10:00:00Z",
                "name_with_namespace": f"Large Group / repo-{i}",
                "description": f"Repository {i}",
                "visibility": "private"
            }
            for i in range(100, 150)
        ]
        
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100",
            json={"id": 100, "name": "Large Group", "full_path": "large"},
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100",
            json=projects_page1,
            status=200,
            headers={"Link": '<https://gitlab.example.com/api/v4/groups/100/projects?per_page=100&page=2>; rel="next"'}
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/projects?per_page=100&page=2",
            json=projects_page2,
            status=200
        )
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100/subgroups?per_page=100",
            json=[],
            status=200
        )
        
        tree = api.get_group_tree(100, max_depth=1)
        
        assert tree is not None
        assert len(tree["projects"]) == 150
    
    def test_repository_with_special_characters(self):
        """Test håndtering af projekter med special characters"""
        api_data = {
            "id": 123,
            "name": "test-repo-æøå-!@#",
            "description": "Beskrivelse med æøå og emoji 🚀",
            "visibility": "private",
            "last_activity_at": "2025-11-18T10:00:00Z",
            "web_url": "https://gitlab.example.com/group/test-repo",
            "name_with_namespace": "Group / test-repo-æøå"
        }
        
        repo = Repository.from_api(api_data)
        repo_dict = repo.to_dict()
        
        # Verificer at special characters bevares
        assert "æøå" in repo.name
        assert "🚀" in repo.description
        
        # Verificer at det kan serialiseres til JSON
        json_string = json.dumps(repo_dict, ensure_ascii=False)
        parsed = json.loads(json_string)
        assert parsed["name"] == api_data["name"]


class TestErrorHandling:
    """Test fejlhåndtering ved API problemer"""
    
    @responses.activate
    def test_api_error_returns_none(self):
        """Test at API fejl returnerer None i stedet for at crashe"""
        api = GitLabAPI("https://gitlab.example.com", "token")
        
        responses.add(
            responses.GET,
            "https://gitlab.example.com/api/v4/groups/100",
            json={"error": "Not found"},
            status=404
        )
        
        tree = api.get_group_tree(100, max_depth=1)
        
        assert tree is None