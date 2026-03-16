from flask import Flask, request, jsonify, render_template
import token_generator

app = Flask(__name__)

# হোমপেজ রেন্ডার করার রাউট
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Access Token জেনারেট করার এন্ডপয়েন্ট
@app.route('/api/get_access_token', methods=['GET'])
def api_get_access_token():
    uid = request.args.get('uid')
    password = request.args.get('password')
    eat_token = request.args.get('eat_token')

    if uid and password:
        result = token_generator.get_access_token_from_uid_pass(uid, password)
        return jsonify(result)
    elif eat_token:
        result = token_generator.get_access_token_from_eat(eat_token)
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Please provide uid & password OR eat_token"}), 400

# JWT Token জেনারেট করার এন্ডপয়েন্ট
@app.route('/api/get_jwt_token', methods=['GET'])
def api_get_jwt_token():
    uid = request.args.get('uid')
    password = request.args.get('password')
    eat_token = request.args.get('eat_token')
    access_token = request.args.get('access_token')

    if access_token:
        result = token_generator.get_jwt_from_access_token(access_token)
        return jsonify(result)
    elif eat_token:
        result = token_generator.get_jwt_from_eat_token(eat_token)
        return jsonify(result)
    elif uid and password:
        result = token_generator.get_jwt_from_uid_pass(uid, password)
        return jsonify(result)
    else:
        return jsonify({"success": False, "error": "Please provide valid parameters"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
