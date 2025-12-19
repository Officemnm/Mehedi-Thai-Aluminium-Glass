import os
import io
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mehedi_thai_key_2025"

# ---- ফিক্সড ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# মেমরিতে ডাটা সেভ রাখার জন্য (রেন্ডার রিস্টার্ট দিলে এগুলো মুছে যাবে, ডাটাবেজ ছাড়া এটিই নিয়ম)
customers = []
products = ["Thai Window", "Mercury Glass", "Sliding Door", "SS Grill"]

# ---- প্রফেশনাল PDF ডিজাইন লজিক ----
def generate_pdf(data, doc_type, c_name, c_mob, advance, note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # হেডার
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "MEHEDI THAI ALUMINUM & GLASS")
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(width/2, height - 65, "West Side Of The Khartoil Boro Mosjid, Satiash Road, Tongi, Gazipur, 1700.")
    c.setFont("Helvetica-Oblique", 10.5)
    c.drawCentredString(width/2, height - 82, "High-quality Thai Aluminum & Glass works with 100% guarantee.")

    # প্রোপাইটর
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656,  +880 1601-465130")
    
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার
    c.drawString(40, height - 160, f"Customer Name: {c_name}")
    c.drawString(40, height - 175, f"Mobile: {c_mob}")

    # টেবিল শুরু
    x_coords = [40, 310, 370, 420, 480, 555]
    curr_y = height - 195
    table_top = curr_y
    c.setFont("Helvetica-Bold", 9)
    cols = ["DESCRIPTION", "SQ.FT", "QTY", "RATE", "TOTAL"]
    for i, col in enumerate(cols):
        c.drawCentredString((x_coords[i]+x_coords[i+1])/2, curr_y-14, col)
    
    curr_y -= 20
    c.setLineWidth(1)
    c.line(40, curr_y, 555, curr_y)

    grand_total = 0
    for i, item in enumerate(data):
        total_val = float(item['total'])
        grand_total += total_val
        text_y = curr_y - 18
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, text_y, f"{i+1}. {item['title']}")
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, item['feet'] or "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, item['pcs'] or "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, item['rate'] or "-")
        c.drawRightString(550, text_y, f"{total_val:.0f}")
        
        curr_y = text_y - 5
        if item['desc']:
            c.setFont("Helvetica", 10.5)
            lines = item['desc'].split('\n')
            list_y = curr_y - 12
            start_l_y = list_y + 10
            max_w = 0
            for line in lines:
                c.drawString(75, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            # অতি চিকন ব্র্যাকেট (০.৩)
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            c.line(65, start_l_y, 60, start_l_y); c.line(60, start_l_y, 60, list_y+5); c.line(60, list_y+5, 65, list_y+5)
            c.line(75+max_w+5, start_l_y, 75+max_w+10, start_l_y); c.line(75+max_w+10, start_l_y, 75+max_w+10, list_y+5); c.line(75+max_w+10, list_y+5, 75+max_w+5, list_y+5)
            c.setStrokeColorRGB(0, 0, 0)
            curr_y = list_y - 5
        else: curr_y -= 10

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
        c.rect(40, summary_y-10, 320, 30); c.drawString(45, summary_y+5, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y-5, note)

    c.line(40, 60, 160, 60); c.line(425, 60, 555, 60)
    c.drawString(45, 45, "Customer Signature"); c.drawRightString(550, 45, "Authorized Signature")
    
    c.save(); buffer.seek(0)
    return buffer

# ---- UI (HTML/CSS) ----
UI_BASE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai | Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f0f2f5; }
        .sidebar { height: 100vh; background: #1a202c; color: white; position: fixed; width: 250px; padding-top: 20px; }
        .sidebar a { color: #cbd5e0; text-decoration: none; padding: 12px 20px; display: block; transition: 0.3s; }
        .sidebar a:hover { background: #2d3748; color: white; }
        .main { margin-left: 250px; padding: 30px; }
        .card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-radius: 12px; }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .main { margin-left: 0; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <div class="sidebar">
        <h4 class="text-center">Mehedi Thai</h4><hr>
        <a href="/dashboard">Dashboard</a>
        <a href="/customers">Customers</a>
        <a href="/products">Products</a>
        <a href="/create/Invoice">Create Invoice</a>
        <a href="/create/Quotation">Create Quotation</a>
        <a href="/logout" class="mt-5 text-danger">Logout</a>
    </div>
    {% endif %}
    <div class="main">{% block content %}{% endblock %}</div>
    <script>
        function toggleTotal(index) {
            const rate = document.getElementById('rate_'+index).value;
            const manual = document.getElementById('manual_'+index);
            if(rate) { manual.disabled = true; manual.value = ''; }
            else { manual.disabled = false; }
        }
    </script>
</body>
</html>
"""

# ---- Routes ----
@app.route('/')
def index(): return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == USER_LOGIN and request.form['pass'] == USER_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(UI_BASE.replace('{% block content %}{% endblock %}', """
        <div class="d-flex justify-content-center mt-5">
            <div class="card p-4 shadow-sm" style="width: 350px;">
                <h3 class="text-center">Login</h3>
                <form method="POST"><input name="user" class="form-control mb-3" placeholder="User"><input name="pass" type="password" class="form-control mb-3" placeholder="Pass"><button class="btn btn-primary w-100">Login</button></form>
            </div>
        </div>
    """))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    return render_template_string(UI_BASE.replace('{% block content %}{% endblock %}', f"""
        <h2>Dashboard</h2>
        <div class="row mt-4">
            <div class="col-md-4"><div class="card p-4 bg-white"><h5>Live Sales</h5><h2>0 Tk</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-white"><h5>Products</h5><h2>{len(products)}</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-white"><h5>Customers</h5><h2>{len(customers)}</h2></div></div>
        </div>
    """))

@app.route('/products', methods=['GET', 'POST'])
def manage_products():
    if request.method == 'POST': products.append(request.form['pname'])
    html = "<h3>Manage Products</h3><form method='POST' class='d-flex mb-3'><input name='pname' class='form-control me-2' placeholder='Add Title'><button class='btn btn-success'>Add</button></form><ul>"
    for p in products: html += f"<li>{p}</li>"
    return render_template_string(UI_BASE.replace('{% block content %}{% endblock %}', html + "</ul>"))

@app.route('/customers', methods=['GET', 'POST'])
def manage_customers():
    if request.method == 'POST': customers.append({'name': request.form['cname'], 'mob': request.form['cmob']})
    html = "<h3>Manage Customers</h3><form method='POST' class='mb-3'><input name='cname' class='form-control mb-2' placeholder='Name'><input name='cmob' class='form-control mb-2' placeholder='Mobile'><button class='btn btn-success'>Add</button></form><ul>"
    for c in customers: html += f"<li>{c['name']} - {c['mob']}</li>"
    return render_template_string(UI_BASE.replace('{% block content %}{% endblock %}', html + "</ul>"))

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if 'logged_in' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        # Processing items
        titles = request.form.getlist('title[]')
        feets = request.form.getlist('feet[]')
        pcss = request.form.getlist('pcs[]')
        rates = request.form.getlist('rate[]')
        manuals = request.form.getlist('manual[]')
        descs = request.form.getlist('desc[]')
        
        final_items = []
        for i in range(len(titles)):
            f, p, r, m = float(feets[i] or 0), int(pcss[i] or 0), float(rates[i] or 0), float(manuals[i] or 0)
            if f == 0 and p == 0: continue
            total = (f if f > 0 else p) * r if r > 0 else m
            final_items.append({'title': titles[i], 'feet': feets[i], 'pcs': pcss[i], 'rate': rates[i], 'total': total, 'desc': descs[i]})
        
        pdf = generate_pdf(final_items, doc_type, request.form['c_name'], request.form['c_mob'], float(request.form.get('advance', 0)), request.form['note'])
        return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)

    # Form with dropdown for products
    options = "".join([f"<option value='{p}'>{p}</option>" for p in products])
    form = f"""
        <h3>Create {doc_type}</h3>
        <form method="POST" class="card p-4 mt-3">
            <div class="row mb-3">
                <div class="col-md-6"><label>Customer Name</label><input name="c_name" class="form-control" list="cust_list" required><datalist id="cust_list">{''.join([f"<option value='{c['name']}'>" for c in customers])}</datalist></div>
                <div class="col-md-6"><label>Mobile</label><input name="c_mob" class="form-control" required></div>
            </div>
            <div id="items">
                <div class="border p-3 mb-3 bg-light rounded">
                    <div class="row">
                        <div class="col-md-3"><label>Title</label><input name="title[]" class="form-control" list="prod_list" required><datalist id="prod_list">{options}</datalist></div>
                        <div class="col-md-2"><label>Sq.Ft</label><input name="feet[]" class="form-control" type="number" step="any"></div>
                        <div class="col-md-1"><label>Qty</label><input name="pcs[]" class="form-control" type="number"></div>
                        <div class="col-md-2"><label>Rate</label><input name="rate[]" id="rate_0" class="form-control" type="number" step="any" oninput="toggleTotal(0)"></div>
                        <div class="col-md-2"><label>Manual Total</label><input name="manual[]" id="manual_0" class="form-control" type="number" step="any"></div>
                    </div>
                    <textarea name="desc[]" class="form-control mt-2" placeholder="Description (Optional)"></textarea>
                </div>
            </div>
            {f'<input name="advance" class="form-control mb-3" placeholder="Advance Payment">' if doc_type == 'Invoice' else ''}
            <input name="note" class="form-control mb-3" placeholder="Note">
            <button class="btn btn-primary w-100">Download {doc_type} PDF</button>
        </form>
    """
    return render_template_string(UI_BASE.replace('{% block content %}{% endblock %}', form))

@app.route('/logout')
def logout(): session.pop('logged_in', None); return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

