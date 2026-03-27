from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Balance Check API is running!"

@app.route('/check-balance', methods=['GET', 'POST'])
def check_balance():
    # Get MSISDN/ICCID from query params (GET) or JSON body (POST)
    if request.method == 'POST':
        msisdn = request.json.get('msisdn') if request.json else None
    else:
        msisdn = request.args.get('msisdn')
    
    if not msisdn:
        return jsonify({'error': 'MSISDN/ICCID required'}), 400
    
    # TODO: Replace with your actual IBIS API call
    # For now, returns dummy data so you can test the widget
    return jsonify({
        'msisdn': msisdn,
        'balance': f'R{round(10 + (hash(msisdn) % 1000) / 100, 2)}',
        'expiry': '2026-12-31',
        'status': 'active'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # CRITICAL FOR RENDER: Bind to 0.0.0.0 and use PORT env var
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
