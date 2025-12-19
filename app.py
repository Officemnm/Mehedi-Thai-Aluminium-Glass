import os, io
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mehedi_thai_wizard_2025"

# ---- ফিক্সড ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# মেমোরি স্টোরেজ
data_store = {
    "customers": [],
    "products": ["Thai Window 4\" (Silver)", "Thai Window 4\" (Bronze)", "5mm Clear Glass", "5mm Blue Mercury Glass", "Sliding Door Frame", "SS Grill Piece"]
}

# ---- ১. PDF জেনারেটর (Fixed Design) ----
def generate_pdf(items_list, doc_type, c_name, c_mob, advance, note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # হেডার ও মার্কেটিং
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "MEHEDI THAI ALUMINUM & GLASS")
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(width/2, height - 65, "West Side Of The Khartoil Boro Mosjid, Satiash Road, Tongi, Gazipur, 1700.")
    c.setFont("Helvetica-Oblique", 10.5)
    c.drawCentredString(width/2, height - 82, "Modern design, durable materials & fast delivery with 100% guarantee.")

    # প্রোপাইটর তথ্য
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656,  +880 1601-465130,  +880 1967-113830")
    
    # তারিখ ও নং
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার তথ্য
    c.drawString(40, height - 160, f"Customer Name: {c_name}")
    c.drawString(40, height - 175, f"Mobile: {c_mob}")

    # টেবিল
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
        t_val = float(item['total'])
        grand_total += t_val
        text_y = curr_y - 18
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, text_y, f"{i+1}. {item['title']}")
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, item['feet'] or "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, item['pcs'] or "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, item['rate'] or "-")
        c.drawRightString(550, text_y, f"{t_val:.0f}")
        
        curr_y = text_y - 5
        if item['desc']:
            c.setLineWidth(0.6); c.line(65, curr_y, 65, curr_y-8) # তীর
            c.setFont("Helvetica", 10.5)
            lines = item['desc'].split('\n')
            list_y = curr_y - 18; start_l_y = list_y + 10; max_w = 0
            for line in lines:
                c.drawString(70, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            c.line(60, start_l_y, 55, start_l_y); c.line(55, start_l_y, 55, list_y+5); c.line(55, list_y+5, 60, list_y+5) # [
            rx = 70 + max_w + 10
            c.line(rx-5, start_l_y, rx, start_l_y); c.line(rx, start_l_y, rx, list_y+5); c.line(rx, list_y+5, rx-5, list_y+5) # ]
            c.setStrokeColorRGB(0,0,0); curr_y = list_y - 5
        else: curr_y -= 10

    # দাগগুলো টানা
    c.setLineWidth(1)
    for x in x_coords: c.line(x, table_top, x, curr_y)
    c.line(40, table_top, 555, table_top); c.line(40, curr_y, 555, curr_y)

    # হিসাব বক্স
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22); c.setFont("Helvetica-Bold", 10); c.drawString(405, summary_y+7, "Grand Total:"); c.drawRightString(550, summary_y+7, f"{grand_total:,.0f} Tk")
    if doc_type == "Invoice":
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Advance:"); c.drawRightString(550, summary_y+7, f"{advance:,.0f} Tk")
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Due:"); c.drawRightString(550, summary_y+7, f"{grand_total-advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y-10, 320, 35); c.drawString(45, summary_y+10, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y, note)

    c.line(40, 60, 160, 60); c.line(435, 60, 555, 60); c.drawString(45, 45, "Customer Signature"); c.drawRightString(550, 45, "Authorized Signature")
    c.save(); buffer.seek(0)
    return buffer

