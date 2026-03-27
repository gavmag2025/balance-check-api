from flask import Flask, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

IBIS_USERNAME = os.environ.get('IBIS_USERNAME')
IBIS_PASSWORD = os.environ.get('IBIS_PASSWORD')
LOGIN_URL = 'https://ibisglobalbeam.satcomhost.com/Account/Login?ReturnUrl=%2FWelcome.aspx'
DASHBOARD_URL = 'https://ibisglobalbeam.satcomhost.com/Welcome.aspx'

@app.route('/')
def home():
    return "IsatPhone Balance Check API v2.0 - LIVE!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    iccid_msisdn = request.args.get('msisdn')
    
    if not iccid_msisdn:
        return jsonify({'error': 'msisdn= required'}), 400
    
    if not IBIS_USERNAME or not IBIS_PASSWORD:
        return jsonify({'error': 'Set IBIS_USERNAME & IBIS_PASSWORD env vars'}), 500
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # STEP 1: LOGIN (EXACT URL from you)
        login_data = {
            'username': IBIS_USERNAME,
            'password': IBIS_PASSWORD,
            'Login': 'Login'
        }
        login_response = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        
        if DASHBOARD_URL not in login_response.url and 'Welcome' not in login_response.text:
            return jsonify({'error': 'Login failed', 'url': login_response.url}), 401
        
        # STEP 2: Go to SIM dashboard & search ICCID
        dashboard_response = session.get(DASHBOARD_URL)
        soup = BeautifulSoup(dashboard_response.text, 'html.parser')
        
        # STEP 3: DevExpress grid search (your exact field)
        search_data = {
            'ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol0': iccid_msisdn,
            '__CALLBACKID': 'ctl00_ContentPlaceHolder1_gvSIMCards',
            '__CALLBACKPARAM': f'PnlFilter%2CCallbackRowValues%7C0%7C{urllib.parse.quote(iccid_msisdn)}'
        }
        
        search_response = session.post(DASHBOARD_URL, data=search_data, timeout=15)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        
        # STEP 4: EXTRACT RESULTS (your exact selectors)
        balance_elem = soup.select_one('td.dxgv[align="right"]')
        expiry_elem = soup.select_one('td.dxgv[style*="border-right-width:0px"]')
        
        result = {
            'iccid_msisdn': iccid_msisdn,
            'balance': balance_elem.text.strip() if balance_elem else 'No balance found',
            'expiry': expiry_elem.text.strip() if expiry_elem else 'No expiry found',
            'status': 'success'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
