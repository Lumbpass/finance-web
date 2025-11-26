# models.py
import os
from pymongo import MongoClient
from bson import ObjectId

# ==============================
#  KẾT NỐI MONGODB
# ==============================
MONGO_URI = os.environ.get("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["expense_tracker"]

transactions_col = db["transactions"]
wallet_col = db["wallet"]


# ==============================
#  HÀM XỬ LÝ VÍ (WALLET)
# ==============================
def get_wallet():
    return wallet_col.find_one()


def update_wallet(name, balance, currency):
    """Cập nhật ví (chỉ giữ 1 ví duy nhất)"""
    wallet_col.delete_many({})  # Xóa ví cũ
    wallet_col.insert_one({
        "name": name,
        "balance": balance,
        "currency": currency
    })


# ==============================
#  HÀM XỬ LÝ GIAO DỊCH (TRANSACTIONS)
# ==============================

def get_all_transactions():
    """Lấy toàn bộ giao dịch"""
    return list(transactions_col.find())


def add_transaction(transaction):
    """Thêm giao dịch mới"""
    transactions_col.insert_one(transaction)
    return transaction


def edit_transaction(tx_id, updated_data):
    """Cập nhật giao dịch"""
    transactions_col.update_one(
        {"_id":  ObjectId(tx_id)}, 
        {"$set": updated_data})


def delete_transaction(tx_id):
    """Xóa giao dịch theo id"""
    transactions_col.delete_one(
        {"_id":  ObjectId(tx_id)})


# ==============================
#  DANH MỤC GIAO DỊCH (CATEGORIES)
# ==============================
def get_categories():
    return [
        {"id": 1, "name": "Other", "transactions": 0, "icon": "👜", "in_wallet": None},
        {"id": 2, "name": "Food & Drink", "transactions": 1, "icon": "🍽️", "in_wallet": 1},
        {"id": 3, "name": "Shopping", "transactions": 0, "icon": "🛍️", "in_wallet": None},
        {"id": 4, "name": "Transport", "transactions": 0, "icon": "🚗", "in_wallet": None},
        {"id": 5, "name": "Home", "transactions": 1, "icon": "🏠", "in_wallet": 1},
        {"id": 6, "name": "Bills & Fees", "transactions": 0, "icon": "💵", "in_wallet": None},
        {"id": 7, "name": "Entertainment", "transactions": 0, "icon": "🎭", "in_wallet": None},
        {"id": 8, "name": "Car", "transactions": 0, "icon": "🚘", "in_wallet": None},
        {"id": 9, "name": "Travel", "transactions": 0, "icon": "✈️", "in_wallet": None},
        {"id": 10, "name": "Family & Personal", "transactions": 0, "icon": "👪", "in_wallet": None},
        {"id": 11, "name": "Healthcare", "transactions": 0, "icon": "💊", "in_wallet": None}
    ]

CATEGORY_MAP = {
    "expense": {
        "Food & Drink": "Ăn uống",
        "Shopping": "Mua sắm",
        "Home": "Nhà cửa",
        "Transport": "Di chuyển",
        "Entertainment": "Giải trí"
    },
    "income": {
        "Salary": "Lương",
        "Bonus": "Thưởng",
        "Gift": "Quà tặng",
        "Investment": "Đầu tư"
    }
}
