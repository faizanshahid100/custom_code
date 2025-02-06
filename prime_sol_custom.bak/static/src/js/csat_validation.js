document.addEventListener('DOMContentLoaded', function() {
    const csatField = document.querySelector('input[name="csat_new"]');
    if (csatField) {
        const form = csatField.closest('form');

        form.addEventListener('submit', function(event) {
            const csatValue = parseFloat(csatField.value);
            if (isNaN(csatValue) || csatValue < 0 || csatValue > 100 || !/^\d+(\.\d{1,2})?$/.test(csatField.value)) {
                event.preventDefault();
                alert('CSAT % must be a positive number between 0 and 100 with up to two decimal places.');
                return false;
            }
        });
    }
});