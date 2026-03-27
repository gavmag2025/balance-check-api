@app.route('/debug-login')
def debug_login():
    session = requests.Session()
    login_data = {
        'username': IBIS_USERNAME,
        'password': IBIS_PASSWORD,
        'Login': 'Login'
    }
    response = session.post(IBIS_BASE_URL, data=login_data)
    return {
        'success': 'Dashboard' in response.text,
        'title': BeautifulSoup(response.text, 'html.parser').title.string if BeautifulSoup(response.text, 'html.parser').title else 'No title',
        'response_snippet': response.text[:500]
    }
