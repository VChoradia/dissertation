from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# In-memory storage for simplicity. For production, consider a database.
data_storage = {
    "name": "Vivek Choradia",
    "to": "+447387210693"
}

# A simple HTML form for input
html_form = '''
<!DOCTYPE html>
<html>
<head>
<title>Update Details</title>
</head>
<body>
<h2>Update Details</h2>
<form method="POST"  action="/updateDetails">
  Name:<br>
  <input type="text" name="name" value="{{data_storage['name']}}">
  <br>
  Phone Number:<br>
  <input type="text" name="to" value="{{data_storage['to']}}">
  <br><br>
  <input type="submit" value="Submit">
</form> 
</body>
</html>
'''

@app.route('/')
def form():
    return render_template_string(html_form, data_storage=data_storage)

@app.route('/updateDetails', methods=['POST'])
def update_details():
    data_storage['name'] = request.form['name']
    data_storage['to'] = request.form['to']
    return 'Details updated successfully!'

@app.route('/getDetails')
def get_details():
    return jsonify(data_storage)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
