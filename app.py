from flask import Flask, render_template, request, jsonify
from main import *
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        if not user_message:
            return jsonify({'error': 'Please refresh the page and try again.'}), 400

        answer, image_paths = bot_response(user_message)
        return jsonify({
            'answer': answer,
            'images': image_paths,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@app.route('/get_items')
def get_items():
    return jsonify({'success': True, 'items': []})

@app.route('/get-products', methods=['GET'])
def get_products():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 9))
    start = (page - 1) * limit
    end = start + limit
    products = foods_dataframe.iloc[start:end].to_dict(orient="records")
    return jsonify({"products": products})

if __name__ == '__main__':
    app.run(debug=True, port=5000)