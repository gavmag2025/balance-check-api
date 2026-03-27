from flask import Flask, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
import time
import urllib.parse

app = Flask(__name__)

@app.route('/')
def home():
    return "IsatPhone Balance Check API - LIVE!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    iccid_msisdn = request.args.get('msisdn') or request.json.get('msisdn') if request.json else None
    
    if not iccid_msisdn:
        return jsonify({'error': 'ICCID/MSISDN required'}), 400
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # IBIS form submission
        form_data = {
            'ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol0': iccid_msisdn,
            '__CALLBACKID': 'ctl00_ContentPlaceHolder1_gvSIMCards',
            '__CALLBACKPARAM': f'PnlFilter%2CCallbackRowValues%7C0%7C{urllib.parse.quote(iccid_msisdn)}'
        }
        
        # POST to IBIS (from your Network tab)
        url = 'https://ibisglobalbeam.satcomhost.com/Default.aspx'
        response = session.post(url, data=form_data, timeout=15)
        
        # Parse results table
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract balance & expiry (EXACT selectors from your screenshot)
        balance_elem = soup.select_one('td.dxgv[align="right"]')
        expiry_elem = soup.select_one('td.dxgv[style*="border-right-width:0px"]')
        
        result = {
            'iccid_msisdn': iccid_msisdn,
            'balance': balance_elem.text.strip() if balance_elem else 'Not found',
            'expiry': expiry_elem.text.strip() if expiry_elem else 'Not found',
            'status': 'success'
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'IBIS scrape failed: {str(e)}'}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
