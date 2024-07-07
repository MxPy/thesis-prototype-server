import requests

def test_call_home_endporint():
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200
    
    
def test_call_postgres_user_delete_get_all_endporint():
    response = requests.delete("http://localhost:8000/dev/user/delete/all")
    assert response.status_code == 204
    response = requests.get("http://localhost:8000/dev/user/get/all")
    assert response.status_code == 404

def test_call_postgres_user_post_endporint():
    response = requests.get("http://localhost:8000/dev/user/get/all")
    assert response.status_code == 404
    user = {
            "username": "string",
            "email": "string",
            "password": "string"
            }
    response = requests.post("http://localhost:8000/user/post",json = user)
    assert response.status_code == 201
    response = requests.get("http://localhost:8000/dev/user/get/all")
    assert response.status_code == 200
    response = requests.delete("http://localhost:8000/dev/user/delete/all")
    assert response.status_code == 204
    response = requests.get("http://localhost:8000/dev/user/get/all")
    assert response.status_code == 404