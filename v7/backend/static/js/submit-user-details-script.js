document.addEventListener('DOMContentLoaded', () => {
    const sliders = document.querySelectorAll('.slider');
  
    const updateSliderValues = () => {
      sliders.forEach(slider => {
        const valueDisplay = slider.nextElementSibling;
        valueDisplay.textContent = slider.value;
      });
    };
  
    // Update on input and on page load
    sliders.forEach(slider => {
      slider.addEventListener('input', updateSliderValues);
    });
  
    // Initial update
    updateSliderValues();
  });