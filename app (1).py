from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- IBIS config ---
IBIS_BASE = "https://ibisglobalbeam.satcomhost.com"
IBIS_LOGIN = f"{IBIS_BASE}/Account/Login?ReturnUrl=%2F"
SIMCARDS_SIMPLE = f"{IBIS_BASE}/SimcardsSimple.aspx"

# In production, store these in Render env vars
USERNAME = "your-ibis-username"
PASSWORD = "your-ibis-password"


# --- Login helper ---
def login_and_get_session():
    session = requests.Session()
    # Step 1: get login page and grab hidden fields
    resp = session.get(IBIS_LOGIN)
    soup = BeautifulSoup(resp.content, "html.parser")

    hidden_inputs = {}
    for inp in soup.find_all("input", type="hidden"):
        if inp.get("name"):
            hidden_inputs[inp.get("name")] = inp.get("value")

    data = {
        **hidden_inputs,
        "Username": USERNAME,
        "Password": PASSWORD,
        "LoginButton": "Log in",
    }

    resp = session.post(IBIS_LOGIN, data=data)
    if resp.status_code != 200:
        raise Exception("Login failed")

    return session


# --- BALANCE SCRAPING FUNCTION ---
def get_balance_from_ibis(session, query_number):
    # 1. Go to SimcardsSimple.aspx
    resp = session.get(SIMCARDS_SIMPLE)
    soup = BeautifulSoup(resp.content, "html.parser")

    # 2. Decide which field to use
    if query_number.startswith("89"):
        field_name = "ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol0"
    elif query_number.startswith("870"):
        field_name = "ctl00$ContentPlaceHolder1$gvSIMCards$DXFREditorcol3"
    else:
        raise Exception("Number must be ICCID (89...) or MSISDN (870...)")

    inp = soup.find("input", {"name": field_name})
    if not inp:
        raise Exception("ICCID/MSISDN input not found")

    # 3. Find the green tick (Apply filter) image
    tick_img = soup.find("img", {"id": "ctl00_ContentPlaceHolder1_gvSIMCards_DXCBtn0Img"})
    if not tick_img:
        raise Exception("Green tick (Apply filter) not found")

    # 4. Find the corresponding submit button
    filter_btn = soup.find("input", value="Apply filter")
    if not filter_btn:
        filter_btn = soup.find("input", onclick=lambda x: x and "ApplyFilter" in x)

    if not filter_btn:
        raise Exception("Apply filter button not found")

    # 5. Build form data
    data = {field_name: query_number}

    # Add any hidden fields in the form
    form = tick_img.find_parent("form") or soup.find("form")
    if form:
        for hidden in form.find_all("input", type="hidden"):
            if hidden.get("name"):
                data[hidden.get("name")] = hidden.get("value")

    # 6. Submit the search (click green tick)
    resp = session.post(SIMCARDS_SIMPLE, data=data)
    soup = BeautifulSoup(resp.content, "html.parser")

    # 7. Find the SIM cards table
    table = soup.find("table", {"id": "ctl00_ContentPlaceHolder1_gvSIMCards"})
    if not table:
        table = soup.find("table", class_="dxgvTable")

    if not table:
        raise Exception("SIM cards table not found")

    # 8. Pick the first data row
    tbody = table.find("tbody") or table
    rows = tbody.find_all("tr", {"class": None})  # skip header rows

    if len(rows) == 0:
        raise Exception("No SIM card rows found (wrong number?)")
    if len(rows) > 1:
        # Use first row if multiple (your normal case is one row)
        pass

    row = rows[0]
    cells = row.find_all("td")

    if len(cells) < 2:
        raise Exception("Not enough columns in table row")

    # 9. Assume last two columns:
    #   second‑to‑last = Prepay (balance units)
    #   last         = Balance (expiry date)
    prepay_cell = cells[-2]
    balance_cell = cells[-1]

    balance_text = prepay_cell.get_text(strip=True)
    expiry_text = balance_cell.get_text(strip=True)

    return balance_text, expiry_text


# --- API endpoint ---
@app.route("/check-balance", methods=["POST"])
def check_balance():
    data = request.get_json()
    number = data.get("number")

    if not number:
        return jsonify({"error": "Number required"}), 400

    try:
        session = login_and_get_session()
        balance, expiry = get_balance_from_ibis(session, number)

        return jsonify({
            "balance": balance,
            "expiry": expiry
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)
