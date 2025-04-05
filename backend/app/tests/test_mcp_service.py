import pytest
from unittest.mock import patch, MagicMock
from app.services.mcp_service import MCPService


class TestMCPService:
    """
    Unit tests for the Model Context Provider service
    """

    @pytest.fixture
    def mcp_service(self):
        """Create a MCPService instance for testing"""
        with patch('app.services.mcp_service.CanvasService') as mock_canvas:
            with patch(
                    'app.services.mcp_service.StevensService') as mock_stevens:
                # Configure the mocks
                mock_canvas_instance = MagicMock()
                mock_stevens_instance = MagicMock()

                # Set up return values for Canvas service methods
                mock_canvas_instance.get_current_courses.return_value = [{
                    "id":
                    101,
                    "name":
                    "Test Course 1",
                    "course_code":
                    "TC101"
                }, {
                    "id":
                    102,
                    "name":
                    "Test Course 2",
                    "course_code":
                    "TC102"
                }]
                mock_canvas_instance.format_courses_response.return_value = "Test Course 1 (TC101)\nTest Course 2 (TC102)"

                # Set up mock assignments data
                mock_assignments = {
                    "courses": [{
                        "course_name":
                        "Test Course 1",
                        "assignments": [{
                            "name":
                            "Assignment 1",
                            "due_at":
                            "2024-05-15T23:59:00Z",
                            "points_possible":
                            100,
                            "html_url":
                            "https://example.com/assignment1"
                        }]
                    }]
                }
                mock_canvas_instance.get_assignments_for_course.return_value = mock_assignments

                # Set up mock announcements data
                mock_announcements = {
                    "courses": [{
                        "course_name":
                        "Test Course 1",
                        "course_announcements_link":
                        "https://example.com/announcements",
                        "announcements": [{
                            "title": "Test Announcement",
                            "posted_at": "2024-04-10T12:00:00Z",
                            "author": {
                                "display_name": "Professor Test"
                            }
                        }]
                    }]
                }
                mock_canvas_instance.get_announcements_for_course.return_value = mock_announcements

                # Set up Stevens service methods
                mock_stevens_instance.get_professors.return_value = [{
                    "name":
                    "Professor Smith",
                    "department":
                    "Computer Science"
                }]

                # Set the instances as the return values for the constructor
                mock_canvas.return_value = mock_canvas_instance
                mock_stevens.return_value = mock_stevens_instance

                # Create and return the service
                service = MCPService()
                yield service

    def test_get_user_context_all_types(self, mcp_service):
        """Test retrieving all context types together"""
        # Request all context types
        context_types = [
            "courses", "assignments", "announcements", "professors"
        ]
        result = mcp_service.get_user_context(context_types)

        # Verify metadata
        assert "context_meta" in result
        assert "retrieved_at" in result["context_meta"]
        assert result["context_meta"]["requested_types"] == context_types
        assert set(result["context_meta"]["source_systems"]) == {
            "Canvas", "Stevens API"
        }

        # Verify all requested types are present
        for context_type in context_types:
            assert context_type in result
            assert result[context_type]["success"] is True
            assert result[context_type]["data"] is not None
            assert result[context_type]["error"] is None

    def test_get_user_context_courses_only(self, mcp_service):
        """Test retrieving only courses context"""
        result = mcp_service.get_user_context(["courses"])

        # Verify courses data
        assert "courses" in result
        assert result["courses"]["success"] is True
        assert len(result["courses"]["data"]) == 2

        # Verify course fields
        course = result["courses"]["data"][0]
        assert "id" in course
        assert "name" in course
        assert "code" in course
        assert "url" in course

        # Verify formatted response
        assert result["courses"]["formatted_response"] is not None

    def test_get_user_context_assignments_only(self, mcp_service):
        """Test retrieving only assignments context"""
        result = mcp_service.get_user_context(["assignments"])

        # Verify assignments data
        assert "assignments" in result
        assert result["assignments"]["success"] is True
        assert "data" in result["assignments"]
        assert "course_assignments" in result["assignments"]["data"]
        assert "all_assignments" in result["assignments"]["data"]

        # Verify assignment fields
        assignment = result["assignments"]["data"]["all_assignments"][0]
        assert "name" in assignment
        assert "course_name" in assignment
        assert "due_at" in assignment
        assert "points_possible" in assignment
        assert "url" in assignment

    def test_get_user_context_announcements_only(self, mcp_service):
        """Test retrieving only announcements context"""
        result = mcp_service.get_user_context(["announcements"])

        # Verify announcements data
        assert "announcements" in result
        assert result["announcements"]["success"] is True

        # Verify announcement fields
        announcement = result["announcements"]["data"]["all_announcements"][0]
        assert "title" in announcement
        assert "course_name" in announcement
        assert "posted_at" in announcement
        assert "author" in announcement

    def test_get_user_context_professors_only(self, mcp_service):
        """Test retrieving only professors context"""
        result = mcp_service.get_user_context(["professors"])

        # Verify professors data
        assert "professors" in result
        assert result["professors"]["success"] is True
        assert len(result["professors"]["data"]) == 1

        # Verify professor fields
        professor = result["professors"]["data"][0]
        assert "name" in professor
        assert "department" in professor

    def test_get_user_context_invalid_type(self, mcp_service):
        """Test requesting an invalid context type"""
        result = mcp_service.get_user_context(["invalid_type"])

        # Should still return metadata but no invalid_type key
        assert "context_meta" in result
        assert "invalid_type" not in result

    @patch('app.services.mcp_service.CanvasService')
    def test_get_user_context_with_errors(self, mock_canvas):
        """Test error handling when a service fails"""
        # Configure Canvas service to raise an exception
        mock_canvas_instance = MagicMock()
        mock_canvas_instance.get_current_courses.side_effect = Exception(
            "Test error")
        mock_canvas.return_value = mock_canvas_instance

        # Create service with failing dependency
        service = MCPService()

        # Request courses which should fail
        result = service.get_user_context(["courses"])

        # Verify error handling
        assert "courses" in result
        assert result["courses"]["success"] is False
        assert result["courses"]["data"] is None
        assert "Test error" in result["courses"]["error"]

        # Verify error in metadata
        assert "errors" in result["context_meta"]
        assert "Error with courses" in result["context_meta"]["errors"][0]
