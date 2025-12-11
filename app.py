"""
MEHEDI THAI ALUMINIUM & GLASS - Complete Professional Management System
Single File Flask Application
Requirements: flask, flask-login, werkzeug
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, jsonify, session, render_template_string, Response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize Flask App
app = Flask(__name__)
app.secret_key = 'aluminium-glass-shop-secret-key-2024-professional'
app.config['SESSION_TYPE'] = 'filesystem'

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Setup
DB_FOLDER = 'database'
os.makedirs(DB_FOLDER, exist_ok=True)

def get_db_path(filename):
    return os.path.join(DB_FOLDER, filename)

# Database files
DATABASES = {
    'users': get_db_path('users.json'),
    'products': get_db_path('products.json'),
    'customers': get_db_path('customers.json'),
    'invoices': get_db_path('invoices.json'),
    'quotations': get_db_path('quotations.json'),
    'transactions': get_db_path('transactions.json'),
    'categories': get_db_path('categories.json'),
    'settings': get_db_path('settings.json')
}

# Initialize empty JSON files if they don't exist
def init_database():
    for db_name, db_path in DATABASES.items():
        if not os.path.exists(db_path):
            with open(db_path, 'w') as f:
                json.dump([], f, indent=4)
    print("✓ Database files initialized")

# Helper functions for JSON operations
def read_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def get_next_id(items, prefix=''):
    if not items:
        return f"{prefix}0001"
    try:
        last_id = max(int(item['id'].replace(prefix, '')) for item in items if item['id'].startswith(prefix))
        return f"{prefix}{last_id + 1:04d}"
    except:
        return f"{prefix}0001"

# User Model
class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.email = user_data['email']
        self.full_name = user_data['full_name']
        self.role = user_data['role']
        self.permissions = user_data.get('permissions', [])
        self._is_active = user_data.get('is_active', True)
    
    @property
    def is_active(self):
        return self._is_active

@login_manager.user_loader
def load_user(user_id):
    users = read_json(DATABASES['users'])
    for user in users:
        if user['id'] == user_id:
            return User(user)
    return None

# Permission Decorator
def permission_required(permission):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if permission not in current_user.permissions and 'all' not in current_user.permissions:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize Default Data
def init_default_data():
    users = read_json(DATABASES['users'])
    if not any(u['username'] == 'admin' for u in users):
        admin_user = {
            'id': str(uuid.uuid4()),
            'username': 'admin',
            'email': 'admin@aluminiumglass.com',
            'password': generate_password_hash('admin123'),
            'full_name': 'Administrator',
            'role': 'admin',
            'permissions': ['all'],
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        users.append(admin_user)
        write_json(DATABASES['users'], users)
        print("✓ Default admin user created (admin/admin123)")

    # Initialize default categories
    categories = read_json(DATABASES['categories'])
    if not categories:
        default_categories = [
            {'id': 'CAT001', 'name': 'Aluminium Windows', 'description': 'Aluminium window frames and accessories'},
            {'id': 'CAT002', 'name': 'Aluminium Doors', 'description': 'Aluminium door frames and systems'},
            {'id': 'CAT003', 'name': 'Glass', 'description': 'All types of glass'},
            {'id': 'CAT004', 'name': 'Hardware', 'description': 'Handles, locks, hinges, etc.'},
            {'id': 'CAT005', 'name': 'Accessories', 'description': 'Other accessories and fittings'}
        ]
        write_json(DATABASES['categories'], default_categories)

    # Initialize default settings
    settings = read_json(DATABASES['settings'])
    if not settings:
        default_settings = {
            'shop_name': 'MEHEDI THAI ALUMINIUM & GLASS',
            'shop_address': '123 Business Street, City, Country',
            'shop_phone': '+880 1234 567890',
            'shop_email': 'info@aluminiumglass.com',
            'tax_rate': 5.0,
            'currency': 'BDT',
            'invoice_prefix': 'INV',
            'quotation_prefix': 'QTN',
            'logo_url': '/static/logo.png',
            'created_at': datetime.now().isoformat()
        }
        write_json(DATABASES['settings'], [default_settings])

# HTML Templates
def get_base_template(title, active_page, content, show_sidebar=True):
    user_links = ""
    if current_user.is_authenticated:
        if 'all' in current_user.permissions or 'manage_users' in current_user.permissions:
            user_links += f'<a href="/users" class="list-group-item list-group-item-action {"active" if active_page == "users" else ""}"><i class="fas fa-users-cog"></i> User Management</a>'
        if 'all' in current_user.permissions or 'manage_settings' in current_user.permissions:
            user_links += f'<a href="/settings" class="list-group-item list-group-item-action {"active" if active_page == "settings" else ""}"><i class="fas fa-cog"></i> Settings</a>'
    
    sidebar = ""
    if show_sidebar:
        sidebar = f"""
        <!-- Sidebar -->
        <div class="col-md-3 col-lg-2 d-md-block bg-dark sidebar collapse" style="min-height: 100vh;">
            <div class="position-sticky pt-3">
                <div class="text-center mb-4">
                    <div class="rounded-circle bg-primary d-inline-flex align-items-center justify-content-center" style="width: 80px; height: 80px;">
                        <i class="fas fa-building fa-2x text-white"></i>
                    </div>
                    <h6 class="mt-3 text-white">{current_user.full_name}</h6>
                    <small class="text-muted">{current_user.role}</small>
                </div>
                
                <ul class="nav flex-column">
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "dashboard" else "text-white"}" href="/dashboard">
                            <i class="fas fa-tachometer-alt"></i> Dashboard
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "products" else "text-white"}" href="/products">
                            <i class="fas fa-box"></i> Products
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "customers" else "text-white"}" href="/customers">
                            <i class="fas fa-users"></i> Customers
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "invoices" else "text-white"}" href="/invoices">
                            <i class="fas fa-file-invoice"></i> Invoices
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "quotations" else "text-white"}" href="/quotations">
                            <i class="fas fa-quote-right"></i> Quotations
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "accounts" else "text-white"}" href="/accounts">
                            <i class="fas fa-wallet"></i> Accounts
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link {"active" if active_page == "reports" else "text-white"}" href="/reports">
                            <i class="fas fa-chart-bar"></i> Reports
                        </a>
                    </li>
                </ul>
                
                <div class="mt-5">
                    <div class="list-group list-group-flush">
                        {user_links}
                        <a href="/logout" class="list-group-item list-group-item-action bg-danger text-white">
                            <i class="fas fa-sign-out-alt"></i> Logout
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
    
    main_content_col = "col-md-12" if not show_sidebar else "col-md-9 col-lg-10"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title} - MEHEDI THAI ALUMINIUM & GLASS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
        <style>
            :root {{
                --primary-color: #2c3e50;
                --secondary-color: #3498db;
                --accent-color: #e74c3c;
                --success-color: #27ae60;
                --warning-color: #f39c12;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f8f9fa;
            }}
            
            .sidebar {{
                background: linear-gradient(180deg, var(--primary-color) 0%, #1a252f 100%);
            }}
            
            .nav-link {{
                transition: all 0.3s;
            }}
            
            .nav-link:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                padding-left: 20px;
            }}
            
            .nav-link.active {{
                background-color: var(--secondary-color);
                border-radius: 5px;
            }}
            
            .stat-card {{
                border-radius: 10px;
                border: none;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s, box-shadow 0.3s;
            }}
            
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
            }}
            
            .btn-primary {{
                background: linear-gradient(45deg, var(--secondary-color), #2980b9);
                border: none;
            }}
            
            .btn-success {{
                background: linear-gradient(45deg, var(--success-color), #219653);
                border: none;
            }}
            
            .btn-warning {{
                background: linear-gradient(45deg, var(--warning-color), #e67e22);
                border: none;
            }}
            
            .btn-danger {{
                background: linear-gradient(45deg, var(--accent-color), #c0392b);
                border: none;
            }}
            
            .table-hover tbody tr:hover {{
                background-color: rgba(52, 152, 219, 0.1);
            }}
            
            .modal-content {{
                border-radius: 15px;
                border: none;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            }}
            
            .alert {{
                border-radius: 10px;
                border: none;
            }}
            
            .form-control, .form-select {{
                border-radius: 8px;
                border: 1px solid #ddd;
                padding: 10px 15px;
            }}
            
            .form-control:focus, .form-select:focus {{
                border-color: var(--secondary-color);
                box-shadow: 0 0 0 0.25rem rgba(52, 152, 219, 0.25);
            }}
            
            .badge {{
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: 500;
            }}
            
            .invoice-header {{
                background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
                color: white;
                padding: 20px;
                border-radius: 10px 10px 0 0;
            }}
            
            @media print {{
                .no-print {{
                    display: none !important;
                }}
                .print-content {{
                    display: block !important;
                }}
            }}
            
            .glass-effect {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark" style="background: var(--primary-color);">
            <div class="container-fluid">
                <a class="navbar-brand" href="/dashboard">
                    <i class="fas fa-building me-2"></i>
                    <strong>MEHEDI THAI ALUMINIUM & GLASS</strong>
                </a>
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav ms-auto">
                        <li class="nav-item">
                            <a class="nav-link" href="/dashboard">
                                <i class="fas fa-home"></i> Dashboard
                            </a>
                        </li>
                        {f'<li class="nav-item"><span class="nav-link"><i class="fas fa-user"></i> {current_user.full_name}</span></li>' if current_user.is_authenticated else ''}
                    </ul>
                </div>
            </div>
        </nav>
        
        <div class="container-fluid">
            <div class="row">
                {sidebar}
                
                <!-- Main Content -->
                <main class="{main_content_col} ms-sm-auto px-md-4">
                    <div class="container-fluid pt-4">
                        {content}
                    </div>
                </main>
            </div>
        </div>
        
        <!-- Bootstrap & jQuery -->
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.1/moment.min.js"></script>
        
        <script>
            // Auto-dismiss alerts
            $(document).ready(function() {{
                setTimeout(function() {{
                    $('.alert').fadeOut('slow');
                }}, 5000);
                
                // Form validation
                $('form').submit(function(e) {{
                    if (!this.checkValidity()) {{
                        e.preventDefault();
                        e.stopPropagation();
                    }}
                    $(this).addClass('was-validated');
                }});
            }});
        </script>
    </body>
    </html>
    """

def get_login_template():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - MEHEDI THAI ALUMINIUM & GLASS</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .login-card {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
            }
            .logo {
                color: #667eea;
                font-size: 3rem;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="login-card">
            <div class="text-center mb-4">
                <div class="logo">
                    <i class="fas fa-building"></i>
                </div>
                <h2>MEHEDI THAI ALUMINIUM & GLASS</h2>
                <p class="text-muted">Professional Management System</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="alert alert-{{ category }} alert-dismissible fade show">
                            {{ message }}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        </div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST" action="/login">
                <div class="mb-3">
                    <label class="form-label">Username</label>
                    <div class="input-group">
                        <span class="input-group-text">
                            <i class="fas fa-user"></i>
                        </span>
                        <input type="text" class="form-control" name="username" placeholder="Enter username" required>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Password</label>
                    <div class="input-group">
                        <span class="input-group-text">
                            <i class="fas fa-lock"></i>
                        </span>
                        <input type="password" class="form-control" name="password" placeholder="Enter password" required>
                    </div>
                </div>
                <div class="d-grid mb-3">
                    <button type="submit" class="btn btn-primary btn-lg">
                        <i class="fas fa-sign-in-alt me-2"></i>Login
                    </button>
                </div>
                <div class="text-center">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        Demo: admin / admin123
                    </small>
                </div>
            </form>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template_string(get_login_template())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = read_json(DATABASES['users'])
        for user in users:
            if user['username'] == username and check_password_hash(user['password'], password):
                if user.get('is_active', True):
                    user_obj = User(user)
                    login_user(user_obj)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Account is inactive', 'danger')
                    break
        
        flash('Invalid username or password', 'danger')
    
    return render_template_string(get_login_template())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    products = read_json(DATABASES['products'])
    customers = read_json(DATABASES['customers'])
    invoices = read_json(DATABASES['invoices'])
    quotations = read_json(DATABASES['quotations'])
    
    # Calculate totals
    total_sales = sum(invoice.get('total', 0) for invoice in invoices)
    pending_invoices = [inv for inv in invoices if inv.get('status') in ['pending', 'partial']]
    total_pending = sum(inv.get('balance', 0) for inv in pending_invoices)
    
    # Recent activities
    recent_invoices = sorted(invoices, key=lambda x: x.get('date', ''), reverse=True)[:5]
    recent_quotations = sorted(quotations, key=lambda x: x.get('date', ''), reverse=True)[:5]
    
    # Build stats HTML
    stats = [
        {'title': 'Total Products', 'value': len(products), 'icon': 'box', 'color': 'primary'},
        {'title': 'Total Customers', 'value': len(customers), 'icon': 'users', 'color': 'success'},
        {'title': 'Total Invoices', 'value': len(invoices), 'icon': 'file-invoice', 'color': 'warning'},
        {'title': 'Total Sales', 'value': f'৳{total_sales:,.2f}', 'icon': 'dollar-sign', 'color': 'info'},
        {'title': 'Pending Amount', 'value': f'৳{total_pending:,.2f}', 'icon': 'clock', 'color': 'danger'},
        {'title': 'Active Quotations', 'value': len([q for q in quotations if q.get('status') == 'pending']), 'icon': 'quote-right', 'color': 'secondary'}
    ]
    
    stats_html = ""
    for stat in stats:
        stats_html += f'''
        <div class="col-md-4 col-lg-2 mb-3">
            <div class="stat-card bg-{stat['color']} text-white p-3">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h6 class="mb-1">{stat['title']}</h6>
                        <h3 class="mb-0">{stat['value']}</h3>
                    </div>
                    <i class="fas fa-{stat['icon']} fa-2x opacity-50"></i>
                </div>
            </div>
        </div>
        '''
    
    # Build recent invoices HTML
    recent_invoices_html = ""
    if recent_invoices:
        for inv in recent_invoices:
            status_color = 'success' if inv.get('status') == 'paid' else 'warning'
            recent_invoices_html += f'''
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h6 class="mb-1">{inv.get('invoice_no', 'N/A')}</h6>
                    <small class="text-muted">{inv.get('customer_name', 'Customer')} • {inv.get('date', '')[:10]}</small>
                </div>
                <div class="text-end">
                    <h6 class="mb-1">৳{inv.get('total', 0):,.2f}</h6>
                    <span class="badge bg-{status_color}">
                        {inv.get('status', 'pending').title()}
                    </span>
                </div>
            </div>
            '''
    else:
        recent_invoices_html = '<div class="text-center py-4"><i class="fas fa-receipt fa-3x text-muted mb-3"></i><p class="text-muted">No invoices yet</p></div>'
    
    # Build recent quotations HTML
    recent_quotations_html = ""
    if recent_quotations:
        for quote in recent_quotations:
            status = quote.get('status', 'pending')
            if status == 'accepted':
                status_color = 'success'
            elif status == 'pending':
                status_color = 'info'
            else:
                status_color = 'secondary'
            
            recent_quotations_html += f'''
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <h6 class="mb-1">{quote.get('quotation_no', 'N/A')}</h6>
                    <small class="text-muted">{quote.get('customer_name', 'Customer')} • {quote.get('date', '')[:10]}</small>
                </div>
                <div class="text-end">
                    <h6 class="mb-1">৳{quote.get('total', 0):,.2f}</h6>
                    <span class="badge bg-{status_color}">
                        {quote.get('status', 'pending').title()}
                    </span>
                </div>
            </div>
            '''
    else:
        recent_quotations_html = '<div class="text-center py-4"><i class="fas fa-quote-left fa-3x text-muted mb-3"></i><p class="text-muted">No quotations yet</p></div>'
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-tachometer-alt me-2"></i>Dashboard</h2>
        <div class="text-muted">
            <i class="fas fa-calendar-alt me-1"></i>
            {datetime.now().strftime('%B %d, %Y')}
        </div>
    </div>
    
    <!-- Stats Cards -->
    <div class="row mb-4">
        {stats_html}
    </div>
    
    <!-- Quick Actions -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0"><i class="fas fa-bolt me-2"></i>Quick Actions</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3 col-6 mb-3">
                            <a href="/products/new" class="btn btn-primary w-100 py-3">
                                <i class="fas fa-plus-circle fa-2x mb-2"></i><br>
                                Add Product
                            </a>
                        </div>
                        <div class="col-md-3 col-6 mb-3">
                            <a href="/customers/new" class="btn btn-success w-100 py-3">
                                <i class="fas fa-user-plus fa-2x mb-2"></i><br>
                                Add Customer
                            </a>
                        </div>
                        <div class="col-md-3 col-6 mb-3">
                            <a href="/invoices/new" class="btn btn-warning w-100 py-3">
                                <i class="fas fa-file-invoice fa-2x mb-2"></i><br>
                                Create Invoice
                            </a>
                        </div>
                        <div class="col-md-3 col-6 mb-3">
                            <a href="/quotations/new" class="btn btn-info w-100 py-3">
                                <i class="fas fa-quote-left fa-2x mb-2"></i><br>
                                Create Quotation
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Activities -->
    <div class="row">
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-history me-2"></i>Recent Invoices</h5>
                    <a href="/invoices" class="btn btn-sm btn-primary">View All</a>
                </div>
                <div class="card-body">
                    {recent_invoices_html}
                </div>
            </div>
        </div>
        
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="fas fa-quote-right me-2"></i>Recent Quotations</h5>
                    <a href="/quotations" class="btn btn-sm btn-primary">View All</a>
                </div>
                <div class="card-body">
                    {recent_quotations_html}
                </div>
            </div>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Dashboard', 'dashboard', content))

@app.route('/products')
@login_required
def products():
    products_data = read_json(DATABASES['products'])
    categories = read_json(DATABASES['categories'])
    
    # Build products table
    products_table = ""
    for product in products_data:
        category = next((cat['name'] for cat in categories if cat['id'] == product.get('category_id', '')), 'N/A')
        status_badge = f'<span class="badge bg-success">In Stock</span>' if product.get('stock', 0) > 0 else f'<span class="badge bg-danger">Out of Stock</span>'
        
        products_table += f"""
        <tr>
            <td>{product.get('code', 'N/A')}</td>
            <td>
                <strong>{product.get('name', 'N/A')}</strong><br>
                <small class="text-muted">{product.get('description', '')}</small>
            </td>
            <td>{category}</td>
            <td>{product.get('unit', 'pcs')}</td>
            <td>{product.get('stock', 0)}</td>
            <td>৳{product.get('purchase_price', 0):.2f}</td>
            <td>৳{product.get('selling_price', 0):.2f}</td>
            <td>{status_badge}</td>
            <td>
                <a href="/products/edit/{product['id']}" class="btn btn-sm btn-warning">
                    <i class="fas fa-edit"></i>
                </a>
                <button onclick="deleteProduct('{product['id']}', '{product.get('name', '')}')" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-box me-2"></i>Products</h2>
        <a href="/products/new" class="btn btn-primary">
            <i class="fas fa-plus-circle me-1"></i>Add New Product
        </a>
    </div>
    
    <!-- Filter and Search -->
    <div class="card mb-4">
        <div class="card-body">
            <div class="row">
                <div class="col-md-4 mb-2">
                    <input type="text" id="searchProduct" class="form-control" placeholder="Search by name or code...">
                </div>
                <div class="col-md-3 mb-2">
                    <select id="filterCategory" class="form-select">
                        <option value="">All Categories</option>
                        {"".join([f'<option value="{cat["id"]}">{cat["name"]}</option>' for cat in categories])}
                    </select>
                </div>
                <div class="col-md-3 mb-2">
                    <select id="filterStatus" class="form-select">
                        <option value="">All Status</option>
                        <option value="in_stock">In Stock</option>
                        <option value="out_of_stock">Out of Stock</option>
                    </select>
                </div>
                <div class="col-md-2 mb-2">
                    <button class="btn btn-secondary w-100" onclick="resetFilters()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Products Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Code</th>
                            <th>Name & Description</th>
                            <th>Category</th>
                            <th>Unit</th>
                            <th>Stock</th>
                            <th>Purchase Price</th>
                            <th>Selling Price</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="productsTable">
                        {products_table if products_table else '<tr><td colspan="9" class="text-center py-4">No products found. <a href="/products/new">Add your first product</a></td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Delete</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete product <strong id="productName"></strong>?</p>
                    <p class="text-danger"><i class="fas fa-exclamation-triangle"></i> This action cannot be undone!</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <a href="#" id="confirmDelete" class="btn btn-danger">Delete Product</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function deleteProduct(id, name) {{
            document.getElementById('productName').textContent = name;
            document.getElementById('confirmDelete').href = '/products/delete/' + id;
            new bootstrap.Modal(document.getElementById('deleteModal')).show();
        }}
        
        function filterProducts() {{
            var search = $('#searchProduct').val().toLowerCase();
            var category = $('#filterCategory').val();
            var status = $('#filterStatus').val();
            
            $('#productsTable tr').each(function() {{
                var row = $(this);
                var name = row.find('td:eq(1)').text().toLowerCase();
                var catId = row.find('td:eq(2)').text().toLowerCase();
                var stock = parseInt(row.find('td:eq(4)').text());
                
                var show = true;
                
                if (search && name.indexOf(search) === -1) show = false;
                if (category && catId !== category) show = false;
                if (status === 'in_stock' && stock <= 0) show = false;
                if (status === 'out_of_stock' && stock > 0) show = false;
                
                if (show) row.show(); else row.hide();
            }});
        }}
        
        function resetFilters() {{
            $('#searchProduct').val('');
            $('#filterCategory').val('');
            $('#filterStatus').val('');
            filterProducts();
        }}
        
        $(document).ready(function() {{
            $('#searchProduct, #filterCategory, #filterStatus').on('keyup change', filterProducts);
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Products', 'products', content))

@app.route('/products/new', methods=['GET', 'POST'])
@login_required
def new_product():
    if request.method == 'POST':
        try:
            products = read_json(DATABASES['products'])
            
            # Generate product ID
            product_id = get_next_id(products, 'PROD')
            
            product_data = {
                'id': product_id,
                'code': request.form.get('code'),
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category_id': request.form.get('category_id'),
                'unit': request.form.get('unit'),
                'purchase_price': float(request.form.get('purchase_price', 0)),
                'selling_price': float(request.form.get('selling_price', 0)),
                'stock': float(request.form.get('stock', 0)),
                'min_stock': float(request.form.get('min_stock', 0)),
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            products.append(product_data)
            write_json(DATABASES['products'], products)
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            flash(f'Error adding product: {str(e)}', 'danger')
    
    categories = read_json(DATABASES['categories'])
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-box me-2"></i>Add New Product</h2>
        <a href="/products" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Products
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="productForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Product Code *</label>
                        <input type="text" class="form-control" name="code" required 
                               placeholder="e.g., AL-WIN-001">
                        <div class="form-text">Unique identifier for the product</div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Product Name *</label>
                        <input type="text" class="form-control" name="name" required 
                               placeholder="e.g., Aluminium Sliding Window">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Category *</label>
                        <select class="form-select" name="category_id" required>
                            <option value="">Select Category</option>
                            {"".join([f'<option value="{cat["id"]}">{cat["name"]}</option>' for cat in categories])}
                        </select>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Unit *</label>
                        <select class="form-select" name="unit" required>
                            <option value="pcs">Pieces</option>
                            <option value="sqft">Square Feet</option>
                            <option value="kg">Kilogram</option>
                            <option value="meter">Meter</option>
                            <option value="set">Set</option>
                            <option value="roll">Roll</option>
                        </select>
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" rows="3" 
                                  placeholder="Product description, specifications, etc."></textarea>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Purchase Price (৳) *</label>
                        <input type="number" class="form-control" name="purchase_price" 
                               step="0.01" min="0" required>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Selling Price (৳) *</label>
                        <input type="number" class="form-control" name="selling_price" 
                               step="0.01" min="0" required>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Stock Quantity *</label>
                        <input type="number" class="form-control" name="stock" 
                               step="0.01" min="0" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Minimum Stock Alert</label>
                        <input type="number" class="form-control" name="min_stock" 
                               step="0.01" min="0" value="0">
                        <div class="form-text">System will alert when stock goes below this level</div>
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Save Product
                        </button>
                        <button type="reset" class="btn btn-secondary">
                            <i class="fas fa-redo me-1"></i>Reset
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Add Product', 'products', content))

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    products = read_json(DATABASES['products'])
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        flash('Product not found!', 'danger')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        try:
            product_index = next(i for i, p in enumerate(products) if p['id'] == product_id)
            
            products[product_index] = {
                **product,
                'code': request.form.get('code'),
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category_id': request.form.get('category_id'),
                'unit': request.form.get('unit'),
                'purchase_price': float(request.form.get('purchase_price', 0)),
                'selling_price': float(request.form.get('selling_price', 0)),
                'stock': float(request.form.get('stock', 0)),
                'min_stock': float(request.form.get('min_stock', 0)),
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user.id
            }
            
            write_json(DATABASES['products'], products)
            flash('Product updated successfully!', 'success')
            return redirect(url_for('products'))
            
        except Exception as e:
            flash(f'Error updating product: {str(e)}', 'danger')
    
    categories = read_json(DATABASES['categories'])
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-edit me-2"></i>Edit Product</h2>
        <a href="/products" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Products
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="productForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Product Code *</label>
                        <input type="text" class="form-control" name="code" required 
                               value="{product.get('code', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Product Name *</label>
                        <input type="text" class="form-control" name="name" required 
                               value="{product.get('name', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Category *</label>
                        <select class="form-select" name="category_id" required>
                            <option value="">Select Category</option>
                            {"".join([f'<option value="{cat["id"]}" {"selected" if cat["id"] == product.get("category_id", "") else ""}>{cat["name"]}</option>' for cat in categories])}
                        </select>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Unit *</label>
                        <select class="form-select" name="unit" required>
                            <option value="pcs" {"selected" if product.get('unit') == 'pcs' else ""}>Pieces</option>
                            <option value="sqft" {"selected" if product.get('unit') == 'sqft' else ""}>Square Feet</option>
                            <option value="kg" {"selected" if product.get('unit') == 'kg' else ""}>Kilogram</option>
                            <option value="meter" {"selected" if product.get('unit') == 'meter' else ""}>Meter</option>
                            <option value="set" {"selected" if product.get('unit') == 'set' else ""}>Set</option>
                            <option value="roll" {"selected" if product.get('unit') == 'roll' else ""}>Roll</option>
                        </select>
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Description</label>
                        <textarea class="form-control" name="description" rows="3">{product.get('description', '')}</textarea>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Purchase Price (৳) *</label>
                        <input type="number" class="form-control" name="purchase_price" 
                               step="0.01" min="0" value="{product.get('purchase_price', 0)}" required>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Selling Price (৳) *</label>
                        <input type="number" class="form-control" name="selling_price" 
                               step="0.01" min="0" value="{product.get('selling_price', 0)}" required>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Stock Quantity *</label>
                        <input type="number" class="form-control" name="stock" 
                               step="0.01" min="0" value="{product.get('stock', 0)}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Minimum Stock Alert</label>
                        <input type="number" class="form-control" name="min_stock" 
                               step="0.01" min="0" value="{product.get('min_stock', 0)}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Last Updated</label>
                        <input type="text" class="form-control" readonly 
                               value="{product.get('updated_at', product.get('created_at', 'N/A'))[:16]}">
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Update Product
                        </button>
                        <a href="/products" class="btn btn-secondary">
                            <i class="fas fa-times me-1"></i>Cancel
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Edit Product', 'products', content))

@app.route('/products/delete/<product_id>')
@login_required
@permission_required('manage_products')
def delete_product(product_id):
    try:
        products = read_json(DATABASES['products'])
        products = [p for p in products if p['id'] != product_id]
        write_json(DATABASES['products'], products)
        
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting product: {str(e)}', 'danger')
    
    return redirect(url_for('products'))

@app.route('/customers')
@login_required
def customers():
    customers_data = read_json(DATABASES['customers'])
    
    # Build customers table
    customers_table = ""
    for customer in customers_data:
        # Calculate total purchases
        invoices = read_json(DATABASES['invoices'])
        customer_invoices = [inv for inv in invoices if inv.get('customer_id') == customer['id']]
        total_purchases = sum(inv.get('total', 0) for inv in customer_invoices)
        
        customers_table += f"""
        <tr>
            <td>
                <strong>{customer.get('name', 'N/A')}</strong><br>
                <small class="text-muted">{customer.get('email', '')}</small>
            </td>
            <td>{customer.get('phone', 'N/A')}</td>
            <td>{customer.get('address', 'N/A')[:50]}{'...' if len(customer.get('address', '')) > 50 else ''}</td>
            <td>{len(customer_invoices)}</td>
            <td>৳{total_purchases:,.2f}</td>
            <td>
                <span class="badge bg-{'success' if customer.get('type', 'retail') == 'retail' else 'primary'}">
                    {customer.get('type', 'retail').title()}
                </span>
            </td>
            <td>
                <a href="/customers/view/{customer['id']}" class="btn btn-sm btn-info">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="/customers/edit/{customer['id']}" class="btn btn-sm btn-warning">
                    <i class="fas fa-edit"></i>
                </a>
                <button onclick="deleteCustomer('{customer['id']}', '{customer.get('name', '')}')" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-users me-2"></i>Customers</h2>
        <a href="/customers/new" class="btn btn-primary">
            <i class="fas fa-plus-circle me-1"></i>Add New Customer
        </a>
    </div>
    
    <!-- Filter and Search -->
    <div class="card mb-4">
        <div class="card-body">
            <div class="row">
                <div class="col-md-6 mb-2">
                    <input type="text" id="searchCustomer" class="form-control" placeholder="Search by name, phone, or email...">
                </div>
                <div class="col-md-3 mb-2">
                    <select id="filterType" class="form-select">
                        <option value="">All Types</option>
                        <option value="retail">Retail</option>
                        <option value="wholesale">Wholesale</option>
                        <option value="contractor">Contractor</option>
                    </select>
                </div>
                <div class="col-md-3 mb-2">
                    <button class="btn btn-secondary w-100" onclick="resetFilters()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Customers Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Customer Details</th>
                            <th>Phone</th>
                            <th>Address</th>
                            <th>Total Invoices</th>
                            <th>Total Purchases</th>
                            <th>Type</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="customersTable">
                        {customers_table if customers_table else '<tr><td colspan="7" class="text-center py-4">No customers found. <a href="/customers/new">Add your first customer</a></td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Delete</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete customer <strong id="customerName"></strong>?</p>
                    <p class="text-danger"><i class="fas fa-exclamation-triangle"></i> All related invoices will also be deleted!</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <a href="#" id="confirmDelete" class="btn btn-danger">Delete Customer</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function deleteCustomer(id, name) {{
            document.getElementById('customerName').textContent = name;
            document.getElementById('confirmDelete').href = '/customers/delete/' + id;
            new bootstrap.Modal(document.getElementById('deleteModal')).show();
        }}
        
        function filterCustomers() {{
            var search = $('#searchCustomer').val().toLowerCase();
            var type = $('#filterType').val();
            
            $('#customersTable tr').each(function() {{
                var row = $(this);
                var name = row.find('td:eq(0)').text().toLowerCase();
                var phone = row.find('td:eq(1)').text().toLowerCase();
                var customerType = row.find('.badge').text().toLowerCase();
                
                var show = true;
                
                if (search && name.indexOf(search) === -1 && phone.indexOf(search) === -1) show = false;
                if (type && customerType !== type.toLowerCase()) show = false;
                
                if (show) row.show(); else row.hide();
            }});
        }}
        
        function resetFilters() {{
            $('#searchCustomer').val('');
            $('#filterType').val('');
            filterCustomers();
        }}
        
        $(document).ready(function() {{
            $('#searchCustomer, #filterType').on('keyup change', filterCustomers);
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Customers', 'customers', content))

@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        try:
            customers = read_json(DATABASES['customers'])
            
            # Generate customer ID
            customer_id = get_next_id(customers, 'CUST')
            
            customer_data = {
                'id': customer_id,
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'type': request.form.get('type', 'retail'),
                'company': request.form.get('company'),
                'tax_number': request.form.get('tax_number'),
                'notes': request.form.get('notes'),
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            customers.append(customer_data)
            write_json(DATABASES['customers'], customers)
            
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            flash(f'Error adding customer: {str(e)}', 'danger')
    
    content = """
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-user-plus me-2"></i>Add New Customer</h2>
        <a href="/customers" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Customers
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="customerForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Full Name *</label>
                        <input type="text" class="form-control" name="name" required 
                               placeholder="e.g., John Smith">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Email Address</label>
                        <input type="email" class="form-control" name="email" 
                               placeholder="customer@example.com">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Phone Number *</label>
                        <input type="text" class="form-control" name="phone" required 
                               placeholder="e.g., +880 1234 567890">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Customer Type</label>
                        <select class="form-select" name="type">
                            <option value="retail">Retail Customer</option>
                            <option value="wholesale">Wholesale</option>
                            <option value="contractor">Contractor</option>
                            <option value="dealer">Dealer</option>
                        </select>
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Address</label>
                        <textarea class="form-control" name="address" rows="3" 
                                  placeholder="Full address with city, postal code, etc."></textarea>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Company Name</label>
                        <input type="text" class="form-control" name="company" 
                               placeholder="Optional company name">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tax Number/VAT ID</label>
                        <input type="text" class="form-control" name="tax_number" 
                               placeholder="Optional tax identification">
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Notes</label>
                        <textarea class="form-control" name="notes" rows="2" 
                                  placeholder="Any additional notes about this customer"></textarea>
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Save Customer
                        </button>
                        <button type="reset" class="btn btn-secondary">
                            <i class="fas fa-redo me-1"></i>Reset
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Add Customer', 'customers', content))

@app.route('/customers/edit/<customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customers = read_json(DATABASES['customers'])
    customer = next((c for c in customers if c['id'] == customer_id), None)
    
    if not customer:
        flash('Customer not found!', 'danger')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        try:
            customer_index = next(i for i, c in enumerate(customers) if c['id'] == customer_id)
            
            customers[customer_index] = {
                **customer,
                'name': request.form.get('name'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'address': request.form.get('address'),
                'type': request.form.get('type', 'retail'),
                'company': request.form.get('company'),
                'tax_number': request.form.get('tax_number'),
                'notes': request.form.get('notes'),
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user.id
            }
            
            write_json(DATABASES['customers'], customers)
            flash('Customer updated successfully!', 'success')
            return redirect(url_for('customers'))
            
        except Exception as e:
            flash(f'Error updating customer: {str(e)}', 'danger')
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-edit me-2"></i>Edit Customer</h2>
        <a href="/customers" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Customers
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="customerForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Full Name *</label>
                        <input type="text" class="form-control" name="name" required 
                               value="{customer.get('name', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Email Address</label>
                        <input type="email" class="form-control" name="email" 
                               value="{customer.get('email', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Phone Number *</label>
                        <input type="text" class="form-control" name="phone" required 
                               value="{customer.get('phone', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Customer Type</label>
                        <select class="form-select" name="type">
                            <option value="retail" {"selected" if customer.get('type') == 'retail' else ""}>Retail Customer</option>
                            <option value="wholesale" {"selected" if customer.get('type') == 'wholesale' else ""}>Wholesale</option>
                            <option value="contractor" {"selected" if customer.get('type') == 'contractor' else ""}>Contractor</option>
                            <option value="dealer" {"selected" if customer.get('type') == 'dealer' else ""}>Dealer</option>
                        </select>
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Address</label>
                        <textarea class="form-control" name="address" rows="3">{customer.get('address', '')}</textarea>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Company Name</label>
                        <input type="text" class="form-control" name="company" 
                               value="{customer.get('company', '')}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Tax Number/VAT ID</label>
                        <input type="text" class="form-control" name="tax_number" 
                               value="{customer.get('tax_number', '')}">
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Notes</label>
                        <textarea class="form-control" name="notes" rows="2">{customer.get('notes', '')}</textarea>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Created On</label>
                        <input type="text" class="form-control" readonly 
                               value="{customer.get('created_at', 'N/A')[:16]}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Last Updated</label>
                        <input type="text" class="form-control" readonly 
                               value="{customer.get('updated_at', 'N/A')[:16]}">
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Update Customer
                        </button>
                        <a href="/customers" class="btn btn-secondary">
                            <i class="fas fa-times me-1"></i>Cancel
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Edit Customer', 'customers', content))

@app.route('/customers/view/<customer_id>')
@login_required
def view_customer(customer_id):
    customers = read_json(DATABASES['customers'])
    customer = next((c for c in customers if c['id'] == customer_id), None)
    
    if not customer:
        flash('Customer not found!', 'danger')
        return redirect(url_for('customers'))
    
    # Get customer invoices
    invoices = read_json(DATABASES['invoices'])
    customer_invoices = [inv for inv in invoices if inv.get('customer_id') == customer_id]
    
    # Calculate statistics
    total_invoices = len(customer_invoices)
    total_amount = sum(inv.get('total', 0) for inv in customer_invoices)
    total_paid = sum(inv.get('paid', 0) for inv in customer_invoices)
    total_balance = total_amount - total_paid
    
    # Recent invoices table
    recent_invoices_html = ""
    if customer_invoices:
        for inv in customer_invoices[:5]:
            status_badge = f'<span class="badge bg-success">Paid</span>' if inv.get('status') == 'paid' else f'<span class="badge bg-warning">{inv.get("status", "pending").title()}</span>'
            
            recent_invoices_html += f"""
            <tr>
                <td><a href="/invoices/view/{inv['id']}">{inv.get('invoice_no', 'N/A')}</a></td>
                <td>{inv.get('date', 'N/A')[:10]}</td>
                <td>৳{inv.get('total', 0):,.2f}</td>
                <td>৳{inv.get('paid', 0):,.2f}</td>
                <td>৳{inv.get('balance', 0):,.2f}</td>
                <td>{status_badge}</td>
            </tr>
            """
    else:
        recent_invoices_html = '<tr><td colspan="6" class="text-center py-4">No invoices found for this customer</td></tr>'
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-user me-2"></i>Customer Details</h2>
        <div>
            <a href="/invoices/new?customer_id={customer_id}" class="btn btn-primary">
                <i class="fas fa-plus-circle me-1"></i>New Invoice
            </a>
            <a href="/customers" class="btn btn-secondary">
                <i class="fas fa-arrow-left me-1"></i>Back
            </a>
        </div>
    </div>
    
    <!-- Customer Info Card -->
    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h4 class="mb-3">{customer.get('name', 'N/A')}</h4>
                            <p>
                                <i class="fas fa-phone text-muted me-2"></i>
                                {customer.get('phone', 'N/A')}
                            </p>
                            <p>
                                <i class="fas fa-envelope text-muted me-2"></i>
                                {customer.get('email', 'N/A')}
                            </p>
                            <p>
                                <i class="fas fa-building text-muted me-2"></i>
                                <span class="badge bg-{'success' if customer.get('type') == 'retail' else 'primary'}">
                                    {customer.get('type', 'retail').title()}
                                </span>
                            </p>
                        </div>
                        <div class="col-md-6">
                            <h6 class="mb-2">Address</h6>
                            <p class="text-muted">{customer.get('address', 'N/A')}</p>
                            
                            {f'<h6 class="mb-2 mt-3">Company</h6><p class="text-muted">{customer.get("company", "")}</p>' if customer.get('company') else ''}
                            {f'<h6 class="mb-2 mt-3">Tax ID</h6><p class="text-muted">{customer.get("tax_number", "")}</p>' if customer.get('tax_number') else ''}
                        </div>
                    </div>
                    
                    {f'<div class="mt-3"><h6>Notes:</h6><p class="text-muted">{customer.get("notes", "")}</p></div>' if customer.get('notes') else ''}
                    
                    <div class="mt-4">
                        <a href="/customers/edit/{customer_id}" class="btn btn-warning">
                            <i class="fas fa-edit me-1"></i>Edit Customer
                        </a>
                        <button onclick="deleteCustomer('{customer_id}', '{customer.get('name', '')}')" class="btn btn-danger">
                            <i class="fas fa-trash me-1"></i>Delete Customer
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Statistics -->
        <div class="col-md-4">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Invoices</h6>
                    <h2 class="mb-0">{total_invoices}</h2>
                </div>
            </div>
            
            <div class="card bg-success text-white mt-3">
                <div class="card-body">
                    <h6 class="card-title">Total Amount</h6>
                    <h2 class="mb-0">৳{total_amount:,.2f}</h2>
                </div>
            </div>
            
            <div class="card bg-info text-white mt-3">
                <div class="card-body">
                    <h6 class="card-title">Total Paid</h6>
                    <h2 class="mb-0">৳{total_paid:,.2f}</h2>
                </div>
            </div>
            
            <div class="card bg-{'danger' if total_balance > 0 else 'secondary'} text-white mt-3">
                <div class="card-body">
                    <h6 class="card-title">Balance Due</h6>
                    <h2 class="mb-0">৳{total_balance:,.2f}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Invoices -->
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0"><i class="fas fa-file-invoice me-2"></i>Recent Invoices</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Invoice No</th>
                            <th>Date</th>
                            <th>Total Amount</th>
                            <th>Paid</th>
                            <th>Balance</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recent_invoices_html}
                    </tbody>
                </table>
            </div>
            
            {f'<div class="text-center mt-3"><a href="/invoices?customer={customer_id}" class="btn btn-sm btn-primary">View All Invoices</a></div>' if customer_invoices else ''}
        </div>
    </div>
    
    <script>
        function deleteCustomer(id, name) {{
            if (confirm('Are you sure you want to delete customer ' + name + '?\\n\\nAll related invoices will also be deleted!')) {{
                window.location.href = '/customers/delete/' + id;
            }}
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Customer Details', 'customers', content))

@app.route('/customers/delete/<customer_id>')
@login_required
@permission_required('manage_customers')
def delete_customer(customer_id):
    try:
        # Delete customer
        customers = read_json(DATABASES['customers'])
        customers = [c for c in customers if c['id'] != customer_id]
        write_json(DATABASES['customers'], customers)
        
        # Delete customer invoices
        invoices = read_json(DATABASES['invoices'])
        invoices = [inv for inv in invoices if inv.get('customer_id') != customer_id]
        write_json(DATABASES['invoices'], invoices)
        
        flash('Customer and related invoices deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'danger')
    
    return redirect(url_for('customers'))

@app.route('/invoices')
@login_required
def invoices():
    invoices_data = read_json(DATABASES['invoices'])
    customers = read_json(DATABASES['customers'])
    
    # Build invoices table
    invoices_table = ""
    for inv in invoices_data:
        customer = next((c for c in customers if c['id'] == inv.get('customer_id', '')), {})
        customer_name = customer.get('name', 'Unknown Customer')
        
        # Determine status badge
        status = inv.get('status', 'pending')
        if status == 'paid':
            badge = 'success'
        elif status == 'partial':
            badge = 'warning'
        else:
            badge = 'danger'
        
        invoices_table += f"""
        <tr>
            <td>
                <a href="/invoices/view/{inv['id']}">
                    <strong>{inv.get('invoice_no', 'N/A')}</strong>
                </a><br>
                <small class="text-muted">{customer_name}</small>
            </td>
            <td>{inv.get('date', 'N/A')[:10]}</td>
            <td>৳{inv.get('subtotal', 0):,.2f}</td>
            <td>৳{inv.get('tax', 0):,.2f}</td>
            <td>৳{inv.get('total', 0):,.2f}</td>
            <td>
                <span class="badge bg-{badge}">
                    {inv.get('status', 'pending').title()}
                </span>
            </td>
            <td>
                <a href="/invoices/view/{inv['id']}" class="btn btn-sm btn-info">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="/invoices/print/{inv['id']}" target="_blank" class="btn btn-sm btn-secondary">
                    <i class="fas fa-print"></i>
                </a>
                <a href="/invoices/payment/{inv['id']}" class="btn btn-sm btn-success">
                    <i class="fas fa-money-bill"></i>
                </a>
                <button onclick="deleteInvoice('{inv['id']}', '{inv.get('invoice_no', '')}')" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
        """
    
    # Calculate totals
    total_invoices = len(invoices_data)
    total_amount = sum(inv.get('total', 0) for inv in invoices_data)
    total_paid = sum(inv.get('paid', 0) for inv in invoices_data)
    total_balance = total_amount - total_paid
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-file-invoice me-2"></i>Invoices</h2>
        <a href="/invoices/new" class="btn btn-primary">
            <i class="fas fa-plus-circle me-1"></i>Create New Invoice
        </a>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Invoices</h6>
                    <h2 class="mb-0">{total_invoices}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Amount</h6>
                    <h2 class="mb-0">৳{total_amount:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Paid</h6>
                    <h2 class="mb-0">৳{total_paid:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-{'danger' if total_balance > 0 else 'secondary'} text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Balance</h6>
                    <h2 class="mb-0">৳{total_balance:,.2f}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filter and Search -->
    <div class="card mb-4">
        <div class="card-body">
            <div class="row">
                <div class="col-md-4 mb-2">
                    <input type="text" id="searchInvoice" class="form-control" placeholder="Search by invoice no or customer...">
                </div>
                <div class="col-md-3 mb-2">
                    <select id="filterStatus" class="form-select">
                        <option value="">All Status</option>
                        <option value="paid">Paid</option>
                        <option value="pending">Pending</option>
                        <option value="partial">Partial</option>
                    </select>
                </div>
                <div class="col-md-3 mb-2">
                    <input type="date" id="filterDate" class="form-control">
                </div>
                <div class="col-md-2 mb-2">
                    <button class="btn btn-secondary w-100" onclick="resetFilters()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Invoices Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Invoice Details</th>
                            <th>Date</th>
                            <th>Subtotal</th>
                            <th>Tax</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="invoicesTable">
                        {invoices_table if invoices_table else '<tr><td colspan="7" class="text-center py-4">No invoices found. <a href="/invoices/new">Create your first invoice</a></td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Delete</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete invoice <strong id="invoiceNo"></strong>?</p>
                    <p class="text-danger"><i class="fas fa-exclamation-triangle"></i> This action cannot be undone!</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <a href="#" id="confirmDelete" class="btn btn-danger">Delete Invoice</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function deleteInvoice(id, invoiceNo) {{
            document.getElementById('invoiceNo').textContent = invoiceNo;
            document.getElementById('confirmDelete').href = '/invoices/delete/' + id;
            new bootstrap.Modal(document.getElementById('deleteModal')).show();
        }}
        
        function filterInvoices() {{
            var search = $('#searchInvoice').val().toLowerCase();
            var status = $('#filterStatus').val();
            var date = $('#filterDate').val();
            
            $('#invoicesTable tr').each(function() {{
                var row = $(this);
                var invoiceText = row.find('td:eq(0)').text().toLowerCase();
                var invoiceStatus = row.find('.badge').text().toLowerCase();
                var invoiceDate = row.find('td:eq(1)').text();
                
                var show = true;
                
                if (search && invoiceText.indexOf(search) === -1) show = false;
                if (status && invoiceStatus !== status.toLowerCase()) show = false;
                if (date && invoiceDate !== date) show = false;
                
                if (show) row.show(); else row.hide();
            }});
        }}
        
        function resetFilters() {{
            $('#searchInvoice').val('');
            $('#filterStatus').val('');
            $('#filterDate').val('');
            filterInvoices();
        }}
        
        $(document).ready(function() {{
            $('#searchInvoice, #filterStatus, #filterDate').on('keyup change', filterInvoices);
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Invoices', 'invoices', content))

@app.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    if request.method == 'POST':
        try:
            invoices = read_json(DATABASES['invoices'])
            products = read_json(DATABASES['products'])
            settings = read_json(DATABASES['settings'])[0]
            
            # Generate invoice number
            invoice_no = f"{settings.get('invoice_prefix', 'INV')}-{datetime.now().strftime('%Y%m%d')}-{len(invoices) + 1:04d}"
            
            # Get form data
            items = []
            item_data = request.form.getlist('item[]')
            quantity_data = request.form.getlist('quantity[]')
            price_data = request.form.getlist('price[]')
            
            for i in range(len(item_data)):
                if item_data[i] and quantity_data[i] and price_data[i]:
                    product = next((p for p in products if p['id'] == item_data[i]), None)
                    if product:
                        # Update product stock
                        product_index = next(j for j, p in enumerate(products) if p['id'] == item_data[i])
                        products[product_index]['stock'] -= float(quantity_data[i])
                        
                        items.append({
                            'product_id': product['id'],
                            'product_code': product.get('code', ''),
                            'product_name': product.get('name', ''),
                            'quantity': float(quantity_data[i]),
                            'unit': product.get('unit', 'pcs'),
                            'price': float(price_data[i]),
                            'total': float(quantity_data[i]) * float(price_data[i])
                        })
            
            subtotal = sum(item['total'] for item in items)
            tax_rate = float(request.form.get('tax_rate', settings.get('tax_rate', 5)))
            tax = subtotal * (tax_rate / 100)
            total = subtotal + tax
            paid = float(request.form.get('paid', 0))
            balance = total - paid
            
            invoice_data = {
                'id': str(uuid.uuid4()),
                'invoice_no': invoice_no,
                'customer_id': request.form.get('customer_id'),
                'customer_name': request.form.get('customer_name'),
                'customer_phone': request.form.get('customer_phone'),
                'customer_address': request.form.get('customer_address'),
                'date': request.form.get('date', datetime.now().isoformat()),
                'due_date': request.form.get('due_date'),
                'items': items,
                'subtotal': subtotal,
                'tax_rate': tax_rate,
                'tax': tax,
                'total': total,
                'paid': paid,
                'balance': balance,
                'status': 'paid' if balance == 0 else 'partial' if paid > 0 else 'pending',
                'notes': request.form.get('notes', ''),
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat()
            }
            
            invoices.append(invoice_data)
            write_json(DATABASES['invoices'], invoices)
            write_json(DATABASES['products'], products)
            
            # Add transaction record
            if paid > 0:
                transactions = read_json(DATABASES['transactions'])
                transaction = {
                    'id': str(uuid.uuid4()),
                    'invoice_id': invoice_data['id'],
                    'type': 'payment',
                    'amount': paid,
                    'payment_method': request.form.get('payment_method', 'cash'),
                    'notes': f'Payment for invoice {invoice_no}',
                    'created_at': datetime.now().isoformat(),
                    'created_by': current_user.id
                }
                transactions.append(transaction)
                write_json(DATABASES['transactions'], transactions)
            
            flash(f'Invoice {invoice_no} created successfully!', 'success')
            return redirect(url_for('view_invoice', invoice_id=invoice_data['id']))
            
        except Exception as e:
            flash(f'Error creating invoice: {str(e)}', 'danger')
    
    customers = read_json(DATABASES['customers'])
    products = read_json(DATABASES['products'])
    settings = read_json(DATABASES['settings'])[0]
    
    # Pre-select customer if provided in query string
    selected_customer = {}
    customer_id = request.args.get('customer_id')
    if customer_id:
        selected_customer = next((c for c in customers if c['id'] == customer_id), {})
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-file-invoice me-2"></i>Create New Invoice</h2>
        <a href="/invoices" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Invoices
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="invoiceForm">
                <!-- Customer Information -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h5><i class="fas fa-user me-2"></i>Customer Information</h5>
                    </div>
                    <div class="col-md-6 text-end">
                        <div class="input-group">
                            <span class="input-group-text">Date</span>
                            <input type="date" class="form-control" name="date" 
                                   value="{datetime.now().strftime('%Y-%m-%d')}" required>
                        </div>
                    </div>
                </div>
                
                <div class="row mb-4">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Select Customer *</label>
                        <select class="form-select" id="customerSelect" name="customer_id" required 
                                onchange="loadCustomerDetails(this.value)">
                            <option value="">Select a customer...</option>
                            {"".join([f'<option value="{cust["id"]}" {"selected" if cust.get("id") == customer_id else ""}>{cust["name"]} - {cust.get("phone", "")}</option>' for cust in customers])}
                        </select>
                        <div class="form-text">Or <a href="/customers/new" target="_blank">add new customer</a></div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Customer Name</label>
                        <input type="text" class="form-control" id="customerName" 
                               name="customer_name" value="{selected_customer.get('name', '')}" readonly>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Phone</label>
                        <input type="text" class="form-control" id="customerPhone" 
                               name="customer_phone" value="{selected_customer.get('phone', '')}" readonly>
                    </div>
                    
                    <div class="col-md-8 mb-3">
                        <label class="form-label">Address</label>
                        <input type="text" class="form-control" id="customerAddress" 
                               name="customer_address" value="{selected_customer.get('address', '')}" readonly>
                    </div>
                </div>
                
                <!-- Invoice Items -->
                <div class="row mb-4">
                    <div class="col-12">
                        <h5><i class="fas fa-shopping-cart me-2"></i>Invoice Items</h5>
                    </div>
                </div>
                
                <div class="table-responsive mb-3">
                    <table class="table table-bordered" id="itemsTable">
                        <thead class="table-dark">
                            <tr>
                                <th width="40%">Product</th>
                                <th width="15%">Quantity</th>
                                <th width="15%">Unit Price (৳)</th>
                                <th width="15%">Total (৳)</th>
                                <th width="15%">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="itemsBody">
                            <!-- Rows will be added dynamically -->
                        </tbody>
                        <tfoot>
                            <tr>
                                <td colspan="5">
                                    <button type="button" class="btn btn-sm btn-success" onclick="addItemRow()">
                                        <i class="fas fa-plus me-1"></i>Add Item
                                    </button>
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                
                <!-- Totals -->
                <div class="row justify-content-end">
                    <div class="col-md-6">
                        <table class="table table-bordered">
                            <tr>
                                <td><strong>Subtotal</strong></td>
                                <td class="text-end">৳<span id="subtotal">0.00</span></td>
                            </tr>
                            <tr>
                                <td>
                                    <strong>Tax Rate</strong>
                                    <input type="number" class="form-control form-control-sm d-inline-block w-50 ms-2" 
                                           id="taxRate" name="tax_rate" value="{settings.get('tax_rate', 5)}" step="0.1" min="0" max="100" onchange="calculateTotal()">
                                    %
                                </td>
                                <td class="text-end">৳<span id="taxAmount">0.00</span></td>
                            </tr>
                            <tr class="table-primary">
                                <td><strong>Total Amount</strong></td>
                                <td class="text-end">৳<span id="totalAmount">0.00</span></td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <!-- Payment Information -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h5><i class="fas fa-money-bill-wave me-2"></i>Payment Information</h5>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Amount Paid (৳)</label>
                        <input type="number" class="form-control" id="paidAmount" name="paid" 
                               step="0.01" min="0" value="0" onchange="updateBalance()">
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Payment Method</label>
                        <select class="form-select" name="payment_method">
                            <option value="cash">Cash</option>
                            <option value="bank">Bank Transfer</option>
                            <option value="card">Credit Card</option>
                            <option value="check">Check</option>
                            <option value="mobile">Mobile Banking</option>
                        </select>
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Due Date</label>
                        <input type="date" class="form-control" name="due_date" 
                               value="{(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}">
                    </div>
                    
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Balance Due (৳)</label>
                        <input type="number" class="form-control" id="balanceDue" readonly value="0">
                    </div>
                </div>
                
                <!-- Notes -->
                <div class="row mb-4">
                    <div class="col-12">
                        <label class="form-label">Notes</label>
                        <textarea class="form-control" name="notes" rows="3" placeholder="Any additional notes for this invoice..."></textarea>
                    </div>
                </div>
                
                <!-- Hidden Fields -->
                <input type="hidden" id="subtotalInput" name="subtotal" value="0">
                <input type="hidden" id="taxInput" name="tax" value="0">
                <input type="hidden" id="totalInput" name="total" value="0">
                
                <!-- Submit Buttons -->
                <div class="row">
                    <div class="col-12">
                        <button type="submit" class="btn btn-primary px-5">
                            <i class="fas fa-save me-1"></i>Save Invoice
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            <i class="fas fa-redo me-1"></i>Reset
                        </button>
                        <button type="button" class="btn btn-success" onclick="saveAndPrint()">
                            <i class="fas fa-print me-1"></i>Save & Print
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Product Modal for Selection -->
    <div class="modal fade" id="productModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Select Product</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Code</th>
                                    <th>Name</th>
                                    <th>Stock</th>
                                    <th>Price</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join([f'''
                                <tr>
                                    <td>{p.get('code', '')}</td>
                                    <td>{p.get('name', '')}</td>
                                    <td>{p.get('stock', 0)} {p.get('unit', 'pcs')}</td>
                                    <td>৳{p.get('selling_price', 0):.2f}</td>
                                    <td>
                                        <button type="button" class="btn btn-sm btn-primary" onclick="selectProduct('{p['id']}', '{p.get('name', '')}', {p.get('selling_price', 0)})">
                                            Select
                                        </button>
                                    </td>
                                </tr>
                                ''' for p in products if p.get('stock', 0) > 0])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentRow = null;
        let productOptions = {json.dumps([{'id': p['id'], 'name': p.get('name', ''), 'price': p.get('selling_price', 0), 'stock': p.get('stock', 0), 'unit': p.get('unit', 'pcs')} for p in products if p.get('stock', 0) > 0])};
        
        // Initialize with one empty row
        $(document).ready(function() {{
            addItemRow();
            loadCustomerDetails('{customer_id}');
        }});
        
        function loadCustomerDetails(customerId) {{
            if (!customerId) return;
            
            $.getJSON('/api/customer/' + customerId, function(data) {{
                if (data) {{
                    $('#customerName').val(data.name);
                    $('#customerPhone').val(data.phone);
                    $('#customerAddress').val(data.address);
                }}
            }});
        }}
        
        function addItemRow() {{
            const rowId = 'row_' + Date.now();
            const row = `
                <tr id="${{rowId}}">
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-primary mb-1" onclick="showProductModal('${{rowId}}')">
                            <i class="fas fa-search"></i> Select Product
                        </button>
                        <input type="hidden" name="item[]" id="item_${{rowId}}">
                        <div>
                            <strong id="productName_${{rowId}}">Select a product...</strong><br>
                            <small class="text-muted" id="productStock_${{rowId}}"></small>
                        </div>
                    </td>
                    <td>
                        <input type="number" class="form-control" name="quantity[]" 
                               id="quantity_${{rowId}}" step="0.01" min="0.01" 
                               onchange="calculateRowTotal('${{rowId}}')" required>
                    </td>
                    <td>
                        <input type="number" class="form-control" name="price[]" 
                               id="price_${{rowId}}" step="0.01" min="0" 
                               onchange="calculateRowTotal('${{rowId}}')" required>
                    </td>
                    <td>
                        <div class="input-group">
                            <span class="input-group-text">৳</span>
                            <input type="number" class="form-control" id="total_${{rowId}}" 
                                   readonly step="0.01">
                        </div>
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-danger" onclick="removeItemRow('${{rowId}}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
            $('#itemsBody').append(row);
        }}
        
        function showProductModal(rowId) {{
            currentRow = rowId;
            new bootstrap.Modal(document.getElementById('productModal')).show();
        }}
        
        function selectProduct(productId, productName, price) {{
            if (!currentRow) return;
            
            const product = productOptions.find(p => p.id === productId);
            if (product) {{
                $('#item_' + currentRow).val(productId);
                $('#productName_' + currentRow).text(productName);
                $('#productStock_' + currentRow).text('Stock: ' + product.stock + ' ' + product.unit);
                $('#price_' + currentRow).val(price);
                $('#quantity_' + currentRow).focus();
                
                bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
                calculateRowTotal(currentRow);
            }}
        }}
        
        function calculateRowTotal(rowId) {{
            const quantity = parseFloat($('#quantity_' + rowId).val()) || 0;
            const price = parseFloat($('#price_' + rowId).val()) || 0;
            const total = quantity * price;
            
            $('#total_' + rowId).val(total.toFixed(2));
            calculateTotal();
        }}
        
        function calculateTotal() {{
            let subtotal = 0;
            
            $('input[id^="total_"]').each(function() {{
                subtotal += parseFloat($(this).val()) || 0;
            }});
            
            const taxRate = parseFloat($('#taxRate').val()) || 0;
            const tax = subtotal * (taxRate / 100);
            const total = subtotal + tax;
            
            $('#subtotal').text(subtotal.toFixed(2));
            $('#taxAmount').text(tax.toFixed(2));
            $('#totalAmount').text(total.toFixed(2));
            
            $('#subtotalInput').val(subtotal);
            $('#taxInput').val(tax);
            $('#totalInput').val(total);
            
            updateBalance();
        }}
        
        function updateBalance() {{
            const total = parseFloat($('#totalInput').val()) || 0;
            const paid = parseFloat($('#paidAmount').val()) || 0;
            const balance = total - paid;
            
            $('#balanceDue').val(balance.toFixed(2));
        }}
        
        function removeItemRow(rowId) {{
            $('#' + rowId).remove();
            calculateTotal();
        }}
        
        function resetForm() {{
            if (confirm('Are you sure you want to reset the form? All entered data will be lost.')) {{
                $('#itemsBody').empty();
                addItemRow();
                $('#customerSelect').val('');
                $('#customerName, #customerPhone, #customerAddress').val('');
                $('#paidAmount').val(0);
                $('textarea[name="notes"]').val('');
                calculateTotal();
            }}
        }}
        
        function saveAndPrint() {{
            // First save the form, then redirect to print
            $('#invoiceForm').submit();
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Create Invoice', 'invoices', content))

@app.route('/api/customer/<customer_id>')
@login_required
def get_customer_details(customer_id):
    customers = read_json(DATABASES['customers'])
    customer = next((c for c in customers if c['id'] == customer_id), None)
    
    if customer:
        return jsonify({
            'name': customer.get('name', ''),
            'phone': customer.get('phone', ''),
            'address': customer.get('address', ''),
            'email': customer.get('email', '')
        })
    return jsonify({}), 404
    # Continue from previous code...

@app.route('/invoices/view/<invoice_id>')
@login_required
def view_invoice(invoice_id):
    invoices = read_json(DATABASES['invoices'])
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if not invoice:
        flash('Invoice not found!', 'danger')
        return redirect(url_for('invoices'))
    
    # Get customer details
    customers = read_json(DATABASES['customers'])
    customer = next((c for c in customers if c['id'] == invoice.get('customer_id', '')), {})
    
    # Get transactions
    transactions = read_json(DATABASES['transactions'])
    invoice_transactions = [t for t in transactions if t.get('invoice_id') == invoice_id]
    
    # Build items table
    items_table = ""
    for item in invoice.get('items', []):
        items_table += f"""
        <tr>
            <td>{item.get('product_code', 'N/A')}</td>
            <td>{item.get('product_name', 'N/A')}</td>
            <td class="text-end">{item.get('quantity', 0)} {item.get('unit', 'pcs')}</td>
            <td class="text-end">৳{item.get('price', 0):,.2f}</td>
            <td class="text-end">৳{item.get('total', 0):,.2f}</td>
        </tr>
        """
    
    # Build transactions table
    transactions_table = ""
    if invoice_transactions:
        for trans in invoice_transactions:
            trans_type = trans.get('type', 'payment')
            if trans_type == 'payment':
                badge = 'success'
            elif trans_type == 'refund':
                badge = 'danger'
            else:
                badge = 'info'
            
            transactions_table += f"""
            <tr>
                <td>{trans.get('created_at', '')[:16]}</td>
                <td><span class="badge bg-{badge}">{trans_type.title()}</span></td>
                <td>{trans.get('payment_method', 'N/A')}</td>
                <td class="text-end">৳{trans.get('amount', 0):,.2f}</td>
                <td>{trans.get('notes', '')}</td>
            </tr>
            """
    else:
        transactions_table = '<tr><td colspan="5" class="text-center py-4">No transactions found</td></tr>'
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-file-invoice me-2"></i>Invoice Details</h2>
        <div>
            <a href="/invoices/print/{invoice_id}" target="_blank" class="btn btn-secondary">
                <i class="fas fa-print me-1"></i>Print
            </a>
            <a href="/invoices" class="btn btn-primary">
                <i class="fas fa-arrow-left me-1"></i>Back to Invoices
            </a>
        </div>
    </div>
    
    <!-- Invoice Header -->
    <div class="card mb-4">
        <div class="invoice-header">
            <div class="row">
                <div class="col-md-6">
                    <h3 class="mb-1">{invoice.get('invoice_no', 'N/A')}</h3>
                    <p class="mb-0">Invoice Date: {invoice.get('date', 'N/A')[:10]}</p>
                    <p class="mb-0">Due Date: {invoice.get('due_date', 'N/A')[:10] if invoice.get('due_date') else 'N/A'}</p>
                </div>
                <div class="col-md-6 text-end">
                    <h1 class="mb-1">৳{invoice.get('total', 0):,.2f}</h1>
                    <span class="badge bg-{'success' if invoice.get('status') == 'paid' else 'warning' if invoice.get('status') == 'partial' else 'danger'} fs-6">
                        {invoice.get('status', 'pending').upper()}
                    </span>
                </div>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h5>Bill To:</h5>
                    <address>
                        <strong>{invoice.get('customer_name', 'N/A')}</strong><br>
                        {invoice.get('customer_phone', 'N/A')}<br>
                        {invoice.get('customer_address', 'N/A')}
                    </address>
                </div>
                <div class="col-md-6 text-end">
                    <h5>From:</h5>
                    <address>
                        <strong>MEHEDI THAI ALUMINIUM & GLASS</strong><br>
                        123 Business Street, City, Country<br>
                        Phone: +880 1234 567890<br>
                        Email: info@aluminiumglass.com
                    </address>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Invoice Items -->
    <div class="card mb-4">
        <div class="card-header">
            <h5 class="mb-0">Invoice Items</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-bordered">
                    <thead class="table-dark">
                        <tr>
                            <th>Code</th>
                            <th>Description</th>
                            <th class="text-end">Quantity</th>
                            <th class="text-end">Unit Price</th>
                            <th class="text-end">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_table}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Subtotal:</strong></td>
                            <td class="text-end"><strong>৳{invoice.get('subtotal', 0):,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Tax ({invoice.get('tax_rate', 0)}%):</strong></td>
                            <td class="text-end"><strong>৳{invoice.get('tax', 0):,.2f}</strong></td>
                        </tr>
                        <tr class="table-primary">
                            <td colspan="4" class="text-end"><strong>Total Amount:</strong></td>
                            <td class="text-end"><strong>৳{invoice.get('total', 0):,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Amount Paid:</strong></td>
                            <td class="text-end"><strong class="text-success">৳{invoice.get('paid', 0):,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Balance Due:</strong></td>
                            <td class="text-end"><strong class="text-danger">৳{invoice.get('balance', 0):,.2f}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Payment Transactions -->
    <div class="card mb-4">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Payment Transactions</h5>
            <a href="/invoices/payment/{invoice_id}" class="btn btn-sm btn-success">
                <i class="fas fa-money-bill-wave me-1"></i>Add Payment
            </a>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Method</th>
                            <th class="text-end">Amount</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {transactions_table}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Notes -->
    {f'''<div class="card mb-4">
        <div class="card-header">
            <h5 class="mb-0">Notes</h5>
        </div>
        <div class="card-body">
            <p>{invoice.get('notes', '')}</p>
        </div>
    </div>''' if invoice.get('notes') else ''}
    
    <!-- Actions -->
    <div class="card">
        <div class="card-body text-center">
            <a href="/invoices/print/{invoice_id}" target="_blank" class="btn btn-primary me-2">
                <i class="fas fa-print me-1"></i>Print Invoice
            </a>
            <a href="/invoices/payment/{invoice_id}" class="btn btn-success me-2">
                <i class="fas fa-money-bill-wave me-1"></i>Record Payment
            </a>
            <a href="/invoices/send/{invoice_id}" class="btn btn-info me-2">
                <i class="fas fa-paper-plane me-1"></i>Send to Customer
            </a>
            <button onclick="deleteInvoice('{invoice_id}', '{invoice.get('invoice_no', '')}')" class="btn btn-danger">
                <i class="fas fa-trash me-1"></i>Delete Invoice
            </button>
        </div>
    </div>
    
    <script>
        function deleteInvoice(id, invoiceNo) {{
            if (confirm('Are you sure you want to delete invoice ' + invoiceNo + '?\\n\\nThis action cannot be undone!')) {{
                window.location.href = '/invoices/delete/' + id;
            }}
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Invoice Details', 'invoices', content))

@app.route('/invoices/print/<invoice_id>')
@login_required
def print_invoice(invoice_id):
    invoices = read_json(DATABASES['invoices'])
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if not invoice:
        flash('Invoice not found!', 'danger')
        return redirect(url_for('invoices'))
    
    settings = read_json(DATABASES['settings'])[0]
    
    # Build items table for print
    items_rows = ""
    for idx, item in enumerate(invoice.get('items', []), 1):
        items_rows += f"""
        <tr>
            <td class="text-center">{idx}</td>
            <td>{item.get('product_name', '')}</td>
            <td class="text-center">{item.get('unit', 'pcs')}</td>
            <td class="text-center">{item.get('quantity', 0)}</td>
            <td class="text-end">৳{item.get('price', 0):,.2f}</td>
            <td class="text-end">৳{item.get('total', 0):,.2f}</td>
        </tr>
        """
    
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice {invoice.get('invoice_no', '')}</title>
        <style>
            @media print {{
                @page {{
                    margin: 0.5in;
                    size: A4 portrait;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 12px;
                    color: #000;
                }}
                .no-print {{ display: none !important; }}
                .print-only {{ display: block !important; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                color: #000;
                margin: 0;
                padding: 20px;
            }}
            .invoice-header {{
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .invoice-footer {{
                border-top: 2px dashed #ddd;
                margin-top: 50px;
                padding-top: 20px;
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .table th, .table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .table th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            .text-end {{ text-align: right !important; }}
            .text-center {{ text-align: center !important; }}
            .total-table {{ width: 300px; float: right; }}
            .clearfix {{ clear: both; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; text-align: center;">
            <button onclick="window.print()" class="btn btn-primary">Print Invoice</button>
            <button onclick="window.close()" class="btn btn-secondary">Close</button>
        </div>
        
        <!-- Invoice Header -->
        <div class="invoice-header">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 50%;">
                        <h1 style="color: #2c3e50; margin: 0;">{settings.get('shop_name', 'MEHEDI THAI ALUMINIUM & GLASS')}</h1>
                        <p style="margin: 5px 0;">{settings.get('shop_address', '123 Business Street, City, Country')}</p>
                        <p style="margin: 5px 0;">Phone: {settings.get('shop_phone', '+880 1234 567890')}</p>
                        <p style="margin: 5px 0;">Email: {settings.get('shop_email', 'info@aluminiumglass.com')}</p>
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <h2 style="color: #3498db; margin: 0;">INVOICE</h2>
                        <p style="margin: 5px 0;"><strong>Invoice No:</strong> {invoice.get('invoice_no', 'N/A')}</p>
                        <p style="margin: 5px 0;"><strong>Invoice Date:</strong> {invoice.get('date', 'N/A')[:10]}</p>
                        <p style="margin: 5px 0;"><strong>Due Date:</strong> {invoice.get('due_date', 'N/A')[:10] if invoice.get('due_date') else 'N/A'}</p>
                        <p style="margin: 5px 0;">
                            <strong>Status:</strong> 
                            <span style="color: {'#27ae60' if invoice.get('status') == 'paid' else '#e74c3c' if invoice.get('status') == 'pending' else '#f39c12'}">
                                {invoice.get('status', 'pending').upper()}
                            </span>
                        </p>
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Bill To / Ship To -->
        <table style="width: 100%; margin-bottom: 30px;">
            <tr>
                <td style="width: 50%; vertical-align: top;">
                    <h3 style="margin: 0 0 10px 0;">Bill To:</h3>
                    <p style="margin: 5px 0;"><strong>{invoice.get('customer_name', 'N/A')}</strong></p>
                    <p style="margin: 5px 0;">{invoice.get('customer_phone', 'N/A')}</p>
                    <p style="margin: 5px 0; white-space: pre-line;">{invoice.get('customer_address', 'N/A')}</p>
                </td>
                <td style="width: 50%; vertical-align: top; text-align: right;">
                    <h3 style="margin: 0 0 10px 0;">Ship To:</h3>
                    <p style="margin: 5px 0;"><strong>{invoice.get('customer_name', 'N/A')}</strong></p>
                    <p style="margin: 5px 0;">{invoice.get('customer_phone', 'N/A')}</p>
                    <p style="margin: 5px 0; white-space: pre-line;">{invoice.get('customer_address', 'N/A')}</p>
                </td>
            </tr>
        </table>
        
        <!-- Invoice Items -->
        <table class="table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 45%;">Description</th>
                    <th style="width: 10%;">Unit</th>
                    <th style="width: 10%;">Qty</th>
                    <th style="width: 15%;">Unit Price</th>
                    <th style="width: 15%;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>
        
        <div class="clearfix"></div>
        
        <!-- Totals -->
        <table class="total-table">
            <tr>
                <td style="text-align: right;"><strong>Subtotal:</strong></td>
                <td style="text-align: right;">৳{invoice.get('subtotal', 0):,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: right;"><strong>Tax ({invoice.get('tax_rate', 0)}%):</strong></td>
                <td style="text-align: right;">৳{invoice.get('tax', 0):,.2f}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="text-align: right;"><strong>Total:</strong></td>
                <td style="text-align: right;"><strong>৳{invoice.get('total', 0):,.2f}</strong></td>
            </tr>
            <tr>
                <td style="text-align: right;"><strong>Paid:</strong></td>
                <td style="text-align: right;">৳{invoice.get('paid', 0):,.2f}</td>
            </tr>
            <tr style="border-top: 2px solid #000;">
                <td style="text-align: right;"><strong>Balance Due:</strong></td>
                <td style="text-align: right;"><strong>৳{invoice.get('balance', 0):,.2f}</strong></td>
            </tr>
        </table>
        
        <div class="clearfix"></div>
        
        <!-- Notes -->
        {f'''<div style="margin-top: 50px;">
            <h4>Notes:</h4>
            <p style="white-space: pre-line;">{invoice.get('notes', '')}</p>
        </div>''' if invoice.get('notes') else ''}
        
        <!-- Terms & Conditions -->
        <div class="invoice-footer">
            <div style="width: 100%;">
                <p><strong>Terms & Conditions:</strong></p>
                <p>1. Payment is due within 30 days from invoice date.</p>
                <p>2. Late payments are subject to 1.5% monthly interest.</p>
                <p>3. Goods sold are not returnable unless defective.</p>
                <p>4. This is a computer generated invoice.</p>
            </div>
            
            <div style="margin-top: 50px; text-align: center;">
                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; text-align: center;">
                            <p>_________________________</p>
                            <p><strong>Customer Signature</strong></p>
                        </td>
                        <td style="width: 50%; text-align: center;">
                            <p>_________________________</p>
                            <p><strong>Authorized Signature</strong></p>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px; font-size: 10px; color: #666;">
                <p>Thank you for your business!</p>
                <p>{settings.get('shop_name', 'MEHEDI THAI ALUMINIUM & GLASS')} | {settings.get('shop_phone', '+880 1234 567890')} | {settings.get('shop_email', 'info@aluminiumglass.com')}</p>
            </div>
        </div>
        
        <script>
            window.onload = function() {{
                window.print();
            }};
        </script>
    </body>
    </html>
    """
    
    return render_template_string(content)

@app.route('/invoices/payment/<invoice_id>', methods=['GET', 'POST'])
@login_required
def invoice_payment(invoice_id):
    invoices = read_json(DATABASES['invoices'])
    invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
    
    if not invoice:
        flash('Invoice not found!', 'danger')
        return redirect(url_for('invoices'))
    
    if request.method == 'POST':
        try:
            # Get payment details
            payment_amount = float(request.form.get('amount', 0))
            payment_method = request.form.get('payment_method', 'cash')
            notes = request.form.get('notes', '')
            
            if payment_amount <= 0:
                flash('Payment amount must be greater than 0!', 'danger')
                return redirect(f'/invoices/payment/{invoice_id}')
            
            # Update invoice
            invoice_index = next(i for i, inv in enumerate(invoices) if inv['id'] == invoice_id)
            
            new_paid = invoice['paid'] + payment_amount
            new_balance = invoice['total'] - new_paid
            
            invoices[invoice_index]['paid'] = new_paid
            invoices[invoice_index]['balance'] = new_balance
            
            if new_balance == 0:
                invoices[invoice_index]['status'] = 'paid'
            elif new_paid > 0:
                invoices[invoice_index]['status'] = 'partial'
            else:
                invoices[invoice_index]['status'] = 'pending'
            
            # Add transaction
            transactions = read_json(DATABASES['transactions'])
            transaction = {
                'id': str(uuid.uuid4()),
                'invoice_id': invoice_id,
                'type': 'payment',
                'amount': payment_amount,
                'payment_method': payment_method,
                'notes': notes or f'Payment for invoice {invoice.get("invoice_no", "")}',
                'created_at': datetime.now().isoformat(),
                'created_by': current_user.id
            }
            transactions.append(transaction)
            
            # Write to database
            write_json(DATABASES['invoices'], invoices)
            write_json(DATABASES['transactions'], transactions)
            
            flash(f'Payment of ৳{payment_amount:,.2f} recorded successfully!', 'success')
            return redirect(url_for('view_invoice', invoice_id=invoice_id))
            
        except Exception as e:
            flash(f'Error recording payment: {str(e)}', 'danger')
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-money-bill-wave me-2"></i>Record Payment</h2>
        <a href="/invoices/view/{invoice_id}" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Invoice
        </a>
    </div>
    
    <div class="row">
        <div class="col-md-8">
            <div class="card">
                <div class="card-body">
                    <form method="POST" id="paymentForm">
                        <!-- Invoice Summary -->
                        <div class="alert alert-info">
                            <div class="row">
                                <div class="col-md-4">
                                    <strong>Invoice No:</strong><br>
                                    {invoice.get('invoice_no', 'N/A')}
                                </div>
                                <div class="col-md-4">
                                    <strong>Customer:</strong><br>
                                    {invoice.get('customer_name', 'N/A')}
                                </div>
                                <div class="col-md-4">
                                    <strong>Total Amount:</strong><br>
                                    ৳{invoice.get('total', 0):,.2f}
                                </div>
                            </div>
                        </div>
                        
                        <!-- Payment Details -->
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Amount Paid *</label>
                                <div class="input-group">
                                    <span class="input-group-text">৳</span>
                                    <input type="number" class="form-control" name="amount" 
                                           id="paymentAmount" step="0.01" min="0.01" 
                                           max="{invoice.get('balance', 0)}" required>
                                </div>
                                <div class="form-text">
                                    Maximum payment: ৳{invoice.get('balance', 0):,.2f}
                                </div>
                            </div>
                            
                            <div class="col-md-6">
                                <label class="form-label">Payment Method *</label>
                                <select class="form-select" name="payment_method" required>
                                    <option value="cash">Cash</option>
                                    <option value="bank">Bank Transfer</option>
                                    <option value="card">Credit/Debit Card</option>
                                    <option value="check">Check</option>
                                    <option value="mobile">Mobile Banking</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                        </div>
                        
                        <div class="row mb-3">
                            <div class="col-12">
                                <label class="form-label">Notes</label>
                                <textarea class="form-control" name="notes" rows="3" 
                                          placeholder="Payment reference, transaction ID, or any additional notes..."></textarea>
                            </div>
                        </div>
                        
                        <!-- Quick Amount Buttons -->
                        <div class="row mb-4">
                            <div class="col-12">
                                <label class="form-label">Quick Amount:</label>
                                <div class="btn-group" role="group">
                                    <button type="button" class="btn btn-outline-primary" onclick="setPaymentAmount({invoice.get('balance', 0)})">
                                        Pay Full (৳{invoice.get('balance', 0):,.2f})
                                    </button>
                                    <button type="button" class="btn btn-outline-primary" onclick="setPaymentAmount({invoice.get('balance', 0) / 2})">
                                        Pay Half (৳{invoice.get('balance', 0) / 2:,.2f})
                                    </button>
                                    <button type="button" class="btn btn-outline-primary" onclick="setPaymentAmount(1000)">
                                        ৳1,000
                                    </button>
                                    <button type="button" class="btn btn-outline-primary" onclick="setPaymentAmount(5000)">
                                        ৳5,000
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Summary -->
                        <div class="card bg-light mb-4">
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-6">
                                        <p class="mb-1">Current Balance: <strong>৳{invoice.get('balance', 0):,.2f}</strong></p>
                                        <p class="mb-1">Amount to Pay: <strong id="amountToPay">0.00</strong></p>
                                    </div>
                                    <div class="col-md-6">
                                        <p class="mb-1">New Balance: <strong id="newBalance">{invoice.get('balance', 0):,.2f}</strong></p>
                                        <p class="mb-1">New Status: <strong id="newStatus">{invoice.get('status', 'pending').title()}</strong></p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-12">
                                <button type="submit" class="btn btn-success px-4">
                                    <i class="fas fa-check-circle me-1"></i>Record Payment
                                </button>
                                <a href="/invoices/view/{invoice_id}" class="btn btn-secondary">
                                    Cancel
                                </a>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        
        <!-- Payment History -->
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Payment History</h5>
                </div>
                <div class="card-body">
                    <div class="list-group list-group-flush">
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <small>Invoice Total</small><br>
                                <strong>৳{invoice.get('total', 0):,.2f}</strong>
                            </div>
                        </div>
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <small>Already Paid</small><br>
                                <strong class="text-success">৳{invoice.get('paid', 0):,.2f}</strong>
                            </div>
                        </div>
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <small>Current Balance</small><br>
                                <strong class="text-danger">৳{invoice.get('balance', 0):,.2f}</strong>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <h6>Payment Progress</h6>
                        <div class="progress" style="height: 20px;">
                            <div class="progress-bar bg-success" role="progressbar" 
                                 style="width: {invoice.get('paid', 0) / invoice.get('total', 1) * 100 if invoice.get('total', 0) > 0 else 0}%">
                                {invoice.get('paid', 0) / invoice.get('total', 1) * 100 if invoice.get('total', 0) > 0 else 0:.1f}%
                            </div>
                        </div>
                        <div class="d-flex justify-content-between mt-1">
                            <small>Paid: ৳{invoice.get('paid', 0):,.2f}</small>
                            <small>Total: ৳{invoice.get('total', 0):,.2f}</small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function setPaymentAmount(amount) {{
            const maxAmount = {invoice.get('balance', 0)};
            const actualAmount = Math.min(amount, maxAmount);
            $('#paymentAmount').val(actualAmount.toFixed(2));
            updateSummary();
        }}
        
        function updateSummary() {{
            const currentBalance = {invoice.get('balance', 0)};
            const paymentAmount = parseFloat($('#paymentAmount').val()) || 0;
            const newBalance = currentBalance - paymentAmount;
            
            $('#amountToPay').text('৳' + paymentAmount.toFixed(2));
            $('#newBalance').text('৳' + newBalance.toFixed(2));
            
            let newStatus = 'Pending';
            if (newBalance <= 0) {{
                newStatus = 'Paid';
            }} else if (paymentAmount > 0) {{
                newStatus = 'Partial';
            }}
            $('#newStatus').text(newStatus);
        }}
        
        $(document).ready(function() {{
            $('#paymentAmount').on('input', updateSummary);
            updateSummary();
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Record Payment', 'invoices', content))

@app.route('/invoices/delete/<invoice_id>')
@login_required
@permission_required('manage_invoices')
def delete_invoice(invoice_id):
    try:
        invoices = read_json(DATABASES['invoices'])
        invoice = next((inv for inv in invoices if inv['id'] == invoice_id), None)
        
        if invoice:
            # Restore product stock
            products = read_json(DATABASES['products'])
            for item in invoice.get('items', []):
                product = next((p for p in products if p['id'] == item.get('product_id', '')), None)
                if product:
                    product_index = next(i for i, p in enumerate(products) if p['id'] == product['id'])
                    products[product_index]['stock'] += item.get('quantity', 0)
            
            # Remove invoice
            invoices = [inv for inv in invoices if inv['id'] != invoice_id]
            
            # Remove related transactions
            transactions = read_json(DATABASES['transactions'])
            transactions = [t for t in transactions if t.get('invoice_id') != invoice_id]
            
            write_json(DATABASES['invoices'], invoices)
            write_json(DATABASES['products'], products)
            write_json(DATABASES['transactions'], transactions)
            
            flash(f'Invoice deleted successfully!', 'success')
        else:
            flash('Invoice not found!', 'danger')
    except Exception as e:
        flash(f'Error deleting invoice: {str(e)}', 'danger')
    
    return redirect(url_for('invoices'))

@app.route('/quotations')
@login_required
def quotations():
    quotations_data = read_json(DATABASES['quotations'])
    customers = read_json(DATABASES['customers'])
    
    # Build quotations table
    quotations_table = ""
    for quote in quotations_data:
        customer = next((c for c in customers if c['id'] == quote.get('customer_id', '')), {})
        customer_name = customer.get('name', 'Unknown Customer')
        
        # Determine status badge
        status = quote.get('status', 'pending')
        if status == 'accepted':
            badge = 'success'
        elif status == 'pending':
            badge = 'warning'
        elif status == 'converted':
            badge = 'info'
        else:
            badge = 'secondary'
        
        quotations_table += f"""
        <tr>
            <td>
                <a href="/quotations/view/{quote['id']}">
                    <strong>{quote.get('quotation_no', 'N/A')}</strong>
                </a><br>
                <small class="text-muted">{customer_name}</small>
            </td>
            <td>{quote.get('date', 'N/A')[:10]}</td>
            <td>{quote.get('valid_until', 'N/A')[:10]}</td>
            <td>৳{quote.get('total', 0):,.2f}</td>
            <td>
                <span class="badge bg-{badge}">
                    {quote.get('status', 'pending').title()}
                </span>
            </td>
            <td>
                <a href="/quotations/view/{quote['id']}" class="btn btn-sm btn-info">
                    <i class="fas fa-eye"></i>
                </a>
                <a href="/quotations/print/{quote['id']}" target="_blank" class="btn btn-sm btn-secondary">
                    <i class="fas fa-print"></i>
                </a>
                <button onclick="convertToInvoice('{quote['id']}')" class="btn btn-sm btn-success">
                    <i class="fas fa-file-invoice"></i>
                </button>
            </td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-quote-right me-2"></i>Quotations</h2>
        <a href="/quotations/new" class="btn btn-primary">
            <i class="fas fa-plus-circle me-1"></i>Create New Quotation
        </a>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Quotations</h6>
                    <h2 class="mb-0">{len(quotations_data)}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-warning text-white">
                <div class="card-body">
                    <h6 class="card-title">Pending</h6>
                    <h2 class="mb-0">{len([q for q in quotations_data if q.get('status') == 'pending'])}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h6 class="card-title">Accepted</h6>
                    <h2 class="mb-0">{len([q for q in quotations_data if q.get('status') == 'accepted'])}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h6 class="card-title">Converted</h6>
                    <h2 class="mb-0">{len([q for q in quotations_data if q.get('status') == 'converted'])}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Filter and Search -->
    <div class="card mb-4">
        <div class="card-body">
            <div class="row">
                <div class="col-md-4 mb-2">
                    <input type="text" id="searchQuotation" class="form-control" placeholder="Search by quotation no or customer...">
                </div>
                <div class="col-md-3 mb-2">
                    <select id="filterStatus" class="form-select">
                        <option value="">All Status</option>
                        <option value="pending">Pending</option>
                        <option value="accepted">Accepted</option>
                        <option value="converted">Converted</option>
                        <option value="rejected">Rejected</option>
                    </select>
                </div>
                <div class="col-md-3 mb-2">
                    <input type="date" id="filterDate" class="form-control">
                </div>
                <div class="col-md-2 mb-2">
                    <button class="btn btn-secondary w-100" onclick="resetFilters()">
                        <i class="fas fa-redo"></i> Reset
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quotations Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Quotation Details</th>
                            <th>Date</th>
                            <th>Valid Until</th>
                            <th>Total Amount</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="quotationsTable">
                        {quotations_table if quotations_table else '<tr><td colspan="6" class="text-center py-4">No quotations found. <a href="/quotations/new">Create your first quotation</a></td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <script>
        function convertToInvoice(quotationId) {{
            if (confirm('Convert this quotation to an invoice? This will create a new invoice with the same items.')) {{
                window.location.href = '/quotations/convert/' + quotationId;
            }}
        }}
        
        function filterQuotations() {{
            var search = $('#searchQuotation').val().toLowerCase();
            var status = $('#filterStatus').val();
            var date = $('#filterDate').val();
            
            $('#quotationsTable tr').each(function() {{
                var row = $(this);
                var quotationText = row.find('td:eq(0)').text().toLowerCase();
                var quotationStatus = row.find('.badge').text().toLowerCase();
                var quotationDate = row.find('td:eq(1)').text();
                
                var show = true;
                
                if (search && quotationText.indexOf(search) === -1) show = false;
                if (status && quotationStatus !== status.toLowerCase()) show = false;
                if (date && quotationDate !== date) show = false;
                
                if (show) row.show(); else row.hide();
            }});
        }}
        
        function resetFilters() {{
            $('#searchQuotation').val('');
            $('#filterStatus').val('');
            $('#filterDate').val('');
            filterQuotations();
        }}
        
        $(document).ready(function() {{
            $('#searchQuotation, #filterStatus, #filterDate').on('keyup change', filterQuotations);
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Quotations', 'quotations', content))

@app.route('/quotations/new', methods=['GET', 'POST'])
@login_required
def new_quotation():
    if request.method == 'POST':
        try:
            quotations = read_json(DATABASES['quotations'])
            products = read_json(DATABASES['products'])
            settings = read_json(DATABASES['settings'])[0]
            
            # Generate quotation number
            quote_no = f"{settings.get('quotation_prefix', 'QTN')}-{datetime.now().strftime('%Y%m%d')}-{len(quotations) + 1:04d}"
            
            # Get form data
            items = []
            item_data = request.form.getlist('item[]')
            quantity_data = request.form.getlist('quantity[]')
            price_data = request.form.getlist('price[]')
            
            for i in range(len(item_data)):
                if item_data[i] and quantity_data[i] and price_data[i]:
                    product = next((p for p in products if p['id'] == item_data[i]), None)
                    if product:
                        items.append({
                            'product_id': product['id'],
                            'product_code': product.get('code', ''),
                            'product_name': product.get('name', ''),
                            'quantity': float(quantity_data[i]),
                            'unit': product.get('unit', 'pcs'),
                            'price': float(price_data[i]),
                            'total': float(quantity_data[i]) * float(price_data[i])
                        })
            
            subtotal = sum(item['total'] for item in items)
            discount = float(request.form.get('discount', 0))
            tax_rate = float(request.form.get('tax_rate', settings.get('tax_rate', 5)))
            tax = (subtotal - discount) * (tax_rate / 100)
            total = subtotal - discount + tax
            
            quotation_data = {
                'id': str(uuid.uuid4()),
                'quotation_no': quote_no,
                'customer_id': request.form.get('customer_id'),
                'customer_name': request.form.get('customer_name'),
                'customer_phone': request.form.get('customer_phone'),
                'customer_address': request.form.get('customer_address'),
                'date': request.form.get('date', datetime.now().isoformat()),
                'valid_until': request.form.get('valid_until'),
                'items': items,
                'subtotal': subtotal,
                'discount': discount,
                'tax_rate': tax_rate,
                'tax': tax,
                'total': total,
                'status': 'pending',
                'terms': request.form.get('terms', ''),
                'notes': request.form.get('notes', ''),
                'created_by': current_user.id,
                'created_at': datetime.now().isoformat()
            }
            
            quotations.append(quotation_data)
            write_json(DATABASES['quotations'], quotations)
            
            flash(f'Quotation {quote_no} created successfully!', 'success')
            return redirect(url_for('view_quotation', quotation_id=quotation_data['id']))
            
        except Exception as e:
            flash(f'Error creating quotation: {str(e)}', 'danger')
    
    customers = read_json(DATABASES['customers'])
    products = read_json(DATABASES['products'])
    settings = read_json(DATABASES['settings'])[0]
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-quote-left me-2"></i>Create New Quotation</h2>
        <a href="/quotations" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Quotations
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="quotationForm">
                <!-- Customer Information -->
                <div class="row mb-4">
                    <div class="col-md-6">
                        <h5><i class="fas fa-user me-2"></i>Customer Information</h5>
                    </div>
                    <div class="col-md-6 text-end">
                        <div class="row g-2">
                            <div class="col-md-6">
                                <div class="input-group">
                                    <span class="input-group-text">Date</span>
                                    <input type="date" class="form-control" name="date" 
                                           value="{datetime.now().strftime('%Y-%m-%d')}" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="input-group">
                                    <span class="input-group-text">Valid Until</span>
                                    <input type="date" class="form-control" name="valid_until" 
                                           value="{(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}" required>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mb-4">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Select Customer *</label>
                        <select class="form-select" id="customerSelect" name="customer_id" required 
                                onchange="loadCustomerDetails(this.value)">
                            <option value="">Select a customer...</option>
                            {"".join([f'<option value="{cust["id"]}">{cust["name"]} - {cust.get("phone", "")}</option>' for cust in customers])}
                        </select>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Customer Name</label>
                        <input type="text" class="form-control" id="customerName" 
                               name="customer_name" readonly>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Phone</label>
                        <input type="text" class="form-control" id="customerPhone" 
                               name="customer_phone" readonly>
                    </div>
                    
                    <div class="col-md-8 mb-3">
                        <label class="form-label">Address</label>
                        <input type="text" class="form-control" id="customerAddress" 
                               name="customer_address" readonly>
                    </div>
                </div>
                
                <!-- Quotation Items -->
                <div class="row mb-4">
                    <div class="col-12">
                        <h5><i class="fas fa-shopping-cart me-2"></i>Quotation Items</h5>
                    </div>
                </div>
                
                <div class="table-responsive mb-3">
                    <table class="table table-bordered" id="itemsTable">
                        <thead class="table-dark">
                            <tr>
                                <th width="40%">Product</th>
                                <th width="15%">Quantity</th>
                                <th width="15%">Unit Price (৳)</th>
                                <th width="15%">Total (৳)</th>
                                <th width="15%">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="itemsBody">
                            <!-- Rows will be added dynamically -->
                        </tbody>
                        <tfoot>
                            <tr>
                                <td colspan="5">
                                    <button type="button" class="btn btn-sm btn-success" onclick="addItemRow()">
                                        <i class="fas fa-plus me-1"></i>Add Item
                                    </button>
                                </td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
                
                <!-- Totals -->
                <div class="row justify-content-end">
                    <div class="col-md-6">
                        <table class="table table-bordered">
                            <tr>
                                <td><strong>Subtotal</strong></td>
                                <td class="text-end">৳<span id="subtotal">0.00</span></td>
                            </tr>
                            <tr>
                                <td>
                                    <strong>Discount</strong>
                                    <input type="number" class="form-control form-control-sm d-inline-block w-50 ms-2" 
                                           id="discount" name="discount" value="0" step="0.01" min="0" onchange="calculateTotal()">
                                    ৳
                                </td>
                                <td class="text-end">-৳<span id="discountAmount">0.00</span></td>
                            </tr>
                            <tr>
                                <td>
                                    <strong>Tax Rate</strong>
                                    <input type="number" class="form-control form-control-sm d-inline-block w-50 ms-2" 
                                           id="taxRate" name="tax_rate" value="{settings.get('tax_rate', 5)}" step="0.1" min="0" max="100" onchange="calculateTotal()">
                                    %
                                </td>
                                <td class="text-end">৳<span id="taxAmount">0.00</span></td>
                            </tr>
                            <tr class="table-primary">
                                <td><strong>Total Amount</strong></td>
                                <td class="text-end">৳<span id="totalAmount">0.00</span></td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <!-- Terms & Notes -->
                <div class="row mb-4">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Terms & Conditions</label>
                        <textarea class="form-control" name="terms" rows="3" 
                                  placeholder="Enter terms and conditions...">1. This quotation is valid for 30 days.
2. Prices are subject to change without notice.
3. Delivery charges may apply.
4. Payment terms: 50% advance, 50% on delivery.</textarea>
                    </div>
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Notes</label>
                        <textarea class="form-control" name="notes" rows="3" 
                                  placeholder="Any additional notes for this quotation..."></textarea>
                    </div>
                </div>
                
                <!-- Hidden Fields -->
                <input type="hidden" id="subtotalInput" name="subtotal" value="0">
                <input type="hidden" id="taxInput" name="tax" value="0">
                <input type="hidden" id="totalInput" name="total" value="0">
                
                <!-- Submit Buttons -->
                <div class="row">
                    <div class="col-12">
                        <button type="submit" class="btn btn-primary px-5">
                            <i class="fas fa-save me-1"></i>Save Quotation
                        </button>
                        <button type="button" class="btn btn-secondary" onclick="resetForm()">
                            <i class="fas fa-redo me-1"></i>Reset
                        </button>
                        <button type="button" class="btn btn-success" onclick="saveAndPrint()">
                            <i class="fas fa-print me-1"></i>Save & Print
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Product Modal for Selection -->
    <div class="modal fade" id="productModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Select Product</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Code</th>
                                    <th>Name</th>
                                    <th>Stock</th>
                                    <th>Price</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join([f'''
                                <tr>
                                    <td>{p.get('code', '')}</td>
                                    <td>{p.get('name', '')}</td>
                                    <td>{p.get('stock', 0)} {p.get('unit', 'pcs')}</td>
                                    <td>৳{p.get('selling_price', 0):.2f}</td>
                                    <td>
                                        <button type="button" class="btn btn-sm btn-primary" onclick="selectProduct('{p['id']}', '{p.get('name', '')}', {p.get('selling_price', 0)})">
                                            Select
                                        </button>
                                    </td>
                                </tr>
                                ''' for p in products])}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentRow = null;
        let productOptions = {json.dumps([{'id': p['id'], 'name': p.get('name', ''), 'price': p.get('selling_price', 0), 'stock': p.get('stock', 0), 'unit': p.get('unit', 'pcs')} for p in products])};
        
        // Initialize with one empty row
        $(document).ready(function() {{
            addItemRow();
        }});
        
        function loadCustomerDetails(customerId) {{
            if (!customerId) return;
            
            $.getJSON('/api/customer/' + customerId, function(data) {{
                if (data) {{
                    $('#customerName').val(data.name);
                    $('#customerPhone').val(data.phone);
                    $('#customerAddress').val(data.address);
                }}
            }});
        }}
        
        function addItemRow() {{
            const rowId = 'row_' + Date.now();
            const row = `
                <tr id="${{rowId}}">
                    <td>
                        <button type="button" class="btn btn-sm btn-outline-primary mb-1" onclick="showProductModal('${{rowId}}')">
                            <i class="fas fa-search"></i> Select Product
                        </button>
                        <input type="hidden" name="item[]" id="item_${{rowId}}">
                        <div>
                            <strong id="productName_${{rowId}}">Select a product...</strong><br>
                            <small class="text-muted" id="productStock_${{rowId}}"></small>
                        </div>
                    </td>
                    <td>
                        <input type="number" class="form-control" name="quantity[]" 
                               id="quantity_${{rowId}}" step="0.01" min="0.01" 
                               onchange="calculateRowTotal('${{rowId}}')" required>
                    </td>
                    <td>
                        <input type="number" class="form-control" name="price[]" 
                               id="price_${{rowId}}" step="0.01" min="0" 
                               onchange="calculateRowTotal('${{rowId}}')" required>
                    </td>
                    <td>
                        <div class="input-group">
                            <span class="input-group-text">৳</span>
                            <input type="number" class="form-control" id="total_${{rowId}}" 
                                   readonly step="0.01">
                        </div>
                    </td>
                    <td>
                        <button type="button" class="btn btn-sm btn-danger" onclick="removeItemRow('${{rowId}}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
            $('#itemsBody').append(row);
        }}
        
        function showProductModal(rowId) {{
            currentRow = rowId;
            new bootstrap.Modal(document.getElementById('productModal')).show();
        }}
        
        function selectProduct(productId, productName, price) {{
            if (!currentRow) return;
            
            const product = productOptions.find(p => p.id === productId);
            if (product) {{
                $('#item_' + currentRow).val(productId);
                $('#productName_' + currentRow).text(productName);
                $('#productStock_' + currentRow).text('Stock: ' + product.stock + ' ' + product.unit);
                $('#price_' + currentRow).val(price);
                $('#quantity_' + currentRow).focus();
                
                bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
                calculateRowTotal(currentRow);
            }}
        }}
        
        function calculateRowTotal(rowId) {{
            const quantity = parseFloat($('#quantity_' + rowId).val()) || 0;
            const price = parseFloat($('#price_' + rowId).val()) || 0;
            const total = quantity * price;
            
            $('#total_' + rowId).val(total.toFixed(2));
            calculateTotal();
        }}
        
        function calculateTotal() {{
            let subtotal = 0;
            
            $('input[id^="total_"]').each(function() {{
                subtotal += parseFloat($(this).val()) || 0;
            }});
            
            const discount = parseFloat($('#discount').val()) || 0;
            const taxRate = parseFloat($('#taxRate').val()) || 0;
            const taxable = subtotal - discount;
            const tax = taxable * (taxRate / 100);
            const total = taxable + tax;
            
            $('#subtotal').text(subtotal.toFixed(2));
            $('#discountAmount').text(discount.toFixed(2));
            $('#taxAmount').text(tax.toFixed(2));
            $('#totalAmount').text(total.toFixed(2));
            
            $('#subtotalInput').val(subtotal);
            $('#taxInput').val(tax);
            $('#totalInput').val(total);
        }}
        
        function removeItemRow(rowId) {{
            $('#' + rowId).remove();
            calculateTotal();
        }}
        
        function resetForm() {{
            if (confirm('Are you sure you want to reset the form? All entered data will be lost.')) {{
                $('#itemsBody').empty();
                addItemRow();
                $('#customerSelect').val('');
                $('#customerName, #customerPhone, #customerAddress').val('');
                $('#discount').val(0);
                $('textarea[name="notes"]').val('');
                calculateTotal();
            }}
        }}
        
        function saveAndPrint() {{
            // First save the form, then redirect to print
            $('#quotationForm').submit();
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Create Quotation', 'quotations', content))

@app.route('/quotations/view/<quotation_id>')
@login_required
def view_quotation(quotation_id):
    quotations = read_json(DATABASES['quotations'])
    quotation = next((q for q in quotations if q['id'] == quotation_id), None)
    
    if not quotation:
        flash('Quotation not found!', 'danger')
        return redirect(url_for('quotations'))
    
    # Build items table
    items_table = ""
    for item in quotation.get('items', []):
        items_table += f"""
        <tr>
            <td>{item.get('product_code', 'N/A')}</td>
            <td>{item.get('product_name', 'N/A')}</td>
            <td class="text-end">{item.get('quantity', 0)} {item.get('unit', 'pcs')}</td>
            <td class="text-end">৳{item.get('price', 0):,.2f}</td>
            <td class="text-end">৳{item.get('total', 0):,.2f}</td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-quote-right me-2"></i>Quotation Details</h2>
        <div>
            <a href="/quotations/print/{quotation_id}" target="_blank" class="btn btn-secondary">
                <i class="fas fa-print me-1"></i>Print
            </a>
            <a href="/quotations" class="btn btn-primary">
                <i class="fas fa-arrow-left me-1"></i>Back to Quotations
            </a>
        </div>
    </div>
    
    <!-- Quotation Header -->
    <div class="card mb-4">
        <div class="invoice-header">
            <div class="row">
                <div class="col-md-6">
                    <h3 class="mb-1">{quotation.get('quotation_no', 'N/A')}</h3>
                    <p class="mb-0">Quotation Date: {quotation.get('date', 'N/A')[:10]}</p>
                    <p class="mb-0">Valid Until: {quotation.get('valid_until', 'N/A')[:10]}</p>
                </div>
                <div class="col-md-6 text-end">
                    <h1 class="mb-1">৳{quotation.get('total', 0):,.2f}</h1>
                    <span class="badge bg-{'success' if quotation.get('status') == 'accepted' else 'warning' if quotation.get('status') == 'pending' else 'info'} fs-6">
                        {quotation.get('status', 'pending').upper()}
                    </span>
                </div>
            </div>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-6">
                    <h5>Bill To:</h5>
                    <address>
                        <strong>{quotation.get('customer_name', 'N/A')}</strong><br>
                        {quotation.get('customer_phone', 'N/A')}<br>
                        {quotation.get('customer_address', 'N/A')}
                    </address>
                </div>
                <div class="col-md-6 text-end">
                    <h5>From:</h5>
                    <address>
                        <strong>MEHEDI THAI ALUMINIUM & GLASS</strong><br>
                        123 Business Street, City, Country<br>
                        Phone: +880 1234 567890<br>
                        Email: info@aluminiumglass.com
                    </address>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quotation Items -->
    <div class="card mb-4">
        <div class="card-header">
            <h5 class="mb-0">Quotation Items</h5>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-bordered">
                    <thead class="table-dark">
                        <tr>
                            <th>Code</th>
                            <th>Description</th>
                            <th class="text-end">Quantity</th>
                            <th class="text-end">Unit Price</th>
                            <th class="text-end">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_table}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Subtotal:</strong></td>
                            <td class="text-end"><strong>৳{quotation.get('subtotal', 0):,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Discount:</strong></td>
                            <td class="text-end"><strong>-৳{quotation.get('discount', 0):,.2f}</strong></td>
                        </tr>
                        <tr>
                            <td colspan="4" class="text-end"><strong>Tax ({quotation.get('tax_rate', 0)}%):</strong></td>
                            <td class="text-end"><strong>৳{quotation.get('tax', 0):,.2f}</strong></td>
                        </tr>
                        <tr class="table-primary">
                            <td colspan="4" class="text-end"><strong>Total Amount:</strong></td>
                            <td class="text-end"><strong>৳{quotation.get('total', 0):,.2f}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Terms & Notes -->
    <div class="row mb-4">
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header">
                    <h5 class="mb-0">Terms & Conditions</h5>
                </div>
                <div class="card-body">
                    <div style="white-space: pre-line;">{quotation.get('terms', '')}</div>
                </div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card h-100">
                <div class="card-header">
                    <h5 class="mb-0">Notes</h5>
                </div>
                <div class="card-body">
                    <div style="white-space: pre-line;">{quotation.get('notes', '')}</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Actions -->
    <div class="card">
        <div class="card-body text-center">
            <a href="/quotations/print/{quotation_id}" target="_blank" class="btn btn-primary me-2">
                <i class="fas fa-print me-1"></i>Print Quotation
            </a>
            <button onclick="updateStatus('{quotation_id}', 'accepted')" class="btn btn-success me-2">
                <i class="fas fa-check-circle me-1"></i>Mark as Accepted
            </button>
            <button onclick="convertToInvoice('{quotation_id}')" class="btn btn-warning me-2">
                <i class="fas fa-file-invoice me-1"></i>Convert to Invoice
            </button>
            <button onclick="updateStatus('{quotation_id}', 'rejected')" class="btn btn-danger">
                <i class="fas fa-times-circle me-1"></i>Mark as Rejected
            </button>
        </div>
    </div>
    
    <script>
        function updateStatus(quotationId, status) {{
            const action = status === 'accepted' ? 'accept' : 'reject';
            if (confirm('Are you sure you want to ' + action + ' this quotation?')) {{
                window.location.href = '/quotations/status/' + quotationId + '?status=' + status;
            }}
        }}
        
        function convertToInvoice(quotationId) {{
            if (confirm('Convert this quotation to an invoice? This will create a new invoice with the same items.')) {{
                window.location.href = '/quotations/convert/' + quotationId;
            }}
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Quotation Details', 'quotations', content))

@app.route('/quotations/print/<quotation_id>')
@login_required
def print_quotation(quotation_id):
    quotations = read_json(DATABASES['quotations'])
    quotation = next((q for q in quotations if q['id'] == quotation_id), None)
    
    if not quotation:
        flash('Quotation not found!', 'danger')
        return redirect(url_for('quotations'))
    
    settings = read_json(DATABASES['settings'])[0]
    
    # Build items table for print
    items_rows = ""
    for idx, item in enumerate(quotation.get('items', []), 1):
        items_rows += f"""
        <tr>
            <td class="text-center">{idx}</td>
            <td>{item.get('product_name', '')}</td>
            <td class="text-center">{item.get('unit', 'pcs')}</td>
            <td class="text-center">{item.get('quantity', 0)}</td>
            <td class="text-end">৳{item.get('price', 0):,.2f}</td>
            <td class="text-end">৳{item.get('total', 0):,.2f}</td>
        </tr>
        """
    
    content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Quotation {quotation.get('quotation_no', '')}</title>
        <style>
            @media print {{
                @page {{
                    margin: 0.5in;
                    size: A4 portrait;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    font-size: 12px;
                    color: #000;
                }}
                .no-print {{ display: none !important; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                color: #000;
                margin: 0;
                padding: 20px;
            }}
            .quotation-header {{
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .quotation-footer {{
                border-top: 2px dashed #ddd;
                margin-top: 50px;
                padding-top: 20px;
            }}
            .table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            .table th, .table td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            .table th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            .text-end {{ text-align: right !important; }}
            .text-center {{ text-align: center !important; }}
            .total-table {{ width: 300px; float: right; }}
            .clearfix {{ clear: both; }}
        </style>
    </head>
    <body>
        <div class="no-print" style="margin-bottom: 20px; text-align: center;">
            <button onclick="window.print()" class="btn btn-primary">Print Quotation</button>
            <button onclick="window.close()" class="btn btn-secondary">Close</button>
        </div>
        
        <!-- Quotation Header -->
        <div class="quotation-header">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 50%;">
                        <h1 style="color: #2c3e50; margin: 0;">{settings.get('shop_name', 'MEHEDI THAI ALUMINIUM & GLASS')}</h1>
                        <p style="margin: 5px 0;">{settings.get('shop_address', '123 Business Street, City, Country')}</p>
                        <p style="margin: 5px 0;">Phone: {settings.get('shop_phone', '+880 1234 567890')}</p>
                        <p style="margin: 5px 0;">Email: {settings.get('shop_email', 'info@aluminiumglass.com')}</p>
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <h2 style="color: #3498db; margin: 0;">QUOTATION</h2>
                        <p style="margin: 5px 0;"><strong>Quotation No:</strong> {quotation.get('quotation_no', 'N/A')}</p>
                        <p style="margin: 5px 0;"><strong>Date:</strong> {quotation.get('date', 'N/A')[:10]}</p>
                        <p style="margin: 5px 0;"><strong>Valid Until:</strong> {quotation.get('valid_until', 'N/A')[:10]}</p>
                        <p style="margin: 5px 0;">
                            <strong>Status:</strong> 
                            <span style="color: {'#27ae60' if quotation.get('status') == 'accepted' else '#e74c3c' if quotation.get('status') == 'rejected' else '#f39c12'}">
                                {quotation.get('status', 'pending').upper()}
                            </span>
                        </p>
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Bill To -->
        <div style="margin-bottom: 30px;">
            <h3 style="margin: 0 0 10px 0;">To:</h3>
            <p style="margin: 5px 0;"><strong>{quotation.get('customer_name', 'N/A')}</strong></p>
            <p style="margin: 5px 0;">{quotation.get('customer_phone', 'N/A')}</p>
            <p style="margin: 5px 0; white-space: pre-line;">{quotation.get('customer_address', 'N/A')}</p>
        </div>
        
        <!-- Quotation Items -->
        <table class="table">
            <thead>
                <tr>
                    <th style="width: 5%;">#</th>
                    <th style="width: 45%;">Description</th>
                    <th style="width: 10%;">Unit</th>
                    <th style="width: 10%;">Qty</th>
                    <th style="width: 15%;">Unit Price</th>
                    <th style="width: 15%;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_rows}
            </tbody>
        </table>
        
        <div class="clearfix"></div>
        
        <!-- Totals -->
        <table class="total-table">
            <tr>
                <td style="text-align: right;"><strong>Subtotal:</strong></td>
                <td style="text-align: right;">৳{quotation.get('subtotal', 0):,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: right;"><strong>Discount:</strong></td>
                <td style="text-align: right;">-৳{quotation.get('discount', 0):,.2f}</td>
            </tr>
            <tr>
                <td style="text-align: right;"><strong>Tax ({quotation.get('tax_rate', 0)}%):</strong></td>
                <td style="text-align: right;">৳{quotation.get('tax', 0):,.2f}</td>
            </tr>
            <tr style="background-color: #f8f9fa;">
                <td style="text-align: right;"><strong>Total:</strong></td>
                <td style="text-align: right;"><strong>৳{quotation.get('total', 0):,.2f}</strong></td>
            </tr>
        </table>
        
        <div class="clearfix"></div>
        
        <!-- Terms & Conditions -->
        <div style="margin-top: 50px;">
            <h4>Terms & Conditions:</h4>
            <div style="white-space: pre-line;">{quotation.get('terms', '')}</div>
        </div>
        
        <!-- Notes -->
        {f'''<div style="margin-top: 30px;">
            <h4>Notes:</h4>
            <div style="white-space: pre-line;">{quotation.get('notes', '')}</div>
        </div>''' if quotation.get('notes') else ''}
        
        <!-- Footer -->
        <div class="quotation-footer">
            <div style="margin-top: 50px; text-align: center;">
                <table style="width: 100%;">
                    <tr>
                        <td style="width: 50%; text-align: center;">
                            <p>_________________________</p>
                            <p><strong>Customer Signature</strong></p>
                        </td>
                        <td style="width: 50%; text-align: center;">
                            <p>_________________________</p>
                            <p><strong>Authorized Signature</strong></p>
                        </td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px; font-size: 10px; color: #666;">
                <p>Thank you for considering our quotation!</p>
                <p>{settings.get('shop_name', 'MEHEDI THAI ALUMINIUM & GLASS')} | {settings.get('shop_phone', '+880 1234 567890')} | {settings.get('shop_email', 'info@aluminiumglass.com')}</p>
            </div>
        </div>
        
        <script>
            window.onload = function() {{
                window.print();
            }};
        </script>
    </body>
    </html>
    """
    
    return render_template_string(content)

@app.route('/quotations/status/<quotation_id>')
@login_required
def update_quotation_status(quotation_id):
    status = request.args.get('status', 'pending')
    
    if status not in ['pending', 'accepted', 'rejected', 'converted']:
        flash('Invalid status!', 'danger')
        return redirect(url_for('view_quotation', quotation_id=quotation_id))
    
    try:
        quotations = read_json(DATABASES['quotations'])
        quotation = next((q for q in quotations if q['id'] == quotation_id), None)
        
        if not quotation:
            flash('Quotation not found!', 'danger')
            return redirect(url_for('quotations'))
        
        quotation_index = next(i for i, q in enumerate(quotations) if q['id'] == quotation_id)
        quotations[quotation_index]['status'] = status
        
        write_json(DATABASES['quotations'], quotations)
        
        flash(f'Quotation status updated to {status}!', 'success')
    except Exception as e:
        flash(f'Error updating quotation status: {str(e)}', 'danger')
    
    return redirect(url_for('view_quotation', quotation_id=quotation_id))

@app.route('/quotations/convert/<quotation_id>')
@login_required
def convert_quotation_to_invoice(quotation_id):
    try:
        quotations = read_json(DATABASES['quotations'])
        quotation = next((q for q in quotations if q['id'] == quotation_id), None)
        
        if not quotation:
            flash('Quotation not found!', 'danger')
            return redirect(url_for('quotations'))
        
        # Update quotation status
        quotation_index = next(i for i, q in enumerate(quotations) if q['id'] == quotation_id)
        quotations[quotation_index]['status'] = 'converted'
        write_json(DATABASES['quotations'], quotations)
        
        # Create invoice from quotation
        invoices = read_json(DATABASES['invoices'])
        settings = read_json(DATABASES['settings'])[0]
        
        # Generate invoice number
        invoice_no = f"{settings.get('invoice_prefix', 'INV')}-{datetime.now().strftime('%Y%m%d')}-{len(invoices) + 1:04d}"
        
        invoice_data = {
            'id': str(uuid.uuid4()),
            'invoice_no': invoice_no,
            'customer_id': quotation.get('customer_id'),
            'customer_name': quotation.get('customer_name'),
            'customer_phone': quotation.get('customer_phone'),
            'customer_address': quotation.get('customer_address'),
            'date': datetime.now().isoformat(),
            'due_date': (datetime.now() + timedelta(days=30)).isoformat(),
            'items': quotation.get('items', []),
            'subtotal': quotation.get('subtotal', 0),
            'discount': quotation.get('discount', 0),
            'tax_rate': quotation.get('tax_rate', 0),
            'tax': quotation.get('tax', 0),
            'total': quotation.get('total', 0),
            'paid': 0,
            'balance': quotation.get('total', 0),
            'status': 'pending',
            'notes': f'Converted from quotation {quotation.get("quotation_no", "")}',
            'created_by': current_user.id,
            'created_at': datetime.now().isoformat()
        }
        
        invoices.append(invoice_data)
        write_json(DATABASES['invoices'], invoices)
        
        flash(f'Quotation converted to invoice {invoice_no} successfully!', 'success')
        return redirect(url_for('view_invoice', invoice_id=invoice_data['id']))
        
    except Exception as e:
        flash(f'Error converting quotation: {str(e)}', 'danger')
        return redirect(url_for('view_quotation', quotation_id=quotation_id))

@app.route('/accounts')
@login_required
def accounts():
    # Get transactions
    transactions = read_json(DATABASES['transactions'])
    invoices = read_json(DATABASES['invoices'])
    
    # Calculate summary
    total_income = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'payment')
    total_expense = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
    net_balance = total_income - total_expense
    
    # Recent transactions
    recent_transactions = sorted(transactions, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
    
    # Build transactions table
    transactions_table = ""
    for trans in recent_transactions:
        trans_type = trans.get('type', 'payment')
        if trans_type == 'payment':
            badge = 'success'
            icon = 'money-bill-wave'
            amount_class = 'text-success'
        elif trans_type == 'expense':
            badge = 'danger'
            icon = 'file-invoice-dollar'
            amount_class = 'text-danger'
        else:
            badge = 'info'
            icon = 'exchange-alt'
            amount_class = 'text-info'
        
        # Get invoice details
        invoice_info = ""
        if trans.get('invoice_id'):
            invoice = next((inv for inv in invoices if inv['id'] == trans.get('invoice_id')), {})
            invoice_info = f'<br><small class="text-muted">Invoice: {invoice.get("invoice_no", "N/A")}</small>'
        
        transactions_table += f"""
        <tr>
            <td>{trans.get('created_at', 'N/A')[:16]}</td>
            <td>
                <span class="badge bg-{badge}">
                    <i class="fas fa-{icon} me-1"></i>{trans_type.title()}
                </span>
                {invoice_info}
            </td>
            <td>{trans.get('payment_method', 'N/A')}</td>
            <td class="{amount_class}">৳{trans.get('amount', 0):,.2f}</td>
            <td>{trans.get('notes', '')}</td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-wallet me-2"></i>Accounts</h2>
        <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addTransactionModal">
            <i class="fas fa-plus-circle me-1"></i>Add Transaction
        </button>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-4 mb-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Income</h6>
                    <h2 class="mb-0">৳{total_income:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card bg-danger text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Expenses</h6>
                    <h2 class="mb-0">৳{total_expense:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-4 mb-3">
            <div class="card bg-{'success' if net_balance >= 0 else 'warning'} text-white">
                <div class="card-body">
                    <h6 class="card-title">Net Balance</h6>
                    <h2 class="mb-0">৳{net_balance:,.2f}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Recent Transactions -->
    <div class="card">
        <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">Recent Transactions</h5>
            <div>
                <button class="btn btn-sm btn-outline-primary" onclick="filterTransactions('all')">All</button>
                <button class="btn btn-sm btn-outline-success" onclick="filterTransactions('payment')">Income</button>
                <button class="btn btn-sm btn-outline-danger" onclick="filterTransactions('expense')">Expenses</button>
            </div>
        </div>
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Method</th>
                            <th>Amount</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody id="transactionsTable">
                        {transactions_table if transactions_table else '<tr><td colspan="5" class="text-center py-4">No transactions found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Add Transaction Modal -->
    <div class="modal fade" id="addTransactionModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Add Transaction</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form method="POST" action="/api/transaction/add">
                        <div class="mb-3">
                            <label class="form-label">Transaction Type</label>
                            <select class="form-select" name="type" required>
                                <option value="payment">Income (Payment Received)</option>
                                <option value="expense">Expense</option>
                                <option value="refund">Refund</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Amount (৳) *</label>
                            <input type="number" class="form-control" name="amount" step="0.01" min="0.01" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Payment Method</label>
                            <select class="form-select" name="payment_method">
                                <option value="cash">Cash</option>
                                <option value="bank">Bank Transfer</option>
                                <option value="card">Credit/Debit Card</option>
                                <option value="check">Check</option>
                                <option value="mobile">Mobile Banking</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Description *</label>
                            <textarea class="form-control" name="notes" rows="3" required placeholder="Enter transaction description..."></textarea>
                        </div>
                        <div class="text-end">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="submit" class="btn btn-primary">Add Transaction</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function filterTransactions(type) {{
            $('#transactionsTable tr').each(function() {{
                var row = $(this);
                var rowType = row.find('.badge').text().toLowerCase();
                
                if (type === 'all' || rowType.includes(type)) {{
                    row.show();
                }} else {{
                    row.hide();
                }}
            }});
        }}
        
        // Handle form submission
        $('form[action="/api/transaction/add"]').submit(function(e) {{
            e.preventDefault();
            
            $.ajax({{
                url: $(this).attr('action'),
                method: 'POST',
                data: $(this).serialize(),
                success: function(response) {{
                    if (response.success) {{
                        location.reload();
                    }} else {{
                        alert(response.message || 'Error adding transaction');
                    }}
                }},
                error: function() {{
                    alert('Error adding transaction');
                }}
            }});
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Accounts', 'accounts', content))

@app.route('/api/transaction/add', methods=['POST'])
@login_required
def add_transaction():
    try:
        transactions = read_json(DATABASES['transactions'])
        
        transaction_data = {
            'id': str(uuid.uuid4()),
            'type': request.form.get('type', 'payment'),
            'amount': float(request.form.get('amount', 0)),
            'payment_method': request.form.get('payment_method', 'cash'),
            'notes': request.form.get('notes', ''),
            'created_at': datetime.now().isoformat(),
            'created_by': current_user.id
        }
        
        transactions.append(transaction_data)
        write_json(DATABASES['transactions'], transactions)
        
        return jsonify({'success': True, 'message': 'Transaction added successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/reports')
@login_required
def reports():
    # Get data for reports
    invoices = read_json(DATABASES['invoices'])
    customers = read_json(DATABASES['customers'])
    products = read_json(DATABASES['products'])
    transactions = read_json(DATABASES['transactions'])
    
    # Calculate statistics
    total_customers = len(customers)
    total_products = len(products)
    total_invoices = len(invoices)
    
    # Total sales
    total_sales = sum(invoice.get('total', 0) for invoice in invoices)
    total_paid = sum(invoice.get('paid', 0) for invoice in invoices)
    total_balance = total_sales - total_paid
    
    # Monthly sales
    monthly_sales = {}
    for invoice in invoices:
        month = invoice.get('date', '')[:7]  # YYYY-MM
        if month:
            monthly_sales[month] = monthly_sales.get(month, 0) + invoice.get('total', 0)
    
    # Top customers
    customer_sales = {}
    for invoice in invoices:
        customer_id = invoice.get('customer_id')
        if customer_id:
            customer_sales[customer_id] = customer_sales.get(customer_id, 0) + invoice.get('total', 0)
    
    top_customers = sorted(customer_sales.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Build monthly sales chart data
    monthly_labels = []
    monthly_data = []
    for month in sorted(monthly_sales.keys())[-6:]:  # Last 6 months
        monthly_labels.append(month)
        monthly_data.append(monthly_sales[month])
    
    # Build top customers list
    top_customers_html = ""
    for customer_id, amount in top_customers:
        customer = next((c for c in customers if c['id'] == customer_id), {})
        customer_name = customer.get('name', 'Unknown Customer')
        top_customers_html += f"""
        <div class="d-flex justify-content-between align-items-center mb-2">
            <span>{customer_name}</span>
            <span class="text-primary">৳{amount:,.2f}</span>
        </div>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-chart-bar me-2"></i>Reports & Analytics</h2>
        <div>
            <button class="btn btn-primary" onclick="printReport()">
                <i class="fas fa-print me-1"></i>Print Report
            </button>
        </div>
    </div>
    
    <!-- Summary Cards -->
    <div class="row mb-4">
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-primary text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Customers</h6>
                    <h2 class="mb-0">{total_customers}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-success text-white">
                <div class="card-body">
                    <h6 class="card-title">Total Sales</h6>
                    <h2 class="mb-0">৳{total_sales:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-info text-white">
                <div class="card-body">
                    <h6 class="card-title">Amount Collected</h6>
                    <h2 class="mb-0">৳{total_paid:,.2f}</h2>
                </div>
            </div>
        </div>
        <div class="col-md-3 col-6 mb-3">
            <div class="card bg-{'danger' if total_balance > 0 else 'secondary'} text-white">
                <div class="card-body">
                    <h6 class="card-title">Pending Amount</h6>
                    <h2 class="mb-0">৳{total_balance:,.2f}</h2>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Charts -->
    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Sales Trend (Last 6 Months)</h5>
                </div>
                <div class="card-body">
                    <canvas id="salesChart" height="200"></canvas>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Top 5 Customers</h5>
                </div>
                <div class="card-body">
                    {top_customers_html if top_customers_html else '<p class="text-center text-muted">No customer data available</p>'}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Report Filters -->
    <div class="card mb-4">
        <div class="card-header">
            <h5 class="mb-0">Generate Custom Report</h5>
        </div>
        <div class="card-body">
            <form id="reportForm">
                <div class="row">
                    <div class="col-md-3 mb-3">
                        <label class="form-label">Report Type</label>
                        <select class="form-select" name="report_type">
                            <option value="sales">Sales Report</option>
                            <option value="customer">Customer Report</option>
                            <option value="product">Product Report</option>
                            <option value="payment">Payment Report</option>
                        </select>
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">From Date</label>
                        <input type="date" class="form-control" name="from_date">
                    </div>
                    <div class="col-md-3 mb-3">
                        <label class="form-label">To Date</label>
                        <input type="date" class="form-control" name="to_date">
                    </div>
                    <div class="col-md-3 mb-3 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary w-100">
                            <i class="fas fa-chart-line me-1"></i>Generate
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Quick Stats -->
    <div class="row">
        <div class="col-md-4 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Invoice Status</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Paid Invoices</span>
                        <span class="text-success">{len([inv for inv in invoices if inv.get('status') == 'paid'])}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Pending Invoices</span>
                        <span class="text-warning">{len([inv for inv in invoices if inv.get('status') == 'pending'])}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Partial Payments</span>
                        <span class="text-info">{len([inv for inv in invoices if inv.get('status') == 'partial'])}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-4 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Product Stock</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>In Stock</span>
                        <span class="text-success">{len([p for p in products if p.get('stock', 0) > 0])}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Out of Stock</span>
                        <span class="text-danger">{len([p for p in products if p.get('stock', 0) <= 0])}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Low Stock (< 10)</span>
                        <span class="text-warning">{len([p for p in products if 0 < p.get('stock', 0) < 10])}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-4 mb-4">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Transaction Summary</h5>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span>Total Transactions</span>
                        <span>{len(transactions)}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Income (Payments)</span>
                        <span class="text-success">৳{sum(t.get('amount', 0) for t in transactions if t.get('type') == 'payment'):,.2f}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span>Expenses</span>
                        <span class="text-danger">৳{sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense'):,.2f}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    
    <script>
        function printReport() {{
            window.print();
        }}
        
        // Initialize chart
        $(document).ready(function() {{
            const ctx = document.getElementById('salesChart').getContext('2d');
            const salesChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {json.dumps(monthly_labels)},
                    datasets: [{{
                        label: 'Monthly Sales',
                        data: {json.dumps(monthly_data)},
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        fill: true
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: true,
                            position: 'top'
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                callback: function(value) {{
                                    return '৳' + value.toLocaleString();
                                }}
                            }}
                        }}
                    }}
                }}
            }});
            
            // Handle report form submission
            $('#reportForm').submit(function(e) {{
                e.preventDefault();
                const formData = $(this).serialize();
                
                // Here you would typically make an AJAX call to generate the report
                alert('Report generation feature would be implemented here with the parameters: ' + formData);
            }});
        }});
    </script>
    """
    
    return render_template_string(get_base_template('Reports', 'reports', content))

@app.route('/users')
@login_required
@permission_required('manage_users')
def user_management():
    users = read_json(DATABASES['users'])
    
    # Build users table (excluding password)
    users_table = ""
    for user in users:
        status_badge = f'<span class="badge bg-success">Active</span>' if user.get('is_active', True) else f'<span class="badge bg-danger">Inactive</span>'
        role_badge = f'<span class="badge bg-primary">{user.get("role", "user").title()}</span>'
        
        users_table += f"""
        <tr>
            <td>
                <strong>{user.get('full_name', 'N/A')}</strong><br>
                <small class="text-muted">{user.get('username', 'N/A')}</small>
            </td>
            <td>{user.get('email', 'N/A')}</td>
            <td>{role_badge}</td>
            <td>{status_badge}</td>
            <td>{user.get('created_at', 'N/A')[:10]}</td>
            <td>
                <a href="/users/edit/{user['id']}" class="btn btn-sm btn-warning">
                    <i class="fas fa-edit"></i>
                </a>
                <button onclick="deleteUser('{user['id']}', '{user.get('full_name', '')}')" class="btn btn-sm btn-danger">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
        """
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-users-cog me-2"></i>User Management</h2>
        <a href="/users/new" class="btn btn-primary">
            <i class="fas fa-user-plus me-1"></i>Add New User
        </a>
    </div>
    
    <!-- Users Table -->
    <div class="card">
        <div class="card-body">
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>User Details</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users_table if users_table else '<tr><td colspan="6" class="text-center py-4">No users found</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Delete</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to delete user <strong id="userName"></strong>?</p>
                    <p class="text-danger"><i class="fas fa-exclamation-triangle"></i> This action cannot be undone!</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <a href="#" id="confirmDelete" class="btn btn-danger">Delete User</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function deleteUser(id, name) {{
            document.getElementById('userName').textContent = name;
            document.getElementById('confirmDelete').href = '/users/delete/' + id;
            new bootstrap.Modal(document.getElementById('deleteModal')).show();
        }}
    </script>
    """
    
    return render_template_string(get_base_template('User Management', 'users', content))

@app.route('/users/new', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def new_user():
    if request.method == 'POST':
        try:
            users = read_json(DATABASES['users'])
            
            # Check if username already exists
            username = request.form.get('username')
            if any(u['username'] == username for u in users):
                flash('Username already exists!', 'danger')
                return redirect(url_for('new_user'))
            
            user_data = {
                'id': str(uuid.uuid4()),
                'username': username,
                'email': request.form.get('email'),
                'password': generate_password_hash(request.form.get('password')),
                'full_name': request.form.get('full_name'),
                'role': request.form.get('role', 'user'),
                'permissions': request.form.getlist('permissions'),
                'is_active': request.form.get('is_active') == 'on',
                'created_at': datetime.now().isoformat(),
                'created_by': current_user.id
            }
            
            users.append(user_data)
            write_json(DATABASES['users'], users)
            
            flash('User created successfully!', 'success')
            return redirect(url_for('user_management'))
            
        except Exception as e:
            flash(f'Error creating user: {str(e)}', 'danger')
    
    # Define available permissions
    permissions_list = [
        ('manage_products', 'Manage Products'),
        ('manage_customers', 'Manage Customers'),
        ('manage_invoices', 'Manage Invoices'),
        ('manage_quotations', 'Manage Quotations'),
        ('manage_users', 'Manage Users'),
        ('manage_settings', 'Manage Settings'),
        ('view_reports', 'View Reports'),
        ('all', 'All Permissions (Admin)')
    ]
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-user-plus me-2"></i>Add New User</h2>
        <a href="/users" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Users
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="userForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Full Name *</label>
                        <input type="text" class="form-control" name="full_name" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Username *</label>
                        <input type="text" class="form-control" name="username" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Email Address *</label>
                        <input type="email" class="form-control" name="email" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Password *</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Role *</label>
                        <select class="form-select" name="role" required>
                            <option value="admin">Administrator</option>
                            <option value="manager">Manager</option>
                            <option value="sales">Sales Person</option>
                            <option value="user" selected>Regular User</option>
                        </select>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Status</label>
                        <div class="form-check form-switch mt-2">
                            <input class="form-check-input" type="checkbox" name="is_active" checked>
                            <label class="form-check-label">Active User</label>
                        </div>
                    </div>
                    
                    <div class="col-12 mb-3">
                        <label class="form-label">Permissions</label>
                        <div class="row">
                            {"".join([f'''
                            <div class="col-md-4 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="permissions" value="{perm[0]}" id="perm_{perm[0]}">
                                    <label class="form-check-label" for="perm_{perm[0]}">
                                        {perm[1]}
                                    </label>
                                </div>
                            </div>
                            ''' for perm in permissions_list])}
                        </div>
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Save User
                        </button>
                        <button type="reset" class="btn btn-secondary">
                            <i class="fas fa-redo me-1"></i>Reset
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Add User', 'users', content))

@app.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required
@permission_required('manage_users')
def edit_user(user_id):
    users = read_json(DATABASES['users'])
    user = next((u for u in users if u['id'] == user_id), None)
    
    if not user:
        flash('User not found!', 'danger')
        return redirect(url_for('user_management'))
    
    # Prevent editing own user (except for admin)
    if user_id == current_user.id and current_user.role != 'admin':
        flash('You cannot edit your own account through this interface.', 'danger')
        return redirect(url_for('user_management'))
    
    if request.method == 'POST':
        try:
            user_index = next(i for i, u in enumerate(users) if u['id'] == user_id)
            
            # Prepare updated user data
            updated_user = {
                **user,
                'username': request.form.get('username'),
                'email': request.form.get('email'),
                'full_name': request.form.get('full_name'),
                'role': request.form.get('role'),
                'permissions': request.form.getlist('permissions'),
                'is_active': request.form.get('is_active') == 'on',
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user.id
            }
            
            # Update password only if provided
            password = request.form.get('password')
            if password:
                updated_user['password'] = generate_password_hash(password)
            
            users[user_index] = updated_user
            write_json(DATABASES['users'], users)
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('user_management'))
            
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'danger')
    
    # Define available permissions
    permissions_list = [
        ('manage_products', 'Manage Products'),
        ('manage_customers', 'Manage Customers'),
        ('manage_invoices', 'Manage Invoices'),
        ('manage_quotations', 'Manage Quotations'),
        ('manage_users', 'Manage Users'),
        ('manage_settings', 'Manage Settings'),
        ('view_reports', 'View Reports'),
        ('all', 'All Permissions (Admin)')
    ]
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-edit me-2"></i>Edit User</h2>
        <a href="/users" class="btn btn-secondary">
            <i class="fas fa-arrow-left me-1"></i>Back to Users
        </a>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="userForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Full Name *</label>
                        <input type="text" class="form-control" name="full_name" value="{user.get('full_name', '')}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Username *</label>
                        <input type="text" class="form-control" name="username" value="{user.get('username', '')}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Email Address *</label>
                        <input type="email" class="form-control" name="email" value="{user.get('email', '')}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" class="form-control" name="password" placeholder="Leave blank to keep current password">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Role *</label>
                        <select class="form-select" name="role" required>
                            <option value="admin" {"selected" if user.get('role') == 'admin' else ""}>Administrator</option>
                            <option value="manager" {"selected" if user.get('role') == 'manager' else ""}>Manager</option>
                            <option value="sales" {"selected" if user.get('role') == 'sales' else ""}>Sales Person</option>
                            <option value="user" {"selected" if user.get('role') == 'user' else ""}>Regular User</option>
                        </select>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Status</label>
                        <div class="form-check form-switch mt-2">
                            <input class="form-check-input" type="checkbox" name="is_active" {"checked" if user.get('is_active', True) else ""}>
                            <label class="form-check-label">Active User</label>
                        </div>
                    </div>
                    
                    <div class="col-12 mb-3">
                        <label class="form-label">Permissions</label>
                        <div class="row">
                            {"".join([f'''
                            <div class="col-md-4 mb-2">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" name="permissions" value="{perm[0]}" id="perm_{perm[0]}" {"checked" if perm[0] in user.get('permissions', []) else ""}>
                                    <label class="form-check-label" for="perm_{perm[0]}">
                                        {perm[1]}
                                    </label>
                                </div>
                            </div>
                            ''' for perm in permissions_list])}
                        </div>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Created At</label>
                        <input type="text" class="form-control" readonly value="{user.get('created_at', 'N/A')[:16]}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Created By</label>
                        <input type="text" class="form-control" readonly value="{user.get('created_by', 'System')}">
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Update User
                        </button>
                        <a href="/users" class="btn btn-secondary">
                            <i class="fas fa-times me-1"></i>Cancel
                        </a>
                    </div>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_template_string(get_base_template('Edit User', 'users', content))

@app.route('/users/delete/<user_id>')
@login_required
@permission_required('manage_users')
def delete_user(user_id):
    try:
        # Prevent deleting own account
        if user_id == current_user.id:
            flash('You cannot delete your own account!', 'danger')
            return redirect(url_for('user_management'))
        
        users = read_json(DATABASES['users'])
        users = [u for u in users if u['id'] != user_id]
        write_json(DATABASES['users'], users)
        
        flash('User deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting user: {str(e)}', 'danger')
    
    return redirect(url_for('user_management'))

@app.route('/settings', methods=['GET', 'POST'])
@login_required
@permission_required('manage_settings')
def settings():
    settings_data = read_json(DATABASES['settings'])
    if not settings_data:
        settings_data = [{}]
    
    current_settings = settings_data[0]
    
    if request.method == 'POST':
        try:
            updated_settings = {
                'shop_name': request.form.get('shop_name'),
                'shop_address': request.form.get('shop_address'),
                'shop_phone': request.form.get('shop_phone'),
                'shop_email': request.form.get('shop_email'),
                'tax_rate': float(request.form.get('tax_rate', 5)),
                'currency': request.form.get('currency'),
                'invoice_prefix': request.form.get('invoice_prefix'),
                'quotation_prefix': request.form.get('quotation_prefix'),
                'logo_url': request.form.get('logo_url'),
                'updated_at': datetime.now().isoformat(),
                'updated_by': current_user.id
            }
            
            # Keep created_at if exists
            if 'created_at' in current_settings:
                updated_settings['created_at'] = current_settings['created_at']
            else:
                updated_settings['created_at'] = datetime.now().isoformat()
            
            write_json(DATABASES['settings'], [updated_settings])
            
            flash('Settings updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        except Exception as e:
            flash(f'Error updating settings: {str(e)}', 'danger')
    
    content = f"""
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2><i class="fas fa-cog me-2"></i>Settings</h2>
    </div>
    
    <div class="card">
        <div class="card-body">
            <form method="POST" id="settingsForm">
                <div class="row">
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Shop Name *</label>
                        <input type="text" class="form-control" name="shop_name" 
                               value="{current_settings.get('shop_name', 'MEHEDI THAI ALUMINIUM & GLASS')}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Shop Phone *</label>
                        <input type="text" class="form-control" name="shop_phone" 
                               value="{current_settings.get('shop_phone', '+880 1234 567890')}" required>
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Shop Address *</label>
                        <textarea class="form-control" name="shop_address" rows="2" required>{current_settings.get('shop_address', '123 Business Street, City, Country')}</textarea>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Shop Email *</label>
                        <input type="email" class="form-control" name="shop_email" 
                               value="{current_settings.get('shop_email', 'info@aluminiumglass.com')}" required>
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Currency</label>
                        <select class="form-select" name="currency">
                            <option value="BDT" {"selected" if current_settings.get('currency', 'BDT') == 'BDT' else ""}>Bangladeshi Taka (৳)</option>
                            <option value="USD" {"selected" if current_settings.get('currency', 'BDT') == 'USD' else ""}>US Dollar ($)</option>
                            <option value="EUR" {"selected" if current_settings.get('currency', 'BDT') == 'EUR' else ""}>Euro (€)</option>
                            <option value="GBP" {"selected" if current_settings.get('currency', 'BDT') == 'GBP' else ""}>British Pound (£)</option>
                            <option value="INR" {"selected" if current_settings.get('currency', 'BDT') == 'INR' else ""}>Indian Rupee (₹)</option>
                        </select>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Tax Rate (%) *</label>
                        <input type="number" class="form-control" name="tax_rate" step="0.1" min="0" max="100" 
                               value="{current_settings.get('tax_rate', 5)}" required>
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Invoice Prefix</label>
                        <input type="text" class="form-control" name="invoice_prefix" 
                               value="{current_settings.get('invoice_prefix', 'INV')}">
                    </div>
                    
                    <div class="col-md-4 mb-3">
                        <label class="form-label">Quotation Prefix</label>
                        <input type="text" class="form-control" name="quotation_prefix" 
                               value="{current_settings.get('quotation_prefix', 'QTN')}">
                    </div>
                    
                    <div class="col-md-12 mb-3">
                        <label class="form-label">Logo URL</label>
                        <input type="text" class="form-control" name="logo_url" 
                               value="{current_settings.get('logo_url', '/static/logo.png')}" 
                               placeholder="URL to your shop logo">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Created At</label>
                        <input type="text" class="form-control" readonly 
                               value="{current_settings.get('created_at', 'N/A')[:16]}">
                    </div>
                    
                    <div class="col-md-6 mb-3">
                        <label class="form-label">Last Updated</label>
                        <input type="text" class="form-control" readonly 
                               value="{current_settings.get('updated_at', 'N/A')[:16] if current_settings.get('updated_at') else 'N/A'}">
                    </div>
                    
                    <div class="col-12 mt-4">
                        <button type="submit" class="btn btn-primary px-4">
                            <i class="fas fa-save me-1"></i>Save Settings
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Database Management -->
    <div class="card mt-4">
        <div class="card-header">
            <h5 class="mb-0">Database Management</h5>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <i class="fas fa-database fa-3x text-primary mb-3"></i>
                            <h5>Backup Database</h5>
                            <p class="text-muted">Create a backup of all data</p>
                            <button class="btn btn-outline-primary" onclick="backupDatabase()">
                                <i class="fas fa-save me-1"></i>Create Backup
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <i class="fas fa-redo fa-3x text-warning mb-3"></i>
                            <h5>Reset Demo Data</h5>
                            <p class="text-muted">Reset to default demo data</p>
                            <button class="btn btn-outline-warning" onclick="resetDemoData()">
                                <i class="fas fa-redo me-1"></i>Reset Data
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <i class="fas fa-trash-alt fa-3x text-danger mb-3"></i>
                            <h5>Clear All Data</h5>
                            <p class="text-muted">Delete all data (irreversible)</p>
                            <button class="btn btn-outline-danger" onclick="clearAllData()">
                                <i class="fas fa-trash me-1"></i>Clear Data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function backupDatabase() {{
            if (confirm('Create a backup of all database files?')) {{
                window.location.href = '/api/database/backup';
            }}
        }}
        
        function resetDemoData() {{
            if (confirm('Reset all data to default demo data? This will delete all current data!')) {{
                window.location.href = '/api/database/reset';
            }}
        }}
        
        function clearAllData() {{
            if (confirm('Are you sure you want to clear ALL data? This action cannot be undone!')) {{
                if (confirm('This will delete ALL invoices, customers, products, etc. Are you absolutely sure?')) {{
                    window.location.href = '/api/database/clear';
                }}
            }}
        }}
    </script>
    """
    
    return render_template_string(get_base_template('Settings', 'settings', content))

# API Routes for database management
@app.route('/api/database/backup')
@login_required
@permission_required('manage_settings')
def backup_database():
    try:
        backup_folder = os.path.join('database', 'backups')
        os.makedirs(backup_folder, exist_ok=True)
        
        backup_file = os.path.join(backup_folder, f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        
        backup_data = {}
        for db_name, db_path in DATABASES.items():
            backup_data[db_name] = read_json(db_path)
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=4)
        
        flash(f'Database backup created: {backup_file}', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/api/database/reset')
@login_required
@permission_required('manage_settings')
def reset_database():
    try:
        # Initialize database with default data
        init_database()
        init_default_data()
        
        flash('Database reset to default demo data successfully!', 'success')
    except Exception as e:
        flash(f'Error resetting database: {str(e)}', 'danger')
    
    return redirect(url_for('settings'))

@app.route('/api/database/clear')
@login_required
@permission_required('manage_settings')
def clear_database():
    try:
        # Clear all data files
        for db_name, db_path in DATABASES.items():
            write_json(db_path, [])
        
        # Re-initialize default data
        init_default_data()
        
        flash('All data cleared successfully! Default data restored.', 'success')
    except Exception as e:
        flash(f'Error clearing database: {str(e)}', 'danger')
    
    return redirect(url_for('settings'))

# API endpoints for data
@app.route('/api/products')
@login_required
def api_products():
    products = read_json(DATABASES['products'])
    return jsonify(products)

@app.route('/api/customers')
@login_required
def api_customers():
    customers = read_json(DATABASES['customers'])
    return jsonify(customers)

@app.route('/api/invoices')
@login_required
def api_invoices():
    invoices = read_json(DATABASES['invoices'])
    return jsonify(invoices)

# Run the application
if __name__ == '__main__':
    init_database()
    init_default_data()
    
    print("=" * 70)
    print("MEHEDI THAI ALUMINIUM & GLASS MANAGEMENT SYSTEM")
    print("=" * 70)
    print("✓ Database initialized")
    print("✓ Default data loaded")
    print("\n🔗 ACCESS THE SYSTEM AT:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")
    print("\n👤 ADMIN LOGIN CREDENTIALS:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n📱 MOBILE READY - Professional Edition")
    print("=" * 70)
    print("\n🚀 Starting server... (Press Ctrl+C to stop)\n")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
    except Exception as e:

        print(f"\nError: {e}")
