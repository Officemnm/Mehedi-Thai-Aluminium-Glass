import os, io, json
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mehedi_thai_final_2025"

# ---- ফিক্সড ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# মেমোরি স্টোরেজ (ডিফল্ট কিছু ডাটা সহ)
data_store = {
    "customers": [{"n": "Walk-in Customer", "m": "01xxxxxxxxx"}],
    "products": ["Thai Window 4\" (Silver)", "Thai Window 4\" (Bronze)", "5mm Clear Glass", "5mm Blue Mercury Glass", "Sliding Door Frame", "SS Grill Piece"]
}

# ---- হেল্পার ফাংশন (এরর ফিক্স করার জন্য) ----
def safe_float(val):
    """খালি স্ট্রিং বা ভুল ডাটা আসলে ০ রিটার্ন করবে, ক্র্যাশ করবে না"""
    if not val: return 0.0
    try:
        return float(val)
    except ValueError:
        return 0.0

def safe_int(val):
    if not val: return 0
    try:
        return int(val)
    except ValueError:
        return 0

# ---- ১. PDF জেনারেটর (Fixed Design) ----
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
        t_val = safe_float(item['total'])
        grand_total += t_val
        text_y = curr_y - 18
        
        # SL No with Title
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, text_y, f"{i+1}. {item['title']}")
        
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, str(item['feet']) if safe_float(item['feet']) > 0 else "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, str(item['pcs']) if safe_int(item['pcs']) > 0 else "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, str(item['rate']) if safe_float(item['rate']) > 0 else "-")
        c.drawRightString(550, text_y, f"{t_val:.0f}")
        
        curr_y = text_y - 5
        
        if item.get('desc') and item['desc'].strip():
            # তীর এবং ব্র্যাকেট ডিজাইন
            c.setLineWidth(0.6); c.line(65, curr_y, 65, curr_y-8) 
            c.setFont("Helvetica", 10.5)
            lines = item['desc'].split('\n')
            list_y = curr_y - 18
            start_l_y = list_y + 10
            max_w = 0
            
            for line in lines:
                c.drawString(70, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            
            # ব্র্যাকেট আঁকা
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            # বাম ব্র্যাকেট [
            c.line(60, start_l_y, 55, start_l_y); c.line(55, start_l_y, 55, list_y+5); c.line(55, list_y+5, 60, list_y+5)
            # ডান ব্র্যাকেট ]
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

    # হিসাব বক্স
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22); c.setFont("Helvetica-Bold", 10)
    c.drawString(405, summary_y+7, "Grand Total:"); c.drawRightString(550, summary_y+7, f"{grand_total:,.0f} Tk")
    
    if doc_type == "Invoice":
        summary_y -= 22; c.rect(400, summary_y, 155, 22)
        c.drawString(405, summary_y+7, "Advance:"); c.drawRightString(550, summary_y+7, f"{advance:,.0f} Tk")
        summary_y -= 22; c.rect(400, summary_y, 155, 22)
        c.drawString(405, summary_y+7, "Due:"); c.drawRightString(550, summary_y+7, f"{grand_total-advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y-10, 320, 35)
        c.drawString(45, summary_y+10, "Note:")
        c.setFont("Helvetica", 9); c.drawString(45, summary_y, note)

    c.line(40, 60, 160, 60); c.line(435, 60, 555, 60)
    c.drawString(45, 45, "Customer Signature"); c.drawRightString(550, 45, "Authorized Signature")
    
    c.save(); buffer.seek(0)
    return buffer

# ---- ২. HTML UI (উইজার্ড স্টাইল) ----
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai | Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; font-family: 'Segoe UI', sans-serif; }
        .sidebar { height: 100vh; background: #1e293b; color: white; position: fixed; width: 250px; z-index: 100; }
        .sidebar a { color: #cbd5e1; text-decoration: none; padding: 15px 25px; display: block; border-bottom: 1px solid #334155; }
        .sidebar a:hover { background: #334155; color: white; }
        .main-content { margin-left: 250px; padding: 30px; }
        .card { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .step { display: none; animation: fadeIn 0.3s; }
        .step.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .main-content { margin-left: 0; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <div class="sidebar">
        <h4 class="text-center py-4 bg-dark m-0">Mehedi Thai</h4>
        <a href="/dashboard">📊 Dashboard</a>
        <a href="/customers">👥 Customers</a>
        <a href="/products">📦 Products</a>
        <a href="/create/Invoice">🧾 Create Invoice</a>
        <a href="/create/Quotation">📄 Create Quotation</a>
        <a href="/logout" class="text-danger mt-4">🚪 Logout</a>
    </div>
    {% endif %}
    <div class="main-content">{% block content %}{% endblock %}</div>
    
    <script>
        // জাভাস্ক্রিপ্ট লজিক
        let items = [];

        function showStep(stepId) {
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            document.getElementById(stepId).classList.add('active');
        }

        function addItem() {
            const title = document.getElementById('item_title').value;
            const desc = document.getElementById('item_desc').value;
            const feet = parseFloat(document.getElementById('item_feet').value) || 0;
            const pcs = parseInt(document.getElementById('item_pcs').value) || 0;
            const rate = parseFloat(document.getElementById('item_rate').value) || 0;
            const manual = parseFloat(document.getElementById('item_manual').value) || 0;

            if(!title) { alert("Title is required!"); return; }
            if(feet === 0 && pcs === 0 && manual === 0) { alert("Please enter Sq.Ft, Qty OR Manual Total."); return; }

            let total = 0;
            if(rate > 0) {
                total = (feet > 0 ? feet : pcs) * rate;
            } else {
                total = manual;
            }

            items.push({title, desc, feet, pcs, rate, total});
            updateTable();
            
            // রিসেট এবং প্রথম ধাপে ফেরা
            document.getElementById('item_title').value = '';
            document.getElementById('item_desc').value = '';
            document.getElementById('item_feet').value = '';
            document.getElementById('item_pcs').value = '';
            document.getElementById('item_rate').value = '';
            document.getElementById('item_manual').value = '';
            showStep('step1');
        }

        function updateTable() {
            const tbody = document.getElementById('item_table_body');
            tbody.innerHTML = "";
            let gTotal = 0;
            items.forEach((it, idx) => {
                gTotal += it.total;
                tbody.innerHTML += `<tr>
                    <td>${idx+1}</td>
                    <td><b>${it.title}</b><br><small>${it.desc}</small></td>
                    <td>${it.feet}</td>
                    <td>${it.pcs}</td>
                    <td>${it.total.toFixed(2)}</td>
                </tr>`;
            });
            document.getElementById('grand_display').innerText = gTotal.toFixed(2);
            document.getElementById('hidden_items').value = JSON.stringify(items);
        }
    </script>
</body>
</html>
"""

# ---- ৩. রাউটস (Routes) ----
@app.route('/')
def index(): return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == USER_LOGIN and request.form['pass'] == USER_PASS:
            session['logged_in'] = True; return redirect(url_for('dashboard'))
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="d-flex justify-content-center align-items-center" style="height: 80vh;">
            <div class="card p-5 shadow" style="width: 400px;">
                <h3 class="text-center mb-4">Admin Login</h3>
                <form method="POST">
                    <input name="user" class="form-control mb-3" placeholder="Username" required>
                    <input name="pass" type="password" class="form-control mb-4" placeholder="Password" required>
                    <button class="btn btn-primary w-100">Login</button>
                </form>
            </div>
        </div>
    """))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h2>Admin Dashboard</h2>
        <div class="row g-4 mt-2">
            <div class="col-md-4"><div class="card p-4 bg-primary text-white"><h5>Products</h5><h2>{len(data_store['products'])}</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-success text-white"><h5>Customers</h5><h2>{len(data_store['customers'])}</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-secondary text-white"><h5>System Status</h5><h2>Active</h2></div></div>
        </div>
    """))

@app.route('/products', methods=['GET', 'POST'])
def products():
    if request.method == 'POST': data_store['products'].append(request.form['p'])
    p_list = "".join([f"<li class='list-group-item d-flex justify-content-between'>{x}</li>" for x in data_store['products']])
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h3>Manage Products</h3>
        <form method='POST' class='d-flex gap-2 mb-4'><input name='p' class='form-control' placeholder='New Product Title' required><button class='btn btn-success'>Add</button></form>
        <ul class='list-group'>{p_list}</ul>
    """))

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if request.method == 'POST': data_store['customers'].append({'n': request.form['n'], 'm': request.form['m']})
    c_list = "".join([f"<li class='list-group-item'>{x['n']} ({x['m']})</li>" for x in data_store['customers']])
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h3>Manage Customers</h3>
        <form method='POST' class='mb-4'><div class='input-group'><input name='n' class='form-control' placeholder='Name'><input name='m' class='form-control' placeholder='Mobile'><button class='btn btn-success'>Add</button></div></form>
        <ul class='list-group'>{c_list}</ul>
    """))

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        # JSON ডাটা লোড এবং সেফটি চেক
        try:
            items_list = json.loads(request.form.get('items_data', '[]'))
            advance = safe_float(request.form.get('adv'))
            
            pdf = generate_pdf(items_list, doc_type, request.form['c_name'], request.form['c_mob'], advance, request.form['note'])
            return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)
        except Exception as e:
            return f"Error creating PDF: {str(e)}"

    c_opts = "".join([f"<option value='{c['n']}'>" for c in data_store['customers']])
    p_opts = "".join([f"<option value='{p}'>" for p in data_store['products']])
    
    form_html = f"""
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h3>Generate {doc_type}</h3>
            <span class="badge bg-info text-dark">Wizard Mode</span>
        </div>

        <div class="card p-4 shadow-sm mb-4 border-primary">
            
            <div id="step1" class="step active">
                <h5 class="mb-3 text-primary">Step 1: Select Item</h5>
                <label>Product Title</label>
                <input id="item_title" class="form-control form-control-lg mb-3" list="p_list" placeholder="Type or select product...">
                <datalist id="p_list">{p_opts}</datalist>
                <button type="button" class="btn btn-primary" onclick="showStep('step2')">Next: Details ></button>
            </div>

            <div id="step2" class="step">
                <h5 class="mb-3 text-primary">Step 2: Description (Optional)</h5>
                <textarea id="item_desc" class="form-control mb-3" rows="3" placeholder="Enter size details, glass type, color etc..."></textarea>
                <button type="button" class="btn btn-secondary" onclick="showStep('step1')">< Back</button>
                <button type="button" class="btn btn-primary" onclick="showStep('step3')">Next: Measurements ></button>
            </div>

            <div id="step3" class="step">
                <h5 class="mb-3 text-primary">Step 3: Measurement & Price</h5>
                <div class="row g-3 mb-3">
                    <div class="col-md-4"><label>Sq.Ft</label><input id="item_feet" type="number" step="any" class="form-control"></div>
                    <div class="col-md-4"><label>Quantity (Pcs)</label><input id="item_pcs" type="number" class="form-control"></div>
                    <div class="col-md-4"><label>Rate (per Ft/Pc)</label><input id="item_rate" type="number" step="any" class="form-control"></div>
                </div>
                <div class="mb-4">
                    <label>Manual Total (Use this if Rate is empty)</label>
                    <input id="item_manual" type="number" step="any" class="form-control bg-light">
                </div>
                <button type="button" class="btn btn-secondary" onclick="showStep('step2')">< Back</button>
                <button type="button" class="btn btn-success px-4" onclick="addItem()">+ Add to List</button>
            </div>
        </div>

        <form method="POST" class="card p-4">
            <h5 class="mb-3">Finalize {doc_type}</h5>
            <div class="row mb-3">
                <div class="col-md-6"><label>Customer Name</label><input name="c_name" class="form-control" list="c_list" required><datalist id="c_list">{c_opts}</datalist></div>
                <div class="col-md-6"><label>Mobile No</label><input name="c_mob" class="form-control" required></div>
            </div>

            <table class="table table-bordered table-striped">
                <thead><tr class="table-dark"><th>SL</th><th>Item</th><th>Ft</th><th>Qty</th><th>Total</th></tr></thead>
                <tbody id="item_table_body"></tbody>
                <tfoot><tr><th colspan="4" class="text-end">Approx. Total:</th><th id="grand_display">0.00</th></tr></tfoot>
            </table>

            <input type="hidden" name="items_data" id="hidden_items">
            
            {f'<label>Advance Payment</label><input name="adv" type="number" class="form-control mb-3" placeholder="0">' if doc_type == 'Invoice' else ''}
            
            <label>Final Note</label>
            <input name="note" class="form-control mb-3" placeholder="Any warranty or conditions...">
            
            <button type="submit" class="btn btn-dark btn-lg w-100">Download PDF</button>
        </form>
    """
    return render_template_string(LAYOUT.replace('{% block content %}{% endblock %}', form_html))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

