import os
from flask import Flask, render_template_string, request, send_file, redirect, url_for, session
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from datetime import datetime
import io

app = Flask(__name__)
app.secret_key = "mehedi_secret_key"

# ---- লগইন ডাটা ----
USER_LOGIN = "Mehedihasan"
USER_PASS = "1234"

# ---- প্রফেশনাল PDF ডিজাইন লজিক (আগের রিকোয়ারমেন্ট অনুযায়ী) ----
def generate_pdf(data, doc_type, cust_name, cust_mobile, advance, note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # হেডার
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "MEHEDI THAI ALUMINUM & GLASS")
    c.setFont("Helvetica", 9.5)
    address = "West Side Of The Khartoil Boro Mosjid, Satiash Road, Tongi, Gazipur, 1700."
    c.drawCentredString(width/2, height - 65, address)
    c.setFont("Helvetica-Oblique", 10.5)
    marketing = "High-quality Thai Aluminum & Glass works with 100% guarantee. Modern design & fast delivery."
    c.drawCentredString(width/2, height - 82, marketing)

    # প্রোপাইটর ও মোবাইল (ফিক্সড)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656,  +880 1601-465130")
    
    # তারিখ ও নম্বর
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.setLineWidth(0.8)
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার ইনফো
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, height - 160, f"Customer Name: {cust_name}")
    c.drawString(40, height - 175, f"Mobile: {cust_mobile}")

    # টেবিল
    x_coords = [40, 310, 370, 420, 480, 555]
    curr_y = height - 195
    table_top = curr_y
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString((x_coords[0]+x_coords[1])/2, curr_y - 14, "DESCRIPTION")
    c.drawCentredString((x_coords[1]+x_coords[2])/2, curr_y - 14, "SQ.FT")
    c.drawCentredString((x_coords[2]+x_coords[3])/2, curr_y - 14, "QTY")
    c.drawCentredString((x_coords[3]+x_coords[4])/2, curr_y - 14, "RATE")
    c.drawCentredString((x_coords[4]+x_coords[5])/2, curr_y - 14, "TOTAL")
    
    curr_y -= 20
    c.line(40, curr_y, 555, curr_y)

    grand_total = 0
    for i, item in enumerate(data):
        total_val = float(item['total'])
        grand_total += total_val
        text_y = curr_y - 15
        
        c.setFont("Helvetica-Bold", 10)
        c.drawString(45, text_y, f"{i+1}. {item['title']}")
        c.setFont("Helvetica", 10)
        c.drawCentredString((x_coords[1]+x_coords[2])/2, text_y, item['feet'] or "-")
        c.drawCentredString((x_coords[2]+x_coords[3])/2, text_y, item['pcs'] or "-")
        c.drawCentredString((x_coords[3]+x_coords[4])/2, text_y, item['rate'] or "-")
        c.drawRightString(550, text_y, f"{total_val:.0f}")
        
        curr_y = text_y - 5
        if item['desc']:
            # তীর এবং ব্র্যাকেট লজিক
            c.setLineWidth(0.6); c.line(70, curr_y, 70, curr_y-5) # Arrow
            c.setFont("Helvetica", 10.5)
            lines = item['desc'].split('\n')
            list_y = curr_y - 15
            start_l_y = list_y + 10
            max_w = 0
            for line in lines:
                c.drawString(75, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            # ব্র্যাকেট আঁকা (Ultra Thin 0.3)
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.3,0.3,0.3)
            c.line(65, start_l_y, 60, start_l_y); c.line(60, start_l_y, 60, list_y+5); c.line(60, list_y+5, 65, list_y+5) # Left [
            c.line(75+max_w+5, start_l_y, 75+max_w+10, start_l_y); c.line(75+max_w+10, start_l_y, 75+max_w+10, list_y+5); c.line(75+max_w+10, list_y+5, 75+max_w+5, list_y+5) # Right ]
            c.setStrokeColorRGB(0,0,0)
            curr_y = list_y - 5
        else: curr_y -= 10

    # টেবিল বর্ডার
    for x in x_coords: c.line(x, table_top, x, curr_y)
    c.line(40, table_top, 555, table_top); c.line(40, curr_y, 555, curr_y)

    # সামারি বক্স
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22); c.setFont("Helvetica-Bold", 10)
    c.drawString(405, summary_y+7, "Grand Total:"); c.drawRightString(550, summary_y+7, f"{grand_total:,.0f} Tk")
    
    if doc_type == "Invoice":
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Advance:"); c.drawRightString(550, summary_y+7, f"{advance:,.0f} Tk")
        summary_y -= 22; c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Due Amount:"); c.drawRightString(550, summary_y+7, f"{grand_total-advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y, 320, 40); c.setFont("Helvetica-Bold", 9); c.drawString(45, summary_y+25, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y+10, note)

    c.line(40, 60, 160, 60); c.drawString(50, 45, "Customer Signature")
    c.line(435, 60, 555, 60); c.drawRightString(545, 45, "Authorized Signature")
    
    c.save()
    buffer.seek(0)
    return buffer

