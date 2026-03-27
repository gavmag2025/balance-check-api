from flask import Flask, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time

app = Flask(__name__)

IBIS_USERNAME = os.environ.get('IBIS_USERNAME')
IBIS_PASSWORD = os.environ.get('IBIS_PASSWORD')
LOGIN_URL = 'https://ibisglobalbeam.satcomhost.com/Account/Login?ReturnUrl=%2FWelcome.aspx'
HOME_URL = 'https://ibisglobalbeam.satcomhost.com/'

@app.route('/')
def home():
    return "IsatPhone Balance Check API - READY!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    iccid_msisdn = request.args.get('msisdn')
    
    if not iccid_msisdn:
        return jsonify({'error': '?msisdn= required'}), 400
    
    if not IBIS_USERNAME or not IBIS_PASSWORD:
        return jsonify({'error': 'IBIS_USERNAME & IBIS_PASSWORD env vars missing'}), 500
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': HOME_URL
        })
        
        # 1. LOGIN
        login_data = {
            'username': IBIS_USERNAME,
            'password': IBIS_PASSWORD,
            'Login': 'Login'
        }
        session.post(LOGIN_URL, data=login_data)
        time.sleep(2)
        
        # 2. Go to SIM table
        home_response = session.get(HOME_URL)
        time.sleep(1)
        
        # 3. EXACT DevExpress search (from your screenshots)
        search_data = {
            'ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol0': iccid_msisdn,
            '__CALLBACKID': 'ctl00_ContentPlaceHolder1_gvSIMCards',
            '__CALLBACKPARAM': f'PnlFilter%2CCallbackRowValues%7C0%7C{urllib.parse.quote_plus(iccid_msisdn)}%7C%7C',
            '__VIEWSTATE': BeautifulSoup(home_response.text, 'html.parser').select_one('#__VIEWSTATE')['value'] if BeautifulSoup(home_response.text, 'html.parser').select_one('#__VIEWSTATE') else '',
        }
        
        search_response = session.post(HOME_URL, data=search_data, timeout=15)
        soup = BeautifulSoup(search_response.text, 'html.parser')
        
        # 4. YOUR EXACT SELECTORS
        balance_elems = soup.select('td.dxgv[align="right"]')
        expiry_elems = soup.select('td.dxgv[style*="border-right-width:0px"]')
        
        result = {
            'iccid_msisdn': iccid_msisdn,
            'balance': balance_elems[0].text.strip() if balance_elems else 'No balance found',
            'expiry': expiry_elems[0].text.strip() if expiry_elems else 'No expiry found',
            'rows_found': len(soup.select('tr.dxgvDataRow')),
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
