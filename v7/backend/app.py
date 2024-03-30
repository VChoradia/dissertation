from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Updated in-memory storage to include placeholders for the threshold values
data_storage = {
    "name": "Vivek Choradia",
    "to": "+447387210693",
    "bpm_lower_threshold": 60,  # Example default value
    "bpm_upper_threshold": 100,  # Example default value
    "temp_lower_threshold": 36,  # Example default value
    "temp_upper_threshold": 37,  # Example default value
    "bpm": 0,
    "temp": 0,
}

# Modified HTML form to include slider inputs for the new threshold values
html_form = '''
<!DOCTYPE html>
<html>
<head>
<title>Update Details</title>
<script>
// Function to update the displayed value next to each slider
function updateSliderValue(sliderId, displayId) {
  var slider = document.getElementById(sliderId);
  var display = document.getElementById(displayId);
  display.innerHTML = slider.value;
  
  // Update the form value to be submitted
  slider.oninput = function() {
    display.innerHTML = this.value;
  }
}

// Initialize slider display values on page load
window.onload = function() {
  updateSliderValue('bpm_lower_threshold', 'bpm_lower_display');
  updateSliderValue('bpm_upper_threshold', 'bpm_upper_display');
  updateSliderValue('temp_lower_threshold', 'temp_lower_display');
  updateSliderValue('temp_upper_threshold', 'temp_upper_display');
}
</script>
</head>
<body>
<h2>Update Details</h2>
<form method="POST"  action="/updateDetails">
  Name:<br>
  <input type="text" name="name" value="{{data_storage['name']}}">
  <br>
  Phone Number:<br>
  <input type="text" name="to" value="{{data_storage['to']}}">
  <br>
  BPM Lower Threshold:<br>
  <span>0</span>
  <input type="range" id="bpm_lower_threshold" name="bpm_lower_threshold" min="0" max="300" value="{{data_storage['bpm_lower_threshold']}}">
  <span>300</span>
  <span id="bpm_lower_display">{{data_storage['bpm_lower_threshold']}}</span>
  <br>
  BPM Upper Threshold:<br>
  <span>0</span>
  <input type="range" id="bpm_upper_threshold" name="bpm_upper_threshold" min="0" max="300" value="{{data_storage['bpm_upper_threshold']}}">
  <span>300</span>
  <span id="bpm_upper_display">{{data_storage['bpm_upper_threshold']}}</span>
  <br>
  Temperature Lower Threshold °C:<br>
  <span>20</span>
  <input type="range" id="temp_lower_threshold" name="temp_lower_threshold" min="20" max="40" value="{{data_storage['temp_lower_threshold']}}">
  <span>40</span>
  <span id="temp_lower_display">{{data_storage['temp_lower_threshold']}}</span>
  <br>
  Temperature Upper Threshold °C:<br>
  <span>20</span>
  <input type="range" id="temp_upper_threshold" name="temp_upper_threshold" min="20" max="40" value="{{data_storage['temp_upper_threshold']}}">
  <span>40</span>
  <span id="temp_upper_display">{{data_storage['temp_upper_threshold']}}</span>
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
    data_storage['bpm_lower_threshold'] = int(request.form['bpm_lower_threshold'])
    data_storage['bpm_upper_threshold'] = int(request.form['bpm_upper_threshold'])
    data_storage['temp_lower_threshold'] = int(request.form['temp_lower_threshold'])
    data_storage['temp_upper_threshold'] = int(request.form['temp_upper_threshold'])
    
    return 'Details updated successfully!'

@app.route('/getDetails')
def get_details():
    return jsonify(data_storage)

@app.route('/getStatus', methods=['GET'])
def get_status():
    # Your existing logic for getting status
    return jsonify({
        "bpm": data_storage['bpm'],
        "temp": data_storage['temp']
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
