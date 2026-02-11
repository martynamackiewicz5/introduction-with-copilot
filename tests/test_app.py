"""Tests for the Mergington High School API."""
import pytest
from urllib.parse import quote


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9

    def test_get_activities_contains_correct_fields(self, client, reset_activities):
        """Test that activities have all required fields."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_is_list(self, client, reset_activities):
        """Test that participants is a list."""
        response = client.get("/activities")
        data = response.json()
        
        assert isinstance(data["Chess Club"]["participants"], list)
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]


class TestSignUpForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup adds the participant to the activity."""
        client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        
        assert "newstudent@mergington.edu" in activity["participants"]
        assert len(activity["participants"]) == 3

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for a nonexistent activity."""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Test that students cannot signup twice for the same activity."""
        # Try to signup a student who is already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities."""
        email = "multiplesignup@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(
            f"/activities/Programming Class/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify signed up for both
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""

    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes the participant from the activity."""
        client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        
        assert "michael@mergington.edu" not in activity["participants"]
        assert len(activity["participants"]) == 1

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister for a nonexistent activity."""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_signed_up_student(self, client, reset_activities):
        """Test that unregistering a student not signed up fails."""
        response = client.post(
            "/activities/Chess Club/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can signup again after unregistering."""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.post(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify signed up
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        assert email in activity["participants"]


class TestEmailEncoding:
    """Tests for email URL encoding."""

    def test_signup_with_special_characters_in_email(self, client, reset_activities):
        """Test signup with email containing special characters."""
        email = "test+tag@mergington.edu"
        response = client.post(
            f"/activities/Chess Club/signup?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify it was added
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        assert email in activity["participants"]

    def test_unregister_with_special_characters_in_email(self, client, reset_activities):
        """Test unregister with email containing special characters."""
        email = "test+tag@mergington.edu"
        
        # First sign up
        client.post(
            f"/activities/Chess Club/signup?email={quote(email)}"
        )
        
        # Then unregister
        response = client.post(
            f"/activities/Chess Club/unregister?email={quote(email)}"
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        activity = response.json()["Chess Club"]
        assert email not in activity["participants"]
