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

# ---- প্রফেশনাল PDF লজিক (হুবহু আগের ডিজাইন) ----
def generate_pdf(data, doc_type, cust_name, cust_mobile, advance, note):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # হেডার ডিজাইন
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height - 50, "MEHEDI THAI ALUMINUM & GLASS")
    c.setFont("Helvetica", 9.5)
    c.drawCentredString(width/2, height - 65, "West Side Of The Khartoil Boro Mosjid, Satiash Road, Tongi, Gazipur, 1700.")
    c.setFont("Helvetica-Oblique", 10.5)
    c.drawCentredString(width/2, height - 82, "High-quality Thai Aluminum & Glass works with 100% guarantee.")

    # প্রোপাইটর তথ্য
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, height - 110, "Proprietor: ABDUL HANNAN")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 125, "Mobile: +880 1811-179656, +880 1601-465130")
    
    # ডেট ও নম্বর
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(555, height - 110, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
    c.drawRightString(555, height - 125, f"{doc_type} No: #200")
    c.line(40, height - 140, 555, height - 140)

    # কাস্টমার
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
            # বিবরণ
            lines = item['desc'].split('\n')
            list_y = curr_y - 15
            max_w = 0
            c.setFont("Helvetica", 10.5)
            for line in lines:
                c.drawString(75, list_y, line)
                w = c.stringWidth(line, "Helvetica", 10.5)
                if w > max_w: max_w = w
                list_y -= 14
            # চিকন ব্র্যাকেট
            c.setLineWidth(0.3); c.setStrokeColorRGB(0.4, 0.4, 0.4)
            c.rect(65, list_y + 10, max_w + 15, (text_y - list_y - 15), stroke=1, fill=0)
            c.setStrokeColorRGB(0, 0, 0)
            curr_y = list_y - 5
        else: curr_y -= 10

    # টেবিল বর্ডার (একটানে খাড়া দাগ)
    c.setLineWidth(1)
    for x in x_coords: c.line(x, table_top, x, curr_y)
    c.line(40, table_top, 555, table_top)
    c.line(40, curr_y, 555, curr_y)

    # হিসাব বক্স
    summary_y = curr_y - 30
    c.rect(400, summary_y, 155, 22)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(405, summary_y + 7, "Grand Total:")
    c.drawRightString(550, summary_y + 7, f"{grand_total:,.0f} Tk")
    
    if doc_type == "Invoice":
        summary_y -= 22
        c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Advance:"); c.drawRightString(550, summary_y+7, f"{advance:,.0f} Tk")
        summary_y -= 22
        c.rect(400, summary_y, 155, 22); c.drawString(405, summary_y+7, "Due Amount:"); c.drawRightString(550, summary_y+7, f"{grand_total-advance:,.0f} Tk")

    if note:
        c.rect(40, summary_y-45, 320, 40); c.drawString(45, summary_y-15, "Note:"); c.setFont("Helvetica", 9); c.drawString(45, summary_y-30, note)

    # সিগনেচার
    c.line(40, 60, 160, 60); c.setFont("Helvetica", 9); c.drawString(50, 45, "Customer Signature")
    c.line(435, 60, 555, 60); c.drawRightString(545, 45, "Authorized Signature")
    
    c.save()
    buffer.seek(0)
    return buffer

# ---- HTML UI Components ----
HEADER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mehedi Thai Admin</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; }
        .sidebar { height: 100vh; background: #212529; color: white; position: fixed; width: 240px; padding: 20px; }
        .main-content { margin-left: 240px; padding: 30px; }
        .card { border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 12px; }
        @media (max-width: 768px) { .sidebar { width: 100%; height: auto; position: relative; } .main-content { margin-left: 0; } }
    </style>
</head>
<body>
"""

SIDEBAR = """
    <div class="sidebar">
        <h3>Mehedi Thai</h3><hr>
        <nav class="nav flex-column">
            <a class="nav-link text-white" href="/dashboard">🏠 Dashboard</a>
            <a class="nav-link text-white" href="/create/Invoice">🧾 Create Invoice</a>
            <a class="nav-link text-white" href="/create/Quotation">📄 Create Quotation</a>
            <a class="nav-link text-white mt-5" href="/logout">🚪 Logout</a>
        </nav>
    </div>
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
        return "Invalid Login"
    
    login_form = """
    <div class="container d-flex justify-content-center align-items-center" style="height: 100vh;">
        <div class="card p-4" style="width: 350px;">
            <h3 class="text-center mb-4">Admin Login</h3>
            <form method="POST">
                <input type="text" name="user" class="form-control mb-3" placeholder="Username" required>
                <input type="password" name="pass" class="form-control mb-3" placeholder="Password" required>
                <button type="submit" class="btn btn-primary w-100">Login</button>
            </form>
        </div>
    </div>
    """
    return render_template_string(HEADER + login_form + "</body></html>")

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session: return redirect(url_for('login'))
    content = """
    <div class="main-content">
        <h2>Dashboard Overview</h2>
        <div class="row mt-4">
            <div class="col-md-4"><div class="card p-4 bg-primary text-white"><h5>Live Sales</h5><h2>0 BDT</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-success text-white"><h5>Orders</h5><h2>0</h2></div></div>
            <div class="col-md-4"><div class="card p-4 bg-warning text-dark"><h5>Customers</h5><h2>0</h2></div></div>
        </div>
    </div>
    """
    return render_template_string(HEADER + SIDEBAR + content + "</body></html>")

@app.route('/create/<doc_type>', methods=['GET', 'POST'])
def create(doc_type):
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        # ডাটা প্রসেসিং লজিক
        titles = request.form.getlist('title[]')
        feets = request.form.getlist('feet[]')
        pcss = request.form.getlist('pcs[]')
        rates = request.form.getlist('rate[]')
        manuals = request.form.getlist('manual[]')
        descs = request.form.getlist('desc[]')
        
        items = []
        for i in range(len(titles)):
            f = float(feets[i]) if feets[i] else 0
            p = int(pcss[i]) if pcss[i] else 0
            r = float(rates[i]) if rates[i] else 0
            m = float(manuals[i]) if manuals[i] else 0
            total = (f if f > 0 else p) * r if r > 0 else m
            items.append({'title': titles[i], 'feet': feets[i], 'pcs': pcss[i], 'rate': rates[i], 'total': total, 'desc': descs[i]})
        
        pdf = generate_pdf(items, doc_type, request.form['cname'], request.form['cmob'], float(request.form.get('adv', 0)), request.form['note'])
        return send_file(pdf, download_name=f"{doc_type}.pdf", as_attachment=True)

    form_html = f"""
    <div class="main-content">
        <h3>Create New {doc_type}</h3>
        <form method="POST" class="card p-4 mt-3">
            <div class="row mb-3">
                <div class="col-md-6"><label>Customer Name</label><input type="text" name="cname" class="form-control" required></div>
                <div class="col-md-6"><label>Mobile No</label><input type="text" name="cmob" class="form-control" required></div>
            </div>
            <hr>
            <div id="item-list">
                <div class="border p-3 mb-3 bg-light rounded">
                    <div class="row">
                        <div class="col-md-3"><label>Title</label><input type="text" name="title[]" class="form-control" required></div>
                        <div class="col-md-2"><label>Sq.Ft</label><input type="number" step="any" name="feet[]" class="form-control"></div>
                        <div class="col-md-1"><label>Qty</label><input type="number" name="pcs[]" class="form-control"></div>
                        <div class="col-md-2"><label>Rate</label><input type="number" step="any" name="rate[]" class="form-control"></div>
                        <div class="col-md-2"><label>Manual Total</label><input type="number" step="any" name="manual[]" class="form-control"></div>
                    </div>
                    <textarea name="desc[]" class="form-control mt-2" placeholder="Description (Optional)"></textarea>
                </div>
            </div>
            {"<label>Advance Payment</label><input type='number' name='adv' class='form-control mb-3' value='0'>" if doc_type == 'Invoice' else ""}
            <label>Notes</label><input type="text" name="note" class="form-control mb-3">
            <button type="submit" class="btn btn-success w-100">Download {doc_type} PDF</button>
        </form>
    </div>
    """
    return render_template_string(HEADER + SIDEBAR + form_html + "</body></html>")

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