# ---- HTML টেমপ্লেটসমূহ ----
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f7f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .sidebar { height: 100vh; background: #2c3e50; color: white; position: fixed; width: 250px; }
        .content { margin-left: 250px; padding: 20px; }
        .card { border: none; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .btn-primary { background: #3498db; border: none; }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .content { margin-left: 0; } }
    </style>
</head>
<body>
    {% if session.logged_in %}
    <div class="sidebar p-3">
        <h3>Mehedi Thai</h3>
        <hr>
        <ul class="nav nav-pills flex-column mb-auto">
            <li class="nav-item"><a href="/dashboard" class="nav-link text-white">Dashboard</a></li>
            <li><a href="/create/Invoice" class="nav-link text-white">Create Invoice</a></li>
            <li><a href="/create/Quotation" class="nav-link text-white">Create Quotation</a></li>
            <li><a href="/logout" class="nav-link text-white mt-5">Logout</a></li>
        </ul>
    </div>
    {% endif %}
    <div class="content">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

LOGIN_HTML = """
{% extends "base" %}
{% block content %}
<div class="d-flex justify-content-center align-items-center" style="height: 80vh;">
    <div class="card p-4" style="width: 350px;">
        <h2 class="text-center mb-4">Login</h2>
        <form method="POST">
            <div class="mb-3"><input type="text" name="user" class="form-control" placeholder="Username" required></div>
            <div class="mb-3"><input type="password" name="pass" class="form-control" placeholder="Password" required></div>
            <button type="submit" class="btn btn-primary w-100">Login</button>
        </form>
    </div>
</div>
{% endblock %}
"""

DASHBOARD_HTML = """
{% extends "base" %}
{% block content %}
<h2>Welcome, Mehedi Hasan</h2>
<div class="row mt-4">
    <div class="col-md-4"><div class="card p-3 bg-white text-center"><h5>Total Sales</h5><h3>0 Tk</h3></div></div>
    <div class="col-md-4"><div class="card p-3 bg-white text-center"><h5>Invoices</h5><h3>0</h3></div></div>
    <div class="col-md-4"><div class="card p-3 bg-white text-center"><h5>Quotations</h5><h3>0</h3></div></div>
</div>
{% endblock %}
"""

CREATE_HTML = """
{% extends "base" %}
{% block content %}
<h2>Create {{ doc_type }}</h2>
<form method="POST" class="card p-4 mt-3">
    <div class="row">
        <div class="col-md-6 mb-3"><label>Customer Name</label><input type="text" name="cust_name" class="form-control" required></div>
        <div class="col-md-6 mb-3"><label>Mobile</label><input type="text" name="cust_mobile" class="form-control" required></div>
    </div>
    <hr>
    <div id="items">
        <div class="item-row border p-3 mb-3 bg-light rounded">
            <div class="row">
                <div class="col-md-4"><label>Title</label><input type="text" name="title[]" class="form-control" required></div>
                <div class="col-md-2"><label>Sq.Ft</label><input type="number" step="any" name="feet[]" class="form-control"></div>
                <div class="col-md-2"><label>Pcs</label><input type="number" name="pcs[]" class="form-control"></div>
                <div class="col-md-2"><label>Rate</label><input type="number" step="any" name="rate[]" class="form-control"></div>
                <div class="col-md-2"><label>Manual Total</label><input type="number" step="any" name="manual_total[]" class="form-control"></div>
            </div>
            <div class="mt-2"><label>Description (Optional)</label><textarea name="desc[]" class="form-control" rows="2"></textarea></div>
        </div>
    </div>
    {% if doc_type == 'Invoice' %}
    <div class="mb-3"><label>Advance Amount</label><input type="number" name="advance" class="form-control" value="0"></div>
    {% endif %}
    <div class="mb-3"><label>Note</label><input type="text" name="note" class="form-control"></div>
    <button type="submit" class="btn btn-success">Generate PDF</button>
</form>
{% endblock %}
"""

# ---- Routes ----
@app.route('/')
def index():
    if 'logged_in' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['user'] == USER_LOGIN and request.form['pass'] == USER_PASS:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', LOGIN_HTML))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', DASHBOARD_HTML))

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if 'logged_in' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        titles = request.form.getlist('title[]')
        feets = request.form.getlist('feet[]')
        pcss = request.form.getlist('pcs[]')
        rates = request.form.getlist('rate[]')
        manual_totals = request.form.getlist('manual_total[]')
        descs = request.form.getlist('desc[]')
        
        processed_items = []
        for i in range(len(titles)):
            f = float(feets[i]) if feets[i] else 0
            p = int(pcss[i]) if pcss[i] else 0
            r = float(rates[i]) if rates[i] else 0
            m = float(manual_totals[i]) if manual_totals[i] else 0
            
            total = 0
            if r > 0:
                total = (f if f > 0 else p) * r
            else:
                total = m
                
            processed_items.append({
                'title': titles[i], 'feet': feets[i], 'pcs': pcss[i], 
                'rate': rates[i], 'total': total, 'desc': descs[i]
            })
            
        pdf = generate_pdf(processed_items, doc_type, request.form['cust_name'], 
                           request.form['cust_mobile'], float(request.form.get('advance', 0)), 
                           request.form['note'])
        return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)

    return render_template_string(BASE_HTML.replace('{% block content %}{% endblock %}', CREATE_HTML), doc_type=doc_type)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
