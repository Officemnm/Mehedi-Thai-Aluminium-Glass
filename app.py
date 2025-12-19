import os, io, json
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mehedi_thai_2025_secure"

# ---- ফিক্সড ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# মেমোরি স্টোরেজ (ডেমো ডাটা)
data_store = {
    "customers": [
        {"n": "Walk-in Customer", "m": "01xxxxxxxxx"},
        {"n": "Rahim Uddin", "m": "01712345678"}
    ],
    "products": ["Thai Window 4\" (Silver)", "Thai Window 4\" (Bronze)", "5mm Clear Glass", "SS Grill Piece", "Sliding Door"]
}

# ---- ১. PDF জেনারেটর (তীর চিহ্ন ফিক্সড) ----
def generate_pdf(items_list, doc_type, c_name, c_mob, advance, note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # হেডার
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "MEHEDI THAI ALUMINUM & GLASS")
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(width/2, height - 65, "West Side Of The Khartoil Boro Mosjid, Satiash Road, Tongi, Gazipur, 1700.")
    c.setFont("Helvetica-Oblique", 10.5)
    c.drawCentredString(width/2, height - 82, "Modern design, durable materials & fast delivery with 100% guarantee.")

    # প্রোপাইটর
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656,  +880 1601-465130,  +880 1967-113830")
    
    # তারিখ ও নং
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার
    c.drawString(40, height - 160, f"Customer Name: {c_name}")
    c.drawString(40, height - 175, f"Mobile: {c_mob}")

    # টেবিল হেডার
    x_coords = [40, 310, 370, 420, 480, 555]
    curr_y = height - 195
    table_top = curr_y
    c.setFont("Helvetica-Bold", 9)
    headers = ["DESCRIPTION", "SQ.FT", "QTY", "RATE", "TOTAL"]
    for i, h in enumerate(headers):
        c.drawCentredString((x_coords[i]+x_coords[i+1])/2, curr_y-14, h)
    
    curr_y -= 20
    c.line(40, curr_y, 555, curr_y)

    grand_total = 0
    
    for i, item in enumerate(items_list):
        # সেইফটি চেক
        try: total_val = float(item['total'])
        except: total_val = 0
        grand_total += total_val
        
        text_y = curr_y - 18
        
        # SL & Title
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, text_y, f"{i+1}. {item['title']}")
        
        # Values
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, str(item['feet']) if float(item['feet'] or 0)>0 else "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, str(item['pcs']) if int(item['pcs'] or 0)>0 else "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, str(item['rate']) if float(item['rate'] or 0)>0 else "-")
        c.drawRightString(550, text_y, f"{total_val:.0f}")
        
        curr_y = text_y - 5
        
        if item.get('desc') and item['desc'].strip():
            # ---- তীর চিহ্ন ডিজাইন (FIXED ARROW) ----
            arrow_x = 65
            c.setLineWidth(0.8)
            c.line(arrow_x, curr_y, arrow_x, curr_y - 10) # খাড়া দাগ
            # তীরের মাথা (Head)
            c.line(arrow_x, curr_y - 10, arrow_x - 3, curr_y - 7)
            c.line(arrow_x, curr_y - 10, arrow_x + 3, curr_y - 7)
            
            c.setFont("Helvetica", 10.5)
            lines = item['desc'].split('\n')
            list_y = curr_y - 20
            start_l_y = list_y + 10
            max_w = 0
            
            for line in lines:
                c.drawString(70, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            
            # চিকন ব্র্যাকেট
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            # বাম [
            c.line(60, start_l_y, 55, start_l_y); c.line(55, start_l_y, 55, list_y+5); c.line(55, list_y+5, 60, list_y+5)
            # ডান ]
            rx = 70 + max_w + 10
            c.line(rx-5, start_l_y, rx, start_l_y); c.line(rx, start_l_y, rx, list_y+5); c.line(rx, list_y+5, rx-5, list_y+5)
            
            c.setStrokeColorRGB(0,0,0)
            curr_y = list_y - 5
        else:
            curr_y -= 10

    # টেবিল বর্ডার
    c.setLineWidth(1)
    for x in x_coords: c.line(x, table_top, x, curr_y)
    c.line(40, table_top, 555, table_top); c.line(40, curr_y, 555, curr_y)

    # হিসাব
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22); c.setFont("Helvetica-Bold", 10); c.drawString(405, summary_y+7, "Grand Total:"); c.drawRightString(550, summary_y+7, f"{grand_total:,.0f} Tk")
    
    if doc_type == "Invoice":
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Advance:"); c.drawRightString(550, summary_y+7, f"{advance:,.0f} Tk")
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Due:"); c.drawRightString(550, summary_y+7, f"{grand_total-advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y-10, 320, 35); c.drawString(45, summary_y+10, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y, note)

    c.line(40, 60, 160, 60); c.line(435, 60, 555, 60)
    c.drawString(45, 45, "Customer Signature"); c.drawRightString(550, 45, "Authorized Signature")
    
    c.save(); buffer.seek(0)
    return buffer

