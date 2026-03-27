from flask import Flask, request, jsonify
import os
import requests  # ← ADD THIS

app = Flask(__name__)

@app.route('/')
def home():
    return "Balance Check API is running!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    # Get MSISDN/ICCID from query params or body
    if request.method == 'POST':
        msisdn = request.json.get('msisdn') if request.json else None
    else:
        msisdn = request.args.get('msisdn')
    
    if not msisdn:
        return jsonify({'error': 'MSISDN/ICCID required'}), 400
    
    # === REAL IBIS INTEGRATION (REPLACE THIS SECTION) ===
    try:
        # UPDATE THESE 4 LINES WITH YOUR IBIS DETAILS:
        ibis_response = requests.post(
            'https://YOUR_IBIS_ENDPOINT.co.za/balance',  # ← Your URL
            headers={
                'Authorization': 'Bearer YOUR_API_KEY_HERE',  # ← Your auth
                'Content-Type': 'application/json'
            },
            json={'msisdn': msisdn}  # ← Your request format
        )
        ibis_data = ibis_response.json()
        
        return jsonify({
            'msisdn': msisdn,
            'balance': ibis_data['balance'],           # ← Adjust field name
            'expiry': ibis_data['expiry_date'],        # ← Adjust field name
            'status': ibis_data.get('status', 'active')
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'IBIS API failed: {str(e)}'}), 502
    except KeyError as e:
        return jsonify({'error': f'Missing IBIS field: {str(e)}'}), 500
    
    # === TEMP DUMMY DATA (REMOVE AFTER IBIS WORKS) ===
    # return jsonify({
    #     'msisdn': msisdn,
    #     'balance': f'R{round(10 + (hash(msisdn) % 1000) / 100, 2)}',
    #     'expiry': '2026-12-31',
    #     'status': 'active'
    # })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

