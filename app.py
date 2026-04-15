from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
import pytz  # Để xử lý múi giờ Việt Nam
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = 'it_docker_secret_key'

# ==========================================
# 1. KẾT NỐI CƠ SỞ DỮ LIỆU MONGODB
# ==========================================
MONGO_URI = "mongodb://admin_bao:bao123456@ac-dcjljad-shard-00-00.kjkg2nt.mongodb.net:27017,ac-dcjljad-shard-00-01.kjkg2nt.mongodb.net:27017,ac-dcjljad-shard-00-02.kjkg2nt.mongodb.net:27017/?ssl=true&replicaSet=atlas-y8vuto-shard-0&authSource=admin&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client['shop_may_tinh']
products_collection = db['products']
orders_collection = db['orders']
users_collection = db['users'] 

# Tự động thêm sản phẩm gốc nếu database trống
if products_collection.count_documents({}) == 0:
    default_products = [
        {"name": "Apple MacBook Pro 14\" M2", "price": 47990000, "brand": "Apple", "img": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=400&auto=format&fit=crop"},
        {"name": "Dell XPS 15 9520", "price": 34500000, "brand": "Dell", "img": "https://images.unsplash.com/photo-1593640408182-31c70c8268f5?q=80&w=400&auto=format&fit=crop"},
        {"name": "Lenovo ThinkPad X1 Carbon", "price": 39000000, "brand": "Lenovo", "img": "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?q=80&w=400&auto=format&fit=crop"},
        {"name": "Asus ROG Strix G15", "price": 29990000, "brand": "Asus", "img": "https://images.unsplash.com/photo-1603302576837-37561b2e2302?q=80&w=400&auto=format&fit=crop"},
        {"name": "Acer Nitro 5 Gaming", "price": 22500000, "brand": "Acer", "img": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?q=80&w=400&auto=format&fit=crop"},
        {"name": "HP Spectre x360", "price": 41200000, "brand": "HP", "img": "https://images.unsplash.com/photo-1531297172867-4b550dd41334?q=80&w=400&auto=format&fit=crop"}
    ]
    products_collection.insert_many(default_products)

def get_all_products():
    products = list(products_collection.find())
    for p in products:
        p['id'] = str(p['_id'])
    return products

# ==========================================
# 2. ĐIỀU HƯỚNG VÀ XỬ LÝ LOGIC (ROUTING)
# ==========================================

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = request.args.get('msg') 
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form['username'].strip()
        password = request.form['password']
        
        if role == 'admin':
            if username == 'admin' and password == 'admin123':
                session['username'] = 'admin'
                return redirect(url_for('admin_dashboard'))
            else:
                return render_template('login.html', error="Tài khoản hoặc mật khẩu Quản trị không chính xác!")
        
        elif role == 'user':
            user_in_db = users_collection.find_one({"username": username, "password": password})
            if user_in_db:
                session['username'] = username
                if 'cart' not in session: 
                    session['cart'] = [] 
                return redirect(url_for('user_store'))
            else:
                return render_template('login.html', error="Tài khoản hoặc mật khẩu không chính xác!")
                
    return render_template('login.html', msg=msg)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        existing_user = users_collection.find_one({"username": username})
        if existing_user or username == 'admin':
            return render_template('register.html', error="Tên đăng nhập này đã có người sử dụng!")

        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": password, 
            "role": "user"
        })
        
        return redirect(url_for('login', msg="Tạo tài khoản thành công! Vui lòng đăng nhập."))
        
    return render_template('register.html')

@app.route('/store')
def user_store():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
        
    all_products = get_all_products()
    cart_items = [p for p in all_products if p['id'] in session.get('cart', [])]
    total_price = sum(item['price'] for item in cart_items)
    msg = request.args.get('msg')
    
    return render_template('user.html', products=all_products, cart=cart_items, total=total_price, msg=msg)

@app.route('/add_cart/<product_id>')
def add_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(product_id)
    session.modified = True
    
    all_products = get_all_products()
    product_name = next((p['name'] for p in all_products if p['id'] == product_id), "Sản phẩm")
    return redirect(url_for('user_store', toast=product_name))

@app.route('/checkout', methods=['POST'])
def checkout():
    all_products = get_all_products()
    cart_items = [p for p in all_products if p['id'] in session.get('cart', [])]
    
    if not cart_items:
        return redirect(url_for('user_store'))
        
    total_price = sum(item['price'] for item in cart_items)
    
    # --- PHẦN SỬA: LẤY GIỜ VIỆT NAM ---
    tz_VN = pytz.timezone('Asia/Ho_Chi_Minh') 
    datetime_VN = datetime.now(tz_VN)
    current_time = datetime_VN.strftime("%d/%m/%Y %H:%M:%S")
    # ---------------------------------
    
    new_order = {
        'account': session['username'], 
        'customer': request.form['customer_name'],
        'phone': request.form['phone'],
        'items': cart_items,
        'total': total_price,
        'time': current_time
    }
    
    orders_collection.insert_one(new_order)
    session['cart'] = []
    
    return redirect(url_for('user_store', msg="Đã gửi đơn đặt hàng thành công!"))

@app.route('/admin')
def admin_dashboard():
    if session.get('username') != 'admin':
        return redirect(url_for('login'))
    
    all_products = get_all_products()
    orders_db = list(orders_collection.find().sort("_id", -1))
    all_users = list(users_collection.find())
    
    total_revenue = sum(order['total'] for order in orders_db)
    total_items_sold = sum(len(order['items']) for order in orders_db)
    
    return render_template('admin.html', products=all_products, orders=orders_db, users=all_users, total_rev=total_revenue, total_items=total_items_sold)

@app.route('/admin/add', methods=['POST'])
def add_product():
    if session.get('username') == 'admin':
        products_collection.insert_one({
            "name": request.form['name'],
            "price": int(request.form['price']),
            "brand": request.form['brand'],
            "img": request.form['img']
        })
    return redirect(url_for('admin_dashboard') + '#laptop')

@app.route('/admin/delete/<product_id>')
def delete_product(product_id):
    if session.get('username') == 'admin':
        products_collection.delete_one({"_id": ObjectId(product_id)})
    return redirect(url_for('admin_dashboard') + '#laptop')

@app.route('/admin/update', methods=['POST'])
def update_product():
    if session.get('username') == 'admin':
        p_id = request.form['id']
        updated_p = {
            "name": request.form['name'],
            "price": int(request.form['price']),
            "brand": request.form['brand'],
            "img": request.form['img']
        }
        products_collection.update_one({"_id": ObjectId(p_id)}, {"$set": updated_p}) 
    return redirect(url_for('admin_dashboard') + '#laptop')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
