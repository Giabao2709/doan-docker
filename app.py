from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'it_docker_secret_key'

USERS = {
    'admin': 'admin123',
    'user': 'user123'
}

PRODUCTS = [
    {"id": 1, "name": "Apple MacBook Pro 14\" M2", "price": 47990000, "brand": "Apple", "img": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=400&auto=format&fit=crop"},
    {"id": 2, "name": "Dell XPS 15 9520", "price": 34500000, "brand": "Dell", "img": "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=400&auto=format&fit=crop"},
    {"id": 3, "name": "Lenovo ThinkPad X1 Carbon", "price": 39000000, "brand": "Lenovo", "img": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?q=80&w=400&auto=format&fit=crop"},
    {"id": 4, "name": "Asus ROG Strix G15", "price": 29990000, "brand": "Asus", "img": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?q=80&w=400&auto=format&fit=crop"},
    {"id": 5, "name": "Acer Nitro 5 Gaming", "price": 22500000, "brand": "Acer", "img": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?q=80&w=400&auto=format&fit=crop"},
    {"id": 6, "name": "HP Spectre x360", "price": 41200000, "brand": "HP", "img": "https://images.unsplash.com/photo-1531297172867-4b550dd41334?q=80&w=400&auto=format&fit=crop"}
]

orders = []

# ==========================================
# 2. ĐIỀU HƯỚNG VÀ XỬ LÝ LOGIC (ROUTING)
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form['username']
        password = request.form['password']
        
        if username in USERS and USERS[username] == password:
            if (role == 'admin' and username != 'admin') or (role == 'user' and username != 'user'):
                return render_template('login.html', error="Tài khoản không khớp với vai trò đã chọn!")

            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                session['cart'] = [] 
                return redirect(url_for('user_store'))
        else:
            return render_template('login.html', error="Tài khoản hoặc mật khẩu không chính xác!")
            
    return render_template('login.html')

@app.route('/store')
def user_store():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
        
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    total_price = sum(item['price'] for item in cart_items)
    msg = request.args.get('msg')
    
    return render_template('user.html', products=PRODUCTS, cart=cart_items, total=total_price, msg=msg)

@app.route('/add_cart/<int:product_id>')
def add_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    session.modified = True
    
    product_name = next((p['name'] for p in PRODUCTS if p['id'] == product_id), "Sản phẩm")
    return redirect(url_for('user_store', toast=product_name))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    if not cart_items:
        return redirect(url_for('user_store'))
        
    total_price = sum(item['price'] for item in cart_items)
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    new_order = {
        'customer': request.form['customer_name'],
        'phone': request.form['phone'],
        'items': cart_items,
        'total': total_price,
        'time': current_time
    }
    orders.append(new_order)
    session['cart'] = []
    
    return redirect(url_for('user_store', msg="Đã gửi đơn đặt hàng thành công!"))

@app.route('/admin')
def admin_dashboard():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    
    total_revenue = sum(order['total'] for order in orders)
    total_items_sold = sum(len(order['items']) for order in orders)
    orders_reversed = orders[::-1]
    
    return render_template('admin.html', orders=orders_reversed, total_rev=total_revenue, total_items=total_items_sold)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

import os 

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
