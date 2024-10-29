# tests/test_auth.py

def test_login_success(app):
    client = app.test_client()
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    # Agrega más aserciones según sea necesario

def test_login_failure(app):
    client = app.test_client()
    response = client.post('/login', data={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    assert response.status_code == 401  # O el código de estado que uses para fallos de login

def test_logout(app):
    client = app.test_client()
    with client:
        client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        response = client.get('/logout')
        assert response.status_code == 200
        # Agrega más aserciones según sea necesario

