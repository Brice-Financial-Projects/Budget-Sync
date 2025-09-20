// budget_sync/static/js/income.js

document.addEventListener('DOMContentLoaded', function () {
    const container = document.getElementById('other-income-container');
    const addIncomeButton = document.getElementById('add-income');
    let incomeCount = 0;

    // Add hidden input for income count
    const countInput = document.createElement('input');
    countInput.type = 'hidden';
    countInput.name = 'other_income_count';
    countInput.value = '0';
    container.parentNode.insertBefore(countInput, container);

    addIncomeButton.addEventListener('click', function () {
        // Remove any "no income sources" message if it exists
        const infoMessage = container.querySelector('.alert-info');
        if (infoMessage) {
            infoMessage.remove();
        }
        
        const newEntry = document.createElement('div');
        newEntry.classList.add('income-entry', 'mb-3');
        
        newEntry.innerHTML = `
            <div class="mb-3">
                <label class="form-label">Income Type</label>
                <select class="form-select" name="other_income_sources-${incomeCount}-category">
                    <option value="">Select Income Type</option>
                    <option value="rental">Rental Income</option>
                    <option value="investment">Investment Dividends</option>
                    <option value="business">Business Income</option>
                    <option value="side_job">Secondary Employment</option>
                    <option value="royalties">Royalties</option>
                    <option value="social_security">Social Security</option>
                    <option value="pension">Pension</option>
                    <option value="other">Other</option>
                </select>
            </div>

            <div class="mb-3">
                <label class="form-label">Income Source Name</label>
                <input type="text" class="form-control" name="other_income_sources-${incomeCount}-name">
            </div>

            <div class="mb-3">
                <label class="form-label">Amount</label>
                <input type="number" class="form-control" name="other_income_sources-${incomeCount}-amount" step="0.01" min="0">
            </div>

            <div class="mb-3">
                <label class="form-label">Frequency</label>
                <select class="form-select" name="other_income_sources-${incomeCount}-frequency">
                    <option value="">Select Frequency</option>
                    <option value="weekly">Weekly</option>
                    <option value="biweekly">Biweekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="bimonthly">Bimonthly</option>
                    <option value="annually">Annually</option>
                </select>
            </div>

            <button type="button" class="btn btn-danger remove-income">Remove</button>
        `;
        container.appendChild(newEntry);
        incomeCount++;
        countInput.value = incomeCount;
    });

    // Handle removal of income sources
    container.addEventListener('click', function (event) {
        if (event.target.classList.contains('remove-income')) {
            const entry = event.target.closest('.income-entry');
            if (entry) {
                entry.remove();
                incomeCount--;
                countInput.value = incomeCount;
                
                // Reindex remaining entries
                const entries = container.querySelectorAll('.income-entry');
                entries.forEach((entry, index) => {
                    entry.querySelectorAll('[name^="other_income_sources-"]').forEach(input => {
                        const parts = input.name.split('-');
                        const fieldName = parts[2]; // The field name is the third part after two splits
                        input.name = `other_income_sources-${index}-${fieldName}`;
                    });
                });
            }
        }
    });
});

