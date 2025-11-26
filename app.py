import datetime
import os
import uuid
from models import get_wallet, get_all_transactions
from flask import Flask, render_template, request, redirect, url_for,session
from pymongo import MongoClient
from bson.objectid import ObjectId
from auth import auth, bcrypt
from models import CATEGORY_MAP


app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = "mysecretkey"  # dùng để lưu session
bcrypt.init_app(app)
# --- Kết nối MongoDB ---
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("ERROR: MONGO_URI is missing! Did you set Railway Variables?")
    raise SystemExit()
client = MongoClient(MONGO_URI)
db = client["expense_tracker"]
transactions_col = db ["transactions"]
wallet_col = db ['wallet'] # ✅ đổi sang VNĐ

def get_all_transactions():
    return list(transactions_col.find())

# Đăng ký Blueprint auth
app.register_blueprint(auth, url_prefix="/auth")

@app.route('/')
def index():
    if 'user_id' not in session:     # ← session phải import
        return redirect(url_for('auth.login'))
    
    transactions_data = list(transactions_col.find({"user_id": session["user_id"]}))
    for t in transactions_data:
        t["_id"] = str(t["_id"])


    total_income = sum(t["amount"] for t in transactions_data if t["amount"] > 0)
    total_expenses = sum(t["amount"] for t in transactions_data if t["amount"] < 0)
    wallet_data = get_wallet() or {"balance": 0, "currency": "VNĐ"}
    balance = wallet_data["balance"] + total_income + total_expenses

    return render_template(
        'transactions.html',
        wallet=wallet_data,
        transactions=transactions_data,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        user_name=session.get('user_name')
    )


@app.route('/add', methods=['GET', 'POST'])
def add_transaction_page():
    if request.method == 'POST':
        new_tx = {
            "user_id": session["user_id"],
            "type": request.form["type"],
            "category": request.form["category"],
            "note": request.form["note"],
            "date": request.form["date"],
            "amount": float(request.form["amount"]),
            "currency": "VNĐ"  # ✅ đổi USD → VNĐ
        }

        # Tự động đổi dấu âm nếu là chi tiêu
        if new_tx["type"] == "expense":
            new_tx["amount"] = -abs(new_tx["amount"])
        else:
            new_tx["amount"] = abs(new_tx["amount"])

        inserted = transactions_col.insert_one(new_tx)
        print("Inserted ID:", inserted.inserted_id)
        return redirect(url_for('index'))

    return render_template('add_transaction.html',  CATEGORY_MAP=CATEGORY_MAP)


@app.route('/edit/<tx_id>', methods=['GET', 'POST'])
def edit_transaction(tx_id):
    print("TX_ID:", tx_id)
    try:
        tx = transactions_col.find_one({"_id": ObjectId(tx_id), "user_id": session["user_id"]})
    except:
        return "Invalid transaction ID", 400
    
    if not tx:
        return "Transaction not found", 404

    if request.method == 'POST':
        updated_tx = {
            "type" : request.form["type"],
            "category" : request.form["category"],
            "note" : request.form["note"],
            "date" : request.form["date"],
            "amount" : float(request.form["amount"]),
            "currency" : "VNĐ"  # ✅ đảm bảo sửa xong vẫn lưu VNĐ
        }

        if updated_tx["type"] == "expense":
            updated_tx["amount"] = -abs(updated_tx["amount"])
        else:
            updated_tx["amount"] = abs(updated_tx["amount"])

        transactions_col.update_one({"_id": ObjectId(tx_id)}, {"$set": updated_tx})
        return redirect(url_for('index'))

    return render_template('edit_transaction.html', tx=tx, CATEGORY_MAP=CATEGORY_MAP)


@app.route('/delete/<tx_id>')
def delete_transaction(tx_id):
    print("TX_ID:", tx_id)
    try:
        transactions_col.delete_one({"_id": ObjectId(tx_id), "user_id": session["user_id"]})
    except:
        return "Invalid transaction ID", 400
    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
def wallet_settings():
    wallet_data = wallet_col.find_one({"user_id": session["user_id"]})

    if request.method == 'POST':
        name = request.form["name"]
        balance = float(request.form["balance"])
        currency = "VNĐ"  # ✅ khóa cứng đơn vị VNĐ cho đồng bộ

        wallet_col.delete_many({"user_id": session["user_id"]})
        wallet_col.insert_one({
            "user_id": session["user_id"],
            "name": name, 
            "balance": balance, 
            "currency": currency})
        return redirect(url_for('index'))

    return render_template('wallet_settings.html', wallet=wallet_data)


@app.route("/filter")
def filter_data():
    classification = request.args.get("classification")  # Chi tiêu / Thu nhập
    category = request.args.get("category")
    min_amount = request.args.get("min")
    max_amount = request.args.get("max")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = {}

    # Xác định loại giao dịch
    type_map = {"Chi tiêu": "expense", "Thu nhập": "income"}
    tx_type = type_map.get(classification)
    if tx_type:
        query["type"] = tx_type

    # Dùng CATEGORY_MAP từ models.py để map category tiếng Việt → DB key
    if tx_type and category:
        # đảo ngược map: "Ăn uống" → "Food & Drink"
        inverse_map = {v: k for k, v in CATEGORY_MAP[tx_type].items()}
    if category in inverse_map:
        query["category"] = inverse_map[category]

    if min_amount or max_amount:
        min_a = float(min_amount) if min_amount else 0
        max_a = float(max_amount) if max_amount else 999999999
        query["amount"] = {"$gte": min_a, "$lte": max_a}

    # FIX: So sánh string, không convert sang datetime
    if start_date or end_date:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.min
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else datetime.max
        query["date"] = {"$gte": start, "$lte": end}



    print("QUERY:", query)  # debug

    results = list(transactions_col.find(query))
    for r in results:
        r["_id"] = str(r["_id"])

    return render_template("filter_result.html", results=results)



@app.route("/overview")
def overview():
    transactions = list(transactions_col.find({"user_id": session["user_id"]}))

    total_income = sum(t["amount"] for t in transactions if t["amount"] > 0)
    total_expenses = sum(t["amount"] for t in transactions if t["amount"] < 0)
    
    wallet = get_wallet() or {"balance": 0}
    balance = wallet["balance"] + total_income + total_expenses

    # Tính theo category
    income_summary = {}
    expense_summary = {}

    for t in transactions:
        cat = t["category"]
        amt = t["amount"]

        if amt > 0:
            income_summary[cat] = income_summary.get(cat, 0) + amt
        else:
            expense_summary[cat] = expense_summary.get(cat, 0) + abs(amt)

    return render_template(
        "overview.html",
        balance=balance,
        total_income=total_income,
        total_expenses=total_expenses,
        income_summary=[{"category": k, "total": v} for k, v in income_summary.items()],
        expense_summary=[{"category": k, "total": v} for k, v in expense_summary.items()]
    )


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