# ---- ২. HTML UI ডিজাইন ----
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai | Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; font-family: 'Inter', sans-serif; }
        .sidebar { height: 100vh; background: #1a202c; color: white; position: fixed; width: 250px; }
        .sidebar a { color: #a0aec0; text-decoration: none; padding: 15px 25px; display: block; }
        .sidebar a:hover { background: #2d3748; color: white; }
        .main-content { margin-left: 250px; padding: 40px; }
        .card { border-radius: 12px; border: none; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .step { display: none; } .step.active { display: block; }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .main-content { margin-left: 0; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <div class="sidebar">
        <h3 class="text-center p-4">Mehedi Thai</h3><hr>
        <a href="/dashboard">Dashboard</a>
        <a href="/customers">Manage Customers</a>
        <a href="/products">Manage Products</a>
        <a href="/create/Invoice">Create Invoice</a>
        <a href="/create/Quotation">Create Quotation</a>
        <a href="/logout" class="text-danger mt-5">Logout</a>
    </div>
    {% endif %}
    <div class="main-content">{% block content %}{% endblock %}</div>
    
    <script>
        let items = [];
        function showStep(stepId) {
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            document.getElementById(stepId).classList.add('active');
        }

        function addItem() {
            const title = document.getElementById('item_title').value;
            const desc = document.getElementById('item_desc').value;
            const feet = document.getElementById('item_feet').value || 0;
            const pcs = document.getElementById('item_pcs').value || 0;
            const rate = document.getElementById('item_rate').value || 0;
            const manual = document.getElementById('item_manual').value || 0;

            if(!title) { alert("Title is required!"); return; }
            if(feet == 0 && pcs == 0) { alert("Feet or Pcs is required!"); return; }

            let total = 0;
            if(rate > 0) { total = (feet > 0 ? feet : pcs) * rate; }
            else { total = manual; }

            items.push({title, desc, feet, pcs, rate, total});
            updateTable();
            // Reset and go back
            document.getElementById('item_form').reset();
            showStep('step1');
        }

        function updateTable() {
            const tbody = document.getElementById('item_table_body');
            tbody.innerHTML = "";
            items.forEach((it, idx) => {
                tbody.innerHTML += `<tr><td>${idx+1}</td><td>${it.title}</td><td>${it.feet}</td><td>${it.pcs}</td><td>${it.total} Tk</td></tr>`;
            });
            document.getElementById('hidden_items').value = JSON.stringify(items);
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
                <h2 class="text-center mb-4">Admin Login</h2>
                <form method="POST">
                    <input name="user" class="form-control mb-3" placeholder="Username" required>
                    <input name="pass" type="password" class="form-control mb-4" placeholder="Password" required>
                    <button class="btn btn-primary w-100 py-2">Login</button>
                </form>
            </div>
        </div>
    """))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
        <h2>Dashboard Status</h2>
        <div class="row g-4 mt-2">
            <div class="col-md-4"><div class="card p-4 bg-primary text-white"><h5>Live Sales</h5><h2>0 Tk</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-white"><h5>Items Set</h5><h2>6</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-white"><h5>Quotations</h5><h2>0</h2></div></div>
        </div>
    """))

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST': data_store['products'].append(request.form['p'])
    p_list = "".join([f"<li class='list-group-item'>{x}</li>" for x in data_store['products']])
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"<h3>Manage Products</h3><form method='POST' class='d-flex gap-2 mb-3'><input name='p' class='form-control' required><button class='btn btn-success'>Add</button></form><ul class='list-group'>{p_list}</ul>"))

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST': data_store['customers'].append({'n': request.form['n'], 'm': request.form['m']})
    c_list = "".join([f"<li class='list-group-item'>{x['n']} - {x['m']}</li>" for x in data_store['customers']])
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"<h3>Manage Customers</h3><form method='POST' class='mb-3'><input name='n' class='form-control mb-2' placeholder='Name'><input name='m' class='form-control mb-2' placeholder='Mobile'><button class='btn btn-success'>Add</button></form><ul class='list-group'>{c_list}</ul>"))

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        import json
        items_list = json.loads(request.form['items_data'])
        pdf = generate_pdf(items_list, doc_type, request.form['c_name'], request.form['c_mob'], float(request.form.get('adv', 0)), request.form['note'])
        return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)

    c_opts = "".join([f"<option value='{c['n']}'>" for c in data_store['customers']])
    p_opts = "".join([f"<option value='{p}'>" for p in data_store['products']])
    
    form_html = f"""
        <h3 class="mb-4">Generate {doc_type}</h3>
        <form id="item_form" class="card p-4 shadow-sm mb-4">
            <div id="step1" class="step active">
                <label class="h5 mb-3">Step 1: Select Product/Title</label>
                <input id="item_title" class="form-control form-control-lg mb-3" list="p_list" placeholder="Start typing product name...">
                <datalist id="p_list">{p_opts}</datalist>
                <button type="button" class="btn btn-primary btn-lg" onclick="showStep('step2')">Next: Description</button>
            </div>

            <div id="step2" class="step">
                <label class="h5 mb-3">Step 2: Description (Optional)</label>
                <textarea id="item_desc" class="form-control mb-3" rows="3" placeholder="Enter glass type, thickness, or colors..."></textarea>
                <button type="button" class="btn btn-secondary btn-lg" onclick="showStep('step1')">Back</button>
                <button type="button" class="btn btn-primary btn-lg" onclick="showStep('step3')">Next: Measurement</button>
            </div>

            <div id="step3" class="step">
                <label class="h5 mb-3">Step 3: Measurement & Price</label>
                <div class="row g-3 mb-3">
                    <div class="col-md-4"><label>Sq.Ft</label><input id="item_feet" type="number" step="any" class="form-control"></div>
                    <div class="col-md-4"><label>Quantity (Pcs)</label><input id="item_pcs" type="number" class="form-control"></div>
                    <div class="col-md-4"><label>Rate</label><input id="item_rate" type="number" step="any" class="form-control"></div>
                </div>
                <div class="mb-4"><label>Manual Total (If rate is skipped)</label><input id="item_manual" type="number" step="any" class="form-control"></div>
                <button type="button" class="btn btn-secondary btn-lg" onclick="showStep('step2')">Back</button>
                <button type="button" class="btn btn-success btn-lg" onclick="addItem()">Finish & Add Item</button>
            </div>
        </form>

        <form method="POST" class="card p-4">
            <h5 class="mb-3">Customer & Final Summary</h5>
            <div class="row mb-3">
                <div class="col-md-6"><input name="c_name" class="form-control" list="c_list" placeholder="Customer Name" required><datalist id="c_list">{c_opts}</datalist></div>
                <div class="col-md-6"><input name="c_mob" class="form-control" placeholder="Customer Mobile" required></div>
            </div>
            <table class="table table-bordered mb-3">
                <thead class="bg-light"><tr><th>SL</th><th>Item</th><th>Ft</th><th>Qty</th><th>Total</th></tr></thead>
                <tbody id="item_table_body"></tbody>
            </table>
            <input type="hidden" name="items_data" id="hidden_items">
            {f'<input name="adv" class="form-control mb-3" placeholder="Advance Payment">' if doc_type == 'Invoice' else ''}
            <input name="note" class="form-control mb-3" placeholder="Final Note (If any)">
            <button type="submit" class="btn btn-primary btn-lg w-100">Download {doc_type} PDF</button>
        </form>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', form_html))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

