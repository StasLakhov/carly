from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

USER_CREDENTIALS = {"admin": "password"}


class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(20), nullable=False)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    auction = db.Column(db.String(50), nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    delivery = db.Column(db.Float, nullable=False)
    american_fee = db.Column(db.Float, nullable=False)
    buy_date = db.Column(db.Date, nullable=False)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sum = db.Column(db.Float, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)


with app.app_context():
    db.create_all()


def calculate_totals(cars, transactions):
    total_buy_price = sum(car.buy_price + car.delivery + car.american_fee for car in cars)
    total_send_sum = sum(transaction.sum for transaction in transactions)
    difference_sum = (total_send_sum - total_buy_price)

    return {
        'Total Buy Price': total_buy_price,
        'Total Send Sum': total_send_sum,
        'Difference Sum': difference_sum
    }


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if USER_CREDENTIALS.get(username) == password:
            return redirect(url_for('dashboard'))
        return "Invalid credentials", 401
    return render_template('login.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    cars = Car.query.all()
    transactions = Transaction.query.all()

    if request.method == 'POST':
        new_car = Car(
            vin=request.form['vin'],
            make=request.form['make'],
            model=request.form['model'],
            year=request.form['year'],
            auction=request.form['auction'],
            buy_price=request.form['buy_price'],
            delivery=request.form['delivery'],
            american_fee=request.form['american_fee'],
            buy_date=datetime.strptime(request.form['buy_date'], '%d-%m-%Y') if request.form['buy_date'] else None,
        )
        db.session.add(new_car)
        db.session.commit()
        return redirect(url_for('dashboard'))

    # Calculate totals
    stats = calculate_totals(cars, transactions)

    return render_template('index.html', cars=cars, stats=stats)


@app.route('/add_car', methods=['POST'])
def add_car():
    data = request.form
    new_car = Car(
        vin=data['vin'],
        make=data['make'],
        model=data['model'],
        year=int(data['year']),
        auction=data['auction'],
        buy_price=float(data['buy_price']),
        delivery=float(data['delivery']),
        american_fee=float(data['american_fee']),
        buy_date=datetime.strptime(data['buy_date'], '%Y-%m-%d') if data['buy_date'] else None
    )
    db.session.add(new_car)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/edit_car/<int:id>', methods=['POST'])
def edit_car(id):
    car = Car.query.get_or_404(id)  # Fetch the car by ID

    # Update fields, converting to appropriate types
    car.vin = request.form.get('vin', car.vin)
    car.make = request.form.get('make', car.make)
    car.model = request.form.get('model', car.model)

    # Convert 'year' to integer, if present
    year = request.form.get('year')
    if year:
        car.year = int(year)

    buy_date_str = request.form.get('buy_date')

    if buy_date_str:
        buy_date_obj = datetime.strptime(buy_date_str, '%Y-%m-%d').date()  # Use '%Y-%m-%d' format
    else:
        buy_date_obj = None  # Handle None case if needed

    car.buy_date = buy_date_obj

    car.auction = request.form.get('auction', car.auction)
    car.buy_price = request.form.get('buy_price', car.buy_price)
    car.delivery = request.form.get('delivery', car.delivery)
    car.american_fee = request.form.get('american_fee', car.american_fee)

    db.session.commit()
    return redirect(url_for('dashboard'))


@app.route('/car/<int:car_id>', methods=['GET'])
def get_car(car_id):
    car = Car.query.get(car_id)
    if car:
        # Ensure that the fields exist in your Car model
        car_details = {
            'vin': car.vin,
            'make': car.make,
            'model': car.model,
            'year': car.year,
            'auction': car.auction,
            'buy_price': car.buy_price,
            'delivery': car.delivery,
            'american_fee': car.american_fee,
            'buy_date': car.buy_date
        }
        return jsonify({'success': True, 'car': car_details})
    return jsonify({'error': 'Car not found'}), 404


@app.route('/delete/<int:car_id>', methods=['DELETE'])
def delete_car(car_id):
    car = Car.query.get(car_id)
    if car:
        db.session.delete(car)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


@app.route('/transactions')
def transactions():
    cars = Car.query.all()
    transactions = Transaction.query.all()
    stats = calculate_totals(cars, transactions)

    print(f"Fetched {len(transactions)} transactions")

    return render_template('transactions.html', stats=stats, transactions=transactions)


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    sum = request.form['sum']
    company = request.form['company']
    date_str = request.form['date']

    date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else None

    new_transaction = Transaction(sum=sum, company=company, date=date)
    db.session.add(new_transaction)
    db.session.commit()

    return redirect(url_for('transactions'))


@app.route('/update_transaction/<int:id>', methods=['POST'])
def update_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    transaction.sum = request.form['sum']
    transaction.company = request.form['company']
    transaction.date = request.form['date']

    date = request.form.get('date')
    if date:
        transaction.date = datetime.strptime(date, '%Y-%m-%d').date()

    db.session.commit()

    return redirect(url_for('transactions'))


@app.route('/transaction/<int:id>', methods=['GET'])
def get_transaction(id):
    transaction = Transaction.query.get_or_404(id)

    if transaction:
        # Format the date to 'DD-MM-YYYY'
        formatted_date = transaction.date.strftime('%d-%m-%Y')

        return jsonify({
            'success': True,
            'data': {
                'id': transaction.id,
                'sum': transaction.sum,
                'company': transaction.company,
                'date': formatted_date  # Return formatted date
            }
        })


@app.route('/delete_transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()

    return '', 204  # No content, successful deletion


if __name__ == '__main__':
    app.run(debug=True)

# 1