# ---- ২. HTML UI (Customer First Flow) ----
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        body { background: #f1f5f9; font-family: 'Segoe UI', sans-serif; }
        .sidebar { height: 100vh; background: #0f172a; color: white; position: fixed; width: 250px; }
        .sidebar a { color: #94a3b8; text-decoration: none; padding: 15px 25px; display: block; border-bottom: 1px solid #1e293b; }
        .sidebar a:hover { background: #1e293b; color: white; }
        .main { margin-left: 250px; padding: 30px; }
        .card { border: none; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border-radius: 8px; }
        .step-container { display: none; }
        .step-container.active { display: block; animation: fadeIn 0.4s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <div class="sidebar">
        <h4 class="text-center py-4 text-white">Mehedi Thai</h4>
        <a href="/dashboard">📊 Dashboard</a>
        <a href="/customers">👥 Customers</a>
        <a href="/products">📦 Products</a>
        <a href="/create/Invoice">🧾 Create Invoice</a>
        <a href="/create/Quotation">📄 Create Quotation</a>
        <a href="/logout" class="text-danger mt-5">🚪 Logout</a>
    </div>
    {% endif %}
    <div class="main">{% block content %}{% endblock %}</div>

    <script>
        // কাস্টমার ডাটাবেজ (Server থেকে আসবে)
        const customers = {{ customers_json | safe }}; 
        
        function checkCustomer() {
            const inputName = document.getElementById('cust_input').value;
            const found = customers.find(c => c.n === inputName);
            if(found) {
                document.getElementById('cust_mobile').value = found.m;
                document.getElementById('cust_status').innerHTML = '<span class="text-success">✔ Existing Customer Found</span>';
            } else {
                document.getElementById('cust_status').innerHTML = '<span class="text-primary">+ New Customer</span>';
            }
        }

        function startWizard() {
            const name = document.getElementById('cust_input').value;
            const mobile = document.getElementById('cust_mobile').value;
            
            if(!name || !mobile) { alert("Please enter Customer Name and Mobile."); return; }
            
            // ডাটা সেট করা
            document.getElementById('final_c_name').value = name;
            document.getElementById('final_c_mob').value = mobile;
            document.getElementById('display_c_name').innerText = name;
            document.getElementById('display_c_mob').innerText = mobile;

            // ভিউ চেঞ্জ
            document.getElementById('section_customer').classList.remove('active');
            document.getElementById('section_items').classList.add('active');
        }

        // আইটেম উইজার্ড লজিক
        let itemList = [];
        
        function showItemStep(id) {
            document.querySelectorAll('.wiz-step').forEach(el => el.style.display = 'none');
            document.getElementById(id).style.display = 'block';
        }

        function saveItem() {
            const title = document.getElementById('i_title').value;
            const desc = document.getElementById('i_desc').value;
            const feet = parseFloat(document.getElementById('i_feet').value) || 0;
            const pcs = parseInt(document.getElementById('i_pcs').value) || 0;
            const rate = parseFloat(document.getElementById('i_rate').value) || 0;
            const manual = parseFloat(document.getElementById('i_manual').value) || 0;

            if(!title) { alert("Title is required"); return; }
            if(feet==0 && pcs==0 && manual==0) { alert("Enter Measurement or Manual Total"); return; }

            let total = 0;
            if(rate > 0) total = (feet > 0 ? feet : pcs) * rate;
            else total = manual;

            itemList.push({title, desc, feet, pcs, rate, total});
            renderTable();
            
            // রিসেট
            document.getElementById('i_title').value='';
            document.getElementById('i_desc').value='';
            document.getElementById('i_feet').value='';
            document.getElementById('i_pcs').value='';
            document.getElementById('i_rate').value='';
            document.getElementById('i_manual').value='';
            
            showItemStep('step_1');
        }

        function renderTable() {
            let html = '';
            let gTotal = 0;
            itemList.forEach((it, idx) => {
                gTotal += it.total;
                html += `<tr><td>${idx+1}</td><td><b>${it.title}</b></td><td>${it.total.toFixed(0)}</td></tr>`;
            });
            document.getElementById('item_tbody').innerHTML = html;
            document.getElementById('g_total_disp').innerText = gTotal.toFixed(0);
            document.getElementById('hidden_json').value = JSON.stringify(itemList);
        }
    </script>
</body>
</html>
"""

# ---- ৩. রাউটস ----
@app.route('/')
def index(): return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == USER_LOGIN and request.form['pass'] == USER_PASS:
            session['logged_in'] = True; return redirect(url_for('dashboard'))
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="d-flex justify-content-center mt-5">
            <div class="card p-5" style="width: 400px;">
                <h3 class="text-center mb-4">Admin Login</h3>
                <form method="POST">
                    <input name="user" class="form-control mb-3" placeholder="Username" required>
                    <input name="pass" type="password" class="form-control mb-4" placeholder="Password" required>
                    <button class="btn btn-primary w-100">Login</button>
                </form>
            </div>
        </div>
    """), customers_json="[]")

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h2>Dashboard</h2>
        <div class="row g-4 mt-2">
            <div class="col-md-4"><div class="card p-4 bg-primary text-white"><h5>Products</h5><h2>{len(data_store['products'])}</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-success text-white"><h5>Customers</h5><h2>{len(data_store['customers'])}</h2></div></div>
        </div>
    """), customers_json="[]")

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            items = json.loads(request.form.get('items_data', '[]'))
            adv = 0
            if request.form.get('adv'): adv = float(request.form.get('adv'))
            
            pdf = generate_pdf(items, doc_type, request.form['c_name'], request.form['c_mob'], adv, request.form['note'])
            return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)
        except Exception as e: return f"Error: {e}"

    # ডাটা প্রিপারেশন
    cust_json = json.dumps(data_store['customers'])
    cust_opts = "".join([f"<option value='{c['n']}'>" for c in data_store['customers']])
    prod_opts = "".join([f"<option value='{p}'>" for p in data_store['products']])
    
    html_content = f"""
    <div id="section_customer" class="step-container active">
        <div class="card p-5 shadow-sm" style="max-width: 600px; margin: auto;">
            <h3 class="mb-4 text-center">Step 1: Select Customer</h3>
            
            <div class="mb-3">
                <label class="form-label">Customer Name</label>
                <input id="cust_input" class="form-control form-control-lg" list="c_list" oninput="checkCustomer()" placeholder="Search or type new name...">
                <datalist id="c_list">{cust_opts}</datalist>
                <div id="cust_status" class="form-text">Start typing to search...</div>
            </div>

            <div class="mb-4">
                <label class="form-label">Mobile Number</label>
                <input id="cust_mobile" class="form-control form-control-lg" placeholder="Enter mobile number">
            </div>

            <button onclick="startWizard()" class="btn btn-primary btn-lg w-100">Next: Add Items &rarr;</button>
        </div>
    </div>

    <div id="section_items" class="step-container">
        <div class="row">
            <div class="col-md-7">
                <div class="card p-4 border-primary">
                    <div class="d-flex justify-content-between mb-3">
                        <h5>Add New Item</h5>
                        <span class="badge bg-info text-dark">Item Wizard</span>
                    </div>

                    <div id="step_1" class="wiz-step">
                        <label>Product Title</label>
                        <input id="i_title" class="form-control mb-3" list="p_list" placeholder="Select product...">
                        <datalist id="p_list">{prod_opts}</datalist>
                        <button class="btn btn-primary w-100" onclick="showItemStep('step_2')">Next: Description</button>
                    </div>

                    <div id="step_2" class="wiz-step" style="display:none;">
                        <label>Description (Optional)</label>
                        <textarea id="i_desc" class="form-control mb-3" rows="3" placeholder="Enter details..."></textarea>
                        <div class="d-flex gap-2">
                            <button class="btn btn-secondary w-50" onclick="showItemStep('step_1')">Back</button>
                            <button class="btn btn-primary w-50" onclick="showItemStep('step_3')">Next: Price</button>
                        </div>
                    </div>

                    <div id="step_3" class="wiz-step" style="display:none;">
                        <div class="row g-2 mb-3">
                            <div class="col-4"><label>Sq.Ft</label><input id="i_feet" type="number" class="form-control"></div>
                            <div class="col-4"><label>Qty</label><input id="i_pcs" type="number" class="form-control"></div>
                            <div class="col-4"><label>Rate</label><input id="i_rate" type="number" class="form-control"></div>
                        </div>
                        <label>Manual Total (Optional)</label>
                        <input id="i_manual" type="number" class="form-control mb-3" placeholder="Use if rate is empty">
                        
                        <div class="d-flex gap-2">
                            <button class="btn btn-secondary w-50" onclick="showItemStep('step_2')">Back</button>
                            <button class="btn btn-success w-50" onclick="saveItem()">+ Add to Invoice</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="col-md-5">
                <div class="card p-4 h-100">
                    <h5>{doc_type} Summary</h5>
                    <div class="alert alert-light border">
                        <strong>Customer:</strong> <span id="display_c_name"></span><br>
                        <strong>Mobile:</strong> <span id="display_c_mob"></span>
                    </div>
                    
                    <div style="flex-grow: 1; overflow-y: auto; max-height: 300px;">
                        <table class="table table-sm">
                            <thead><tr><th>#</th><th>Item</th><th>Total</th></tr></thead>
                            <tbody id="item_tbody"></tbody>
                        </table>
                    </div>
                    
                    <h4 class="text-end border-top pt-2">Total: <span id="g_total_disp">0</span></h4>
                    
                    <form method="POST" class="mt-3">
                        <input type="hidden" name="c_name" id="final_c_name">
                        <input type="hidden" name="c_mob" id="final_c_mob">
                        <input type="hidden" name="items_data" id="hidden_json">
                        
                        {f'<input name="adv" type="number" class="form-control mb-2" placeholder="Advance Payment">' if doc_type == 'Invoice' else ''}
                        <input name="note" class="form-control mb-2" placeholder="Note (Warranty/Conditions)">
                        
                        <button class="btn btn-dark w-100 py-2">Download PDF</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', html_content), customers_json=cust_json)

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST': data_store['customers'].append({'n': request.form['n'], 'm': request.form['m']})
    # Simple list view
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', "<h3>Customers</h3><form method='post'><input name='n' placeholder='Name'><input name='m' placeholder='Mobile'><button>Add</button></form>"), customers_json="[]")

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST': data_store['products'].append(request.form['p'])
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', "<h3>Products</h3><form method='post'><input name='p'><button>Add</button></form>"), customers_json="[]")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

