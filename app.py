from flask import Flask, render_template, request, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import datetime

app = Flask(__name__)

# Firebase 초기화
cred = credentials.Certificate('firebase_config.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# ======================
# 손님용 주문 작성 페이지
# ======================
@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        data = request.form
        table_number = int(data.get('tableNumber'))
        selected_menus = data.getlist('menu')  # ✅ 여러 개 선택된 메뉴 받기
        request_note = data.get('request', '')

        # 하드코딩된 가격표
        menu_prices = {
            "김치찌개": 8000,
            "된장찌개": 7000,
            "제육볶음": 9000
        }

        items = [{"menu": menu, "quantity": 1, "price": menu_prices.get(menu, 0)} for menu in selected_menus]

        order_data = {
            'tableNumber': table_number,
            'items': items,
            'request': request_note,
            'status': '대기 중',
            'timestamp': datetime.datetime.now().isoformat()
        }

        db.collection('orders').document(f'table_{table_number}').set(order_data)
        return redirect(url_for('table_status', table_number=table_number))
    
    return render_template('order.html')


# ======================
# 손님용 주문 현황 페이지
# ======================
@app.route('/table/<int:table_number>')
def table_status(table_number):
    return render_template('table_status.html', table_number=table_number)

# ======================
# 주방/서버용 주문 관리 페이지
# ======================
@app.route('/kitchen')
def kitchen():
    return render_template('kitchen.html')

# ======================
# 관리자용 메뉴 관리 페이지
# ======================
@app.route('/admin')
def admin():
    return render_template('admin.html')

# ======================
# 총무용 매출/정산 페이지
# ======================
@app.route('/accounting')
def accounting():
    return render_template('accounting.html')

# ======================
# 테이블 주문 리셋 → 아카이브로 이동
# ======================
@app.route('/reset-table/<int:table_number>', methods=['POST'])
def reset_table(table_number):
    table_ref = db.collection('orders').document(f'table_{table_number}')
    table_doc = table_ref.get()
    
    if table_doc.exists:
        data = table_doc.to_dict()
        # 주문 상태를 '서빙 완료'로 강제 수정
        archive_data = {
            **data,
            'status': '서빙 완료',
            'finished_at': datetime.datetime.now().isoformat()
        }
        db.collection('order_history').add(archive_data)
        # 원래 주문 삭제
        table_ref.delete()
    
    return redirect(url_for('accounting'))

# ======================
# 서버 실행
# ======================
if __name__ == '__main__':
    app.run(debug=True)
