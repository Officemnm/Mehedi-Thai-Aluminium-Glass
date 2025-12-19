import os
import io
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mehedi_thai_ultimate_key"

# ---- ফিক্সড এবং মেমরি ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# ডাটাবেজ ছাড়া মেমরিতে ডাটা রাখার জন্য (রেন্ডার রিস্টার্ট দিলে রিসেট হবে)
data_store = {
    "customers": [],
    "products": ["Thai Window", "Sliding Door", "Mercury Glass", "SS Grill", "Netting"]
}

# ---- ১. প্রফেশনাল PDF ডিজাইন (FIXED DESIGN) ----
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
    c.drawCentredString(width/2, height - 82, "Expert in Thai Aluminum & Glass works with 100% guarantee by skilled technicians.")

    # প্রোপাইটর এবং মোবাইল (পাশাপাশি - ফিক্সড)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656,  +880 1601-465130,  +880 1967-113830")
    
    # তারিখ ও নম্বর
    curr_date = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {curr_date}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.setLineWidth(0.8)
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার তথ্য
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, height - 160, f"Customer Name: {c_name}")
    c.drawString(40, height - 175, f"Mobile: {c_mob}")

    # টেবিল কলাম কনফিগারেশন
    x_coords = [40, 310, 370, 420, 480, 555]
    curr_y = height - 195
    table_start_y = curr_y

    # হেডার টেক্সট (Centered)
    c.setFont("Helvetica-Bold", 9)
    headers = ["DESCRIPTION", "SQ.FT", "QTY", "RATE", "TOTAL"]
    for i, h in enumerate(headers):
        c.drawCentredString((x_coords[i]+x_coords[i+1])/2, curr_y - 14, h)
    
    curr_y -= 20
    c.setLineWidth(1)
    c.line(40, curr_y, 555, curr_y)

    grand_total = 0
    # আইটেম লুপ (মাল্টিপল আইটেম)
    for i, item in enumerate(items_list):
        t_val = float(item['total'])
        grand_total += t_val
        text_y = curr_y - 15
        
        # SL নং টাইটেলের সাথে
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x_coords[0] + 5, text_y, f"{i+1}. {item['title']}")
        
        # মাপ ও হিসাব
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, item['feet'] if float(item['feet'] or 0) > 0 else "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, item['pcs'] if int(item['pcs'] or 0) > 0 else "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, item['rate'] if float(item['rate'] or 0) > 0 else "-")
        c.drawRightString(x_coords[5] - 5, text_y, f"{t_val:.0f}")
        
        curr_y = text_y - 5
        # বিবরণ (ব্র্যাকেট ও তীর)
        if item['desc']:
            c.setLineWidth(0.6)
            # তীর চিহ্ন
            c.line(x_coords[0]+25, curr_y, x_coords[0]+25, curr_y-8)
            c.line(x_coords[0]+25, curr_y-8, x_coords[0]+22, curr_y-5)
            c.line(x_coords[0]+25, curr_y-8, x_coords[0]+28, curr_y-5)
            
            c.setFont("Helvetica", 10.5)
            desc_lines = item['desc'].split('\n')
            list_y = curr_y - 18
            start_l_y = list_y + 10
            max_w = 0
            for line in desc_lines:
                c.drawString(x_coords[0] + 20, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            
            # চিকন ব্র্যাকেট (0.3)
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            # Left [
            c.line(x_coords[0]+12, start_l_y, x_coords[0]+8, start_l_y)
            c.line(x_coords[0]+8, start_l_y, x_coords[0]+8, list_y+5)
            c.line(x_coords[0]+8, list_y+5, x_coords[0]+12, list_y+5)
            # Right ]
            rx = x_coords[0] + 20 + max_w + 8
            c.line(rx-4, start_l_y, rx, start_l_y)
            c.line(rx, start_l_y, rx, list_y+5)
            c.line(rx, list_y+5, rx-4, list_y+5)
            
            c.setStrokeColorRGB(0, 0, 0)
            curr_y = list_y - 5
        else:
            curr_y -= 10

    # টেবিলের খাড়া দাগ
    c.setLineWidth(1)
    for x in x_coords: c.line(x, table_start_y, x, curr_y)
    c.line(x_coords[0], table_start_y, x_coords[-1], table_start_y)
    c.line(x_coords[0], curr_y, x_coords[-1], curr_y)

    # টোটাল সেকশন
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22); c.setFont("Helvetica-Bold", 10)
    c.drawString(405, summary_y + 7, "Grand Total:"); c.drawRightString(550, summary_y + 7, f"{grand_total:,.0f} Tk")
    
    if doc_type == "Invoice":
        summary_y -= 22; c.rect(400, summary_y, 155, 22)
        c.drawString(405, summary_y + 7, "Advance Paid:"); c.drawRightString(550, summary_y + 7, f"{advance:,.0f} Tk")
        summary_y -= 22; c.rect(400, summary_y, 155, 22)
        c.drawString(405, summary_y + 7, "Due Amount:"); c.drawRightString(550, summary_y + 7, f"{grand_total - advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y, 320, 40); c.setFont("Helvetica-Bold", 9)
        c.drawString(45, summary_y + 25, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y + 10, note)

    # সাক্ষর
    c.setLineWidth(0.8)
    c.line(40, 60, 160, 60); c.drawString(45, 45, "Customer Signature")
    c.line(435, 60, 555, 60); c.drawRightString(550, 45, "Authorized Signature")
    
    c.save(); buffer.seek(0)
    return buffer

# ---- ২. ফ্রন্টএন্ড UI (HTML) ----
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai | Professional Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; }
        .sidebar { height: 100vh; background: #2c3e50; color: white; position: fixed; width: 250px; z-index: 1000; }
        .sidebar a { color: #bdc3c7; text-decoration: none; padding: 15px 25px; display: block; font-weight: 500; }
        .sidebar a:hover, .sidebar a.active { background: #34495e; color: white; border-left: 5px solid #3498db; }
        .main { margin-left: 250px; padding: 40px; }
        .card { border: none; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }
        .stat-card { background: white; padding: 25px; border-radius: 15px; text-align: center; }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .main { margin-left: 0; } }
    </style>
</head>
<body>
    {% if session.get('logged_in') %}
    <div class="sidebar">
        <h3 class="text-center py-4">Mehedi Thai</h3>
        <a href="/dashboard">Dashboard</a>
        <a href="/customers">Customers</a>
        <a href="/products">Products</a>
        <a href="/create/Invoice">Create Invoice</a>
        <a href="/create/Quotation">Create Quotation</a>
        <a href="/logout" class="text-danger mt-5">Logout</a>
    </div>
    {% endif %}
    <div class="main">{% block content %}{% endblock %}</div>

    <script>
        function addItem() {
            const container = document.getElementById('item-container');
            const index = container.children.length;
            const row = document.createElement('div');
            row.className = 'item-row border p-4 mb-4 bg-white rounded shadow-sm';
            row.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-4">
                        <label class="form-label">Item Title</label>
                        <input name="title[]" class="form-control" list="p_list" required>
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Sq.Ft</label>
                        <input name="feet[]" type="number" step="any" class="form-control">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Qty (Pcs)</label>
                        <input name="pcs[]" type="number" class="form-control">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Rate</label>
                        <input name="rate[]" type="number" step="any" class="form-control" oninput="toggleManual(${index})">
                    </div>
                    <div class="col-md-2">
                        <label class="form-label">Manual Total</label>
                        <input name="manual[]" type="number" step="any" class="form-control" id="manual_${index}">
                    </div>
                    <div class="col-12 mt-3">
                        <label class="form-label">Description (Optional)</label>
                        <textarea name="desc[]" class="form-control" rows="2" placeholder="Glass type, Lock, Color..."></textarea>
                    </div>
                </div>
            `;
            container.appendChild(row);
        }
        function toggleManual(idx) {
            // Logic handled by server side, but can add visual hints here
        }
    </script>
</body>
</html>
"""

# ---- ৩. রাউটস (ROUTES) ----
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == USER_LOGIN and request.form['pass'] == USER_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', """
        <div class="container d-flex justify-content-center align-items-center" style="height: 80vh;">
            <div class="card p-5" style="width: 400px;">
                <h2 class="text-center mb-4">Admin Login</h2>
                <form method="POST">
                    <div class="mb-3"><input name="user" class="form-control form-control-lg" placeholder="Username" required></div>
                    <div class="mb-4"><input name="pass" type="password" class="form-control form-control-lg" placeholder="Password" required></div>
                    <button class="btn btn-primary btn-lg w-100">Login</button>
                </form>
            </div>
        </div>
    """))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h2 class="mb-4">Dashboard Status</h2>
        <div class="row g-4">
            <div class="col-md-4"><div class="stat-card"><h5>Total Sales</h5><h2 class="text-primary">0 Tk</h2></div></div>
            <div class="col-md-4"><div class="stat-card"><h5>Customers</h5><h2 class="text-success">{len(data_store['customers'])}</h2></div></div>
            <div class="col-md-4"><div class="stat-card"><h5>Product Items</h5><h2 class="text-info">{len(data_store['products'])}</h2></div></div>
        </div>
    """))

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        data_store['customers'].append({'name': request.form['n'], 'mob': request.form['m']})
    
    table_rows = "".join([f"<tr><td>{c['name']}</td><td>{c['mob']}</td></tr>" for c in data_store['customers']])
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h3>Manage Customers</h3>
        <form method="POST" class="card p-4 mb-4 d-flex flex-row gap-3">
            <input name="n" class="form-control" placeholder="Customer Name" required>
            <input name="m" class="form-control" placeholder="Mobile No" required>
            <button class="btn btn-success">Add Customer</button>
        </form>
        <div class="card p-4"><table class="table"><thead><tr><th>Name</th><th>Mobile</th></tr></thead><tbody>{table_rows}</tbody></table></div>
    """))

@app.route('/products', methods=['GET', 'POST'])
def products():
    if not session.get('logged_in'): return redirect(url_for('login'))
    if request.method == 'POST':
        data_store['products'].append(request.form['p'])
    
    list_items = "".join([f"<li class='list-group-item'>{p}</li>" for p in data_store['products']])
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <h3>Manage Products</h3>
        <form method="POST" class="card p-4 mb-4 d-flex flex-row gap-3">
            <input name="p" class="form-control" placeholder="Product Title (e.g. Window 4/4)" required>
            <button class="btn btn-primary">Add Product</button>
        </form>
        <ul class="list-group card p-2">{list_items}</ul>
    """))

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if not session.get('logged_in'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Processing multi-item inputs
        titles = request.form.getlist('title[]')
        feets = request.form.getlist('feet[]')
        pcss = request.form.getlist('pcs[]')
        rates = request.form.getlist('rate[]')
        manuals = request.form.getlist('manual[]')
        descs = request.form.getlist('desc[]')
        
        items = []
        for i in range(len(titles)):
            f, p, r, m = float(feets[i] or 0), int(pcss[i] or 0), float(rates[i] or 0), float(manuals[i] or 0)
            if f == 0 and p == 0: continue # Skip invalid rows
            total = (f if f > 0 else p) * r if r > 0 else m
            items.append({'title': titles[i], 'feet': feets[i], 'pcs': pcss[i], 'rate': rates[i], 'total': total, 'desc': descs[i]})
        
        pdf = generate_pdf(items, doc_type, request.form['c_name'], request.form['c_mob'], float(request.form.get('adv', 0)), request.form['note'])
        return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)

    c_options = "".join([f"<option value='{c['name']}'>{c['name']}</option>" for c in data_store['customers']])
    p_options = "".join([f"<option value='{p}'>{p}</option>" for p in data_store['products']])
    
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', f"""
        <div class="d-flex justify-content-between"><h3>Create {doc_type}</h3><button onclick="addItem()" class="btn btn-dark">+ Add New Item Row</button></div>
        <form method="POST" class="mt-4">
            <div class="card p-4 mb-4">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label>Customer Name</label>
                        <input name="c_name" class="form-control" list="c_list" required>
                        <datalist id="c_list">{c_options}</datalist>
                    </div>
                    <div class="col-md-6 mb-3"><label>Customer Mobile</label><input name="c_mob" class="form-control" required></div>
                </div>
            </div>
            
            <div id="item-container">
                <div class="item-row border p-4 mb-4 bg-white rounded shadow-sm">
                    <div class="row g-3">
                        <div class="col-md-4"><label class="form-label">Item Title</label><input name="title[]" class="form-control" list="p_list" required><datalist id="p_list">{p_options}</datalist></div>
                        <div class="col-md-2"><label class="form-label">Sq.Ft</label><input name="feet[]" type="number" step="any" class="form-control"></div>
                        <div class="col-md-2"><label class="form-label">Qty (Pcs)</label><input name="pcs[]" type="number" class="form-control"></div>
                        <div class="col-md-2"><label class="form-label">Rate</label><input name="rate[]" type="number" step="any" class="form-control"></div>
                        <div class="col-md-2"><label class="form-label">Manual Total</label><input name="manual[]" type="number" step="any" class="form-control"></div>
                        <div class="col-12 mt-3"><label class="form-label">Description (Optional)</label><textarea name="desc[]" class="form-control" rows="2"></textarea></div>
                    </div>
                </div>
            </div>

            <div class="card p-4">
                {f'<div class="mb-3"><label>Advance Payment</label><input name="adv" type="number" class="form-control" value="0"></div>' if doc_type == 'Invoice' else ''}
                <div class="mb-3"><label>Note/Conditions</label><input name="note" class="form-control"></div>
                <button type="submit" class="btn btn-primary btn-lg w-100">Download {doc_type} PDF</button>
            </div>
        </form>
        <datalist id="p_list">{p_options}</datalist>
    """))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

