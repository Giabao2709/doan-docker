from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import os 

app = Flask(__name__)

# GHI CHÚ 1: Secret Key dùng để mã hóa Session. 
# Không có cái này, tính năng Đăng ký và Giỏ hàng sẽ bị lỗi trên Cloud.
app.secret_key = 'it_docker_secret_key'

# 1. CƠ SỞ DỮ LIỆU GIẢ LẬP (In-memory storage)
# Chú ý: Dữ liệu này nằm trên RAM. Khi Docker Restart, tài khoản mới đăng ký sẽ mất.
USERS = {
    'admin': 'admin123',
    'user': 'user123'
}

# Lưu trữ thêm Email cho phần Đăng ký
USER_DETAILS = {
    'admin': 'admin@itdocker.com',
    'user': 'user@itdocker.com'
}

PRODUCTS = [
    {"id": 1, "name": "Apple MacBook Pro 14\" M2", "price": 47990000, "brand": "Apple", "img": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=400"},
    {"id": 2, "name": "Dell XPS 15 9520", "price": 34500000, "brand": "Dell", "img": "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=400"},
    {"id": 3, "name": "Lenovo ThinkPad X1 Carbon", "price": 39000000, "brand": "Lenovo", "img": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?q=80&w=400"},
    {"id": 4, "name": "Asus ROG Strix G15", "price": 29990000, "brand": "Asus", "img": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?q=80&w=400"},
    {"id": 5, "name": "Acer Nitro 5 Gaming", "price": 22500000, "brand": "Acer", "img": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?q=80&w=400"},
    {"id": 6, "name": "HP Spectre x360", "price": 41200000, "brand": "HP", "img": "https://images.unsplash.com/photo-1531297172867-4b550dd41334?q=80&w=400"}
]

# Danh sách đơn hàng (Lưu trên RAM - Stateless)
orders = []

# ==========================================
# PHẦN ĐIỀU HƯỚNG (ROUTES)
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def login():
    # Nhận thông báo "Đăng ký thành công" từ trang Register gửi sang
    msg = request.args.get('msg')
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form['username']
        password = request.form['password']
        
        # Xác thực người dùng (Authentication)
        if username in USERS and USERS[username] == password:
            # Phân quyền (Authorization)
            if (role == 'admin' and username != 'admin'):
                return render_template('login.html', error="Bạn không có quyền quản trị!")
            
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                session['cart'] = [] 
                return redirect(url_for('user_store'))
        return render_template('login.html', error="Sai tài khoản hoặc mật khẩu!")
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # GHI CHÚ 2: Kiểm tra trùng lặp tài khoản
        if username in USERS:
            return render_template('register.html', error="Tên đăng nhập đã tồn tại!")
        
        # Lưu tài khoản mới vào RAM
        USERS[username] = password
        USER_DETAILS[username] = email
        
        # Sau khi đăng ký xong, quay về trang login kèm thông báo
        return redirect(url_for('login', msg="Đăng ký thành công! Mời bạn đăng nhập."))
    return render_template('register.html')

@app.route('/store')
def user_store():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    # GHI CHÚ 3: Sử dụng List Comprehension để lọc giỏ hàng nhanh hơn
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    total_price = sum(item['price'] for item in cart_items)
    return render_template('user.html', products=PRODUCTS, cart=cart_items, total=total_price)

@app.route('/add_cart/<int:product_id>')
def add_cart(product_id):
    if 'cart' not in session: session['cart'] = []
    session['cart'].append(product_id)
    session.modified = True # Cập nhật lại session cookie
    return redirect(url_for('user_store', toast="Đã thêm vào giỏ!"))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    if cart_items:
        new_order = {
            'customer': request.form['customer_name'],
            'phone': request.form['phone'],
            'items': cart_items,
            'total': sum(item['price'] for item in cart_items),
            'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        orders.append(new_order) # Ghi đơn hàng vào RAM
        session['cart'] = [] 
    return redirect(url_for('user_store', msg="Đặt hàng thành công!"))

@app.route('/admin')
def admin_dashboard():
    if session.get('username') != 'admin': return redirect(url_for('login'))
    total_rev = sum(order['total'] for order in orders)
    # GHI CHÚ 4: Đảo ngược danh sách để đơn hàng mới nhất hiện lên đầu
    return render_template('admin.html', orders=orders[::-1], total_rev=total_rev)

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('login'))

# ==========================================
# CẤU HÌNH DOCKER & CLOUD
# ==========================================

if __name__ == '__main__':
    # GHI CHÚ 5: Dynamic Port Binding - Tự động nhận diện cổng của Render
    port = int(os.environ.get('PORT', 5000))
    # Host 0.0.0.0 để Docker Container có thể "nói chuyện" với internet
    app.run(host='0.0.0.0', port=port)