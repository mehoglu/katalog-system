import pytest
from pathlib import Path

def test_csv_upload_creates_timestamp_folder(client, sample_csv, test_upload_dir):
    """Test CONTEXT D-03: Zeitstempel-Ordner pro Upload"""
    with open(sample_csv, 'rb') as f:
        response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "upload_id" in data
    assert "filename" in data
    assert data["filename"] == "test.csv"
    
    # Verify timestamp format YYYY-MM-DD_HHMMSS
    upload_id = data["upload_id"]
    assert len(upload_id) == 19  # 2026-03-26_143022
    assert upload_id[4] == "-" and upload_id[7] == "-" and upload_id[10] == "_"
    
    # Verify folder exists
    upload_folder = test_upload_dir / upload_id
    assert upload_folder.exists()
    assert (upload_folder / "test.csv").exists()

def test_csv_upload_rejects_non_csv_files(client, tmp_path):
    """Test file type validation"""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not a csv")
    
    with open(txt_file, 'rb') as f:
        response = client.post(
            "/api/upload/csv",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_separate_upload_steps(client, sample_csv, sample_image, test_upload_dir):
    """Test CONTEXT D-06: Getrennte Schritte (erst CSVs, dann Bilder)"""
    # Step 1: Upload CSV
    with open(sample_csv, 'rb') as f:
        csv_response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    assert csv_response.status_code == 200
    upload_id = csv_response.json()["upload_id"]
    
    # Step 2: Upload images to same session
    with open(sample_image, 'rb') as f:
        img_response = client.post(
            f"/api/upload/images/{upload_id}",
            files={"files": ("test.jpg", f, "image/jpeg")}
        )
    assert img_response.status_code == 200
    data = img_response.json()
    assert data["image_count"] == 1
    assert data["upload_id"] == upload_id
    
    # Verify bilder subfolder created
    bilder_dir = test_upload_dir / upload_id / "bilder"
    assert bilder_dir.exists()
    assert (bilder_dir / "test.jpg").exists()

def test_image_upload_requires_existing_session(client, sample_image):
    """Test image upload validates CSV was uploaded first"""
    with open(sample_image, 'rb') as f:
        response = client.post(
            "/api/upload/images/nonexistent-session",
            files={"files": ("test.jpg", f, "image/jpeg")}
        )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_upload_session_info(client, sample_csv, sample_image, test_upload_dir):
    """Test upload session retrieval"""
    # Upload CSV
    with open(sample_csv, 'rb') as f:
        csv_response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    upload_id = csv_response.json()["upload_id"]
    
    # Upload image
    with open(sample_image, 'rb') as f:
        client.post(
            f"/api/upload/images/{upload_id}",
            files={"files": ("test.jpg", f, "image/jpeg")}
        )
    
    # Get session info
    response = client.get(f"/api/upload/{upload_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["csv_count"] == 1
    assert data["image_count"] == 1
    assert "test.csv" in data["csv_files"]

def test_multiple_csv_uploads_create_separate_sessions(client, sample_csv, test_upload_dir):
    """Test each CSV upload gets own timestamp folder"""
    # Upload 1
    with open(sample_csv, 'rb') as f:
        response1 = client.post(
            "/api/upload/csv",
            files={"file": ("test1.csv", f, "text/csv")}
        )
    upload_id1 = response1.json()["upload_id"]
    
    # Upload 2 (minimal delay to ensure different timestamp)
    import time
    time.sleep(1)
    
    with open(sample_csv, 'rb') as f:
        response2 = client.post(
            "/api/upload/csv",
            files={"file": ("test2.csv", f, "text/csv")}
        )
    upload_id2 = response2.json()["upload_id"]
    
    # Verify separate folders
    assert upload_id1 != upload_id2
    assert (test_upload_dir / upload_id1).exists()
    assert (test_upload_dir / upload_id2).exists()
