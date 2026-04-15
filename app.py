from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import os # Quan trọng: Dùng để đọc biến môi trường từ Docker/Cloud

app = Flask(__name__)

# GHI CHÚ 1: Secret Key dùng để mã hóa Session (dữ liệu người dùng).

app.secret_key = 'it_docker_secret_key'
# GHI CHÚ 2: Sử dụng List Comprehension để lọc dữ liệu.
# Kỹ thuật này giúp code Python chạy nhanh và tối ưu bộ nhớ bên trong Container.
USERS = {
    'admin': 'admin123',
    'user': 'user123'
}

PRODUCTS = [
    {"id": 1, "name": "Apple MacBook Pro 14\" M2", "price": 47990000, "brand": "Apple", "img": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=400"},
    {"id": 2, "name": "Dell XPS 15 9520", "price": 34500000, "brand": "Dell", "img": "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=400"},
    {"id": 3, "name": "Lenovo ThinkPad X1 Carbon", "price": 39000000, "brand": "Lenovo", "img": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?q=80&w=400"},
    {"id": 4, "name": "Asus ROG Strix G15", "price": 29990000, "brand": "Asus", "img": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?q=80&w=400"},
    {"id": 5, "name": "Acer Nitro 5 Gaming", "price": 22500000, "brand": "Acer", "img": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?q=80&w=400"},
    {"id": 6, "name": "HP Spectre x360", "price": 41200000, "brand": "HP", "img": "https://images.unsplash.com/photo-1531297172867-4b550dd41334?q=80&w=400"}
]

# Danh sách đơn hàng - Sẽ mất sạch nếu Container bị Restart (Tính chất Stateless của Docker)
orders = []

# PHẦN ĐIỀU HƯỚNG (ROUTES)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form['username']
        password = request.form['password']
        
        # Kiểm tra logic đăng nhập và khớp vai trò (Role Validation)
        if username in USERS and USERS[username] == password:
            if (role == 'admin' and username != 'admin') or (role == 'user' and username != 'user'):
                return render_template('login.html', error="Tài khoản không khớp với vai trò!")
            
            # Lưu tên người dùng vào Session (Cookie trình duyệt)
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                session['cart'] = [] # Khởi tạo giỏ hàng trống cho User
                return redirect(url_for('user_store'))
        return render_template('login.html', error="Sai tài khoản hoặc mật khẩu!")
    return render_template('login.html')

@app.route('/store')
def user_store():
    # Bảo mật: Nếu chưa đăng nhập mà đòi vào Store -> Đuổi ra trang Login
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    # Lấy danh sách sản phẩm thực tế từ ID trong giỏ hàng
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    total_price = sum(item['price'] for item in cart_items)
    return render_template('user.html', products=PRODUCTS, cart=cart_items, total=total_price)

@app.route('/add_cart/<int:product_id>')
def add_cart(product_id):
    if 'cart' not in session: session['cart'] = []
    session['cart'].append(product_id)
    
    # GHI CHÚ 3: Thông báo cho Flask biết Session đã thay đổi để cập nhật Cookie
    session.modified = True
    
    product_name = next((p['name'] for p in PRODUCTS if p['id'] == product_id), "Sản phẩm")
    return redirect(url_for('user_store', toast=product_name))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = [p for p in PRODUCTS if p['id'] in session.get('cart', [])]
    if cart_items:
        # Tạo đối tượng đơn hàng mới
        new_order = {
            'customer': request.form['customer_name'],
            'phone': request.form['phone'],
            'items': cart_items,
            'total': sum(item['price'] for item in cart_items),
            'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        orders.append(new_order) # Lưu vào danh sách orders trên RAM
        session['cart'] = [] # Xóa sạch giỏ hàng sau khi đặt thành công
    return redirect(url_for('user_store', msg="Đặt hàng thành công!"))

@app.route('/admin')
def admin_dashboard():
    # Chỉ Admin mới được vào trang quản trị
    if session.get('username') != 'admin': return redirect(url_for('login'))
    
    total_rev = sum(order['total'] for order in orders)
    total_items = sum(len(order['items']) for order in orders)
    
    # Đảo ngược danh sách đơn hàng để đơn mới nhất hiện lên đầu
    return render_template('admin.html', orders=orders[::-1], total_rev=total_rev, total_items=total_items)

@app.route('/logout')
def logout():
    session.clear() # Xóa sạch Session khi đăng xuất
    return redirect(url_for('login'))

# ==========================================
# CẤU HÌNH ĐỂ CHẠY TRÊN DOCKER & CLOUD
# ==========================================
if __name__ == '__main__':
    # GHI CHÚ 4: Lấy cổng PORT từ hệ thống (Render/Azure cấp phát)
    # Nếu chạy máy cá nhân (Local) thì dùng mặc định 5000
    port = int(os.environ.get('PORT', 5000))
    
    # GHI CHÚ 5: Host '0.0.0.0' là BẮT BUỘC để Docker Container có thể 
    # giao tiếp được với mạng bên ngoài máy chủ.
    app.run(host='0.0.0.0', port=port)
