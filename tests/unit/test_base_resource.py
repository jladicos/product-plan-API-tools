"""
Unit tests for BaseResource class

Tests authentication, HTTP requests, pagination, and error handling.
Since BaseResource is abstract, we create a concrete TestResource for testing.
"""

import pytest
import requests
from unittest.mock import Mock, patch, mock_open
from productplan_api_tools.api.client import BaseResource


# Concrete implementation of BaseResource for testing
class TestResource(BaseResource):
    """Concrete test implementation of BaseResource"""

    @property
    def endpoint_path(self) -> str:
        return "test/endpoint"


class TestBaseResourceInit:
    """Test BaseResource initialization and authentication"""

    def test_init_reads_token_file(self):
        """Test that __init__ reads token from file"""
        mock_file_content = "test_token_12345"

        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            resource = TestResource(token_file="token.txt")

            assert resource.token == "test_token_12345"
            assert resource.headers["authorization"] == "Bearer test_token_12345"
            assert resource.headers["accept"] == "application/json"

    def test_init_strips_whitespace_from_token(self):
        """Test that __init__ strips whitespace from token"""
        mock_file_content = "  test_token_12345  \n"

        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            resource = TestResource(token_file="token.txt")

            assert resource.token == "test_token_12345"

    def test_init_raises_system_exit_if_file_not_found(self):
        """Test that __init__ exits if token file doesn't exist"""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            with pytest.raises(SystemExit):
                TestResource(token_file="missing.txt")

    def test_init_raises_system_exit_on_read_error(self):
        """Test that __init__ exits on file read errors"""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with pytest.raises(SystemExit):
                TestResource(token_file="token.txt")


class TestBaseResourceMakeRequest:
    """Test BaseResource._make_request() method"""

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_success(self, mock_get):
        """Test successful API request"""
        # Setup
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": 1, "name": "Test"}],
            "paging": {"next": None}
        }
        mock_get.return_value = mock_response

        resource = TestResource()

        # Execute
        result = resource._make_request("test/endpoint", params={"page": 1})

        # Verify
        assert result["results"] == [{"id": 1, "name": "Test"}]
        assert "paging" in result
        mock_get.assert_called_once()

        # Verify URL construction
        call_args = mock_get.call_args
        assert call_args[0][0] == "https://app.productplan.com/api/v2/test/endpoint"
        assert call_args[1]["params"] == {"page": 1}
        assert call_args[1]["headers"]["authorization"] == "Bearer test_token"

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_with_no_params(self, mock_get):
        """Test API request without parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        resource = TestResource()
        result = resource._make_request("test/endpoint")

        assert result == {"results": []}
        call_args = mock_get.call_args
        assert call_args[1]["params"] is None

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_handles_401_error(self, mock_get):
        """Test that 401 authentication error raises SystemExit"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_get.return_value = mock_response

        resource = TestResource()

        with pytest.raises(SystemExit):
            resource._make_request("test/endpoint")

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_handles_404_error(self, mock_get):
        """Test that 404 not found error raises SystemExit"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        resource = TestResource()

        with pytest.raises(SystemExit):
            resource._make_request("test/endpoint")

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_handles_500_error(self, mock_get):
        """Test that 500 server error raises SystemExit"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Internal Server Error")
        mock_get.return_value = mock_response

        resource = TestResource()

        with pytest.raises(SystemExit):
            resource._make_request("test/endpoint")

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_make_request_handles_network_error(self, mock_get):
        """Test that network errors raise SystemExit"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        resource = TestResource()

        with pytest.raises(SystemExit):
            resource._make_request("test/endpoint")


class TestBaseResourceFetchAllPages:
    """Test BaseResource._fetch_all_pages() method"""

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_all_pages_single_page(self, mock_get):
        """Test fetching when only one page exists"""
        # Single page response with no next page
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": 1}, {"id": 2}],
            "paging": {"next": None, "page": 1}
        }
        mock_get.return_value = mock_response

        resource = TestResource()
        result = resource._fetch_all_pages("test/endpoint", page_size=200)

        assert len(result["results"]) == 2
        assert result["results"][0]["id"] == 1
        assert result["results"][1]["id"] == 2
        # Should only make one API call
        assert mock_get.call_count == 1

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_all_pages_multiple_pages(self, mock_get):
        """Test fetching across multiple pages"""
        # Setup responses for 3 pages
        response_page1 = Mock()
        response_page1.status_code = 200
        response_page1.json.return_value = {
            "results": [{"id": 1}, {"id": 2}],
            "paging": {"next": "page2_url", "page": 1}
        }

        response_page2 = Mock()
        response_page2.status_code = 200
        response_page2.json.return_value = {
            "results": [{"id": 3}, {"id": 4}],
            "paging": {"next": "page3_url", "page": 2}
        }

        response_page3 = Mock()
        response_page3.status_code = 200
        response_page3.json.return_value = {
            "results": [{"id": 5}],
            "paging": {"next": None, "page": 3}
        }

        mock_get.side_effect = [response_page1, response_page2, response_page3]

        resource = TestResource()
        result = resource._fetch_all_pages("test/endpoint", page_size=2)

        # Should have all results from all pages
        assert len(result["results"]) == 5
        assert result["results"][0]["id"] == 1
        assert result["results"][4]["id"] == 5

        # Should have made 3 API calls
        assert mock_get.call_count == 3

        # Verify pagination parameters
        calls = mock_get.call_args_list
        assert calls[0][1]["params"]["page"] == 1
        assert calls[1][1]["params"]["page"] == 2
        assert calls[2][1]["params"]["page"] == 3

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_all_pages_with_filters(self, mock_get):
        """Test that filters are applied to all pages"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": 1}],
            "paging": {"next": None}
        }
        mock_get.return_value = mock_response

        resource = TestResource()
        filters = {"name": "Test", "status": "active"}
        result = resource._fetch_all_pages("test/endpoint", page_size=100, filters=filters)

        # Verify filters were converted to q[key] format
        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert params["q[name]"] == "Test"
        assert params["q[status]"] == "active"

    @patch('productplan_api_tools.api.client.requests.get')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_all_pages_empty_results(self, mock_get):
        """Test handling of empty results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [],
            "paging": {"next": None}
        }
        mock_get.return_value = mock_response

        resource = TestResource()
        result = resource._fetch_all_pages("test/endpoint")

        assert result["results"] == []
        assert mock_get.call_count == 1


class TestBaseResourceFetchList:
    """Test BaseResource.fetch_list() method"""

    @patch.object(TestResource, '_make_request')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_list_single_page(self, mock_make_request):
        """Test fetch_list for single page"""
        mock_make_request.return_value = {
            "results": [{"id": 1}],
            "paging": {"next": None}
        }

        resource = TestResource()
        result = resource.fetch_list(page=1, page_size=100)

        assert result["results"] == [{"id": 1}]
        mock_make_request.assert_called_once()

        # Verify it used the resource's endpoint_path
        call_args = mock_make_request.call_args
        assert call_args[0][0] == "test/endpoint"

    @patch.object(TestResource, '_fetch_all_pages')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_list_all_pages(self, mock_fetch_all_pages):
        """Test fetch_list with get_all=True"""
        mock_fetch_all_pages.return_value = {
            "results": [{"id": 1}, {"id": 2}, {"id": 3}],
            "paging": {"next": None}
        }

        resource = TestResource()
        result = resource.fetch_list(page=1, page_size=100, get_all=True)

        assert len(result["results"]) == 3
        mock_fetch_all_pages.assert_called_once_with("test/endpoint", 100, None)

    @patch.object(TestResource, '_make_request')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_list_with_filters(self, mock_make_request):
        """Test fetch_list with filter parameters"""
        mock_make_request.return_value = {"results": []}

        resource = TestResource()
        filters = {"status": "active"}
        result = resource.fetch_list(filters=filters)

        # Verify filters were passed to _make_request
        call_args = mock_make_request.call_args
        params = call_args[0][1]  # Second positional arg
        assert params["q[status]"] == "active"


class TestBaseResourceFetchDetails:
    """Test BaseResource.fetch_details() method"""

    @patch.object(TestResource, '_make_request')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_details_success(self, mock_make_request):
        """Test fetching details for a single item"""
        mock_make_request.return_value = {
            "id": 123,
            "name": "Test Item",
            "description": "Detailed information"
        }

        resource = TestResource()
        result = resource.fetch_details(123)

        assert result["id"] == 123
        assert result["name"] == "Test Item"

        # Verify endpoint includes item ID
        call_args = mock_make_request.call_args
        assert call_args[0][0] == "test/endpoint/123"

    @patch.object(TestResource, '_make_request')
    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_fetch_details_different_ids(self, mock_make_request):
        """Test that different IDs create different endpoints"""
        resource = TestResource()

        resource.fetch_details(456)
        call1 = mock_make_request.call_args[0][0]

        resource.fetch_details(789)
        call2 = mock_make_request.call_args[0][0]

        assert call1 == "test/endpoint/456"
        assert call2 == "test/endpoint/789"


class TestAbstractBaseClass:
    """Test that BaseResource is properly abstract"""

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_cannot_instantiate_base_resource_directly(self):
        """Test that BaseResource cannot be instantiated without endpoint_path"""

        # Trying to instantiate BaseResource directly should fail
        with pytest.raises(TypeError) as exc_info:
            BaseResource(token_file="token.txt")

        # Error message should mention abstract method
        assert "abstract" in str(exc_info.value).lower() or "endpoint_path" in str(exc_info.value)

    @patch('builtins.open', mock_open(read_data="test_token"))
    def test_subclass_must_implement_endpoint_path(self):
        """Test that subclasses must implement endpoint_path property"""

        class IncompleteResource(BaseResource):
            pass  # Doesn't implement endpoint_path

        # Should not be able to instantiate
        with pytest.raises(TypeError):
            IncompleteResource(token_file="token.txt")
