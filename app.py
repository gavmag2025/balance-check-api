from flask import Flask, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = Flask(__name__)

# Get credentials from Environment vars
IBIS_USERNAME = os.environ.get('IBIS_USERNAME')
IBIS_PASSWORD = os.environ.get('IBIS_PASSWORD')
IBIS_BASE_URL = 'https://ibisglobalbeam.satcomhost.com'

@app.route('/')
def home():
    return "IsatPhone Balance Check API - LIVE!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    iccid_msisdn = request.args.get('msisdn')
    
    if not iccid_msisdn:
        return jsonify({'error': 'msisdn parameter required'}), 400
    
    if not IBIS_USERNAME or not IBIS_PASSWORD:
        return jsonify({'error': 'IBIS credentials missing'}), 500
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # STEP 1: CORRECT LOGIN (from your screenshot)
        login_data = {
            'username': IBIS_USERNAME,    # ← FIXED
            'password': IBIS_PASSWORD,    # ← FIXED
            'Login': 'Login'              # ← Button value
        }
        login_response = session.post(IBIS_BASE_URL, data=login_data)
        
        if 'Dashboard' not in login_response.text and 'welcome' not in login_response.text.lower():
            return jsonify({'error': 'IBIS login failed'}), 401
        
        # STEP 2: Submit ICCID (DevExpress grid callback)
        form_data = {
            'ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol0': iccid_msisdn,
            '__CALLBACKID': 'ctl00_ContentPlaceHolder1_gvSIMCards',
            '__CALLBACKPARAM': f'PnlFilter%2CCallbackRowValues%7C0%7C{urllib.parse.quote(iccid_msisdn)}'
        }
        
        response = session.post(f'{IBIS_BASE_URL}/Default.aspx', data=form_data, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # STEP 3: EXACT SELECTORS (from your earlier screenshot)
        balance_elem = soup.select_one('td.dxgv[align="right"]')
        expiry_elem = soup.select_one('td.dxgv[style*="border-right-width:0px"]')
        
        result = {
            'iccid_msisdn': iccid_msisdn,
            'balance': balance_elem.text.strip() if balance_elem else 'Login may be required',
            'expiry': expiry_elem.text.strip() if expiry_elem else 'Login may be required',
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
