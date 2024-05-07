document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.deviceButton').forEach(button => {
        button.addEventListener('click', function() {
            document.getElementById('deviceIp').value = this.getAttribute('data-ip');
        });
    });
});

function submitPatientDetails() {
    const deviceIp = document.getElementById('deviceIp').value;
    const patientName = document.getElementById('patientName').value;
    const phoneNumber = document.getElementById('phoneNumber').value;

    console.log(deviceIp, patientName, phoneNumber);
    
    fetch('/submit-patient-details', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ deviceIp, patientName, phoneNumber }),
    })
    .then(response => response.json())
    .then(data => alert("Details Submitted Successfully"))
    .catch((error) => {
        console.error('Error:', error);
        alert("Failed to Submit Details");
    });
}