# Project Progress Documentation

This document tracks the ongoing development progress, challenges, and next steps for the project.  
Entries are organized with the **most recent updates at the top**.

---

## Date: 2025-08-20
### Progress
- Core project functionality working end-to-end.
- Implemented interactive dashboard.
- Enforced password requirements.
- Flash messages display as intended.
- User profile must be completed prior to budget creation.
- Support for multiple budgets per user.
- Database integration functional (all data saves correctly).
- Budget summary and spending chart implemented.
- Taxes and deductions are applied as intended.

### Next Steps
- Implement password recovery flow.
- Replace generic tax logic with state-specific JSON data.
- Transition JSON tax logic into a dedicated Tax API.
- Migrate from local DB to AWS RDS.

---

## Date: 2025-04-02
### Progress
- Revised flash messages to be rendered from `base.html`, fixing delayed display issues.

### Needs Improvement
- Budget name not persisting to the database.
- After creating a budget, routing should go to budget categories, then to budget input (with pre-populated categories).  
  Currently, it routes directly to budget input.

---

## Date: 2025-03-18 (Update 2)
### Progress
- Implemented internal **Tax Rate API** with the following endpoints:

1. **Get Federal Tax Brackets**  
    ```http
    GET /api/v1/tax/federal/<year>
    ```
    Returns federal tax brackets and standard deduction for the specified year.

2. **Get State Tax Brackets**  
    ```http
    GET /api/v1/tax/state/<state>/<year>
    ```
    Returns state tax brackets and related information for a specific state and year.

3. **Get FICA Rates**  
    ```http
    GET /api/v1/tax/fica/<year>
    ```
    Returns Social Security and Medicare rates for the specified year.

4. **Calculate Taxes**  
    ```http
    POST /api/v1/tax/calculate
    ```
    Calculates total tax liability based on provided income and details.  
    **Example Request Body:**
    ```json
    {
        "year": 2024,
        "income": 75000,
        "state": "CA",
        "filing_status": "single",
        "pay_frequency": "biweekly",
        "additional_withholding": 100,
        "pretax_deductions": 5000
    }
    ```

5. **Get Available Tax Years**  
    ```http
    GET /api/v1/tax/years
    ```
    Returns a list of years for which tax data is available.

### Needs Improvement
- Implement data modules for federal, state, and FICA tax calculations.
- Add request/response validation models.
- Add comprehensive API tests.
- Write API documentation with example responses.
- Implement caching for API responses.
- Add rate limiting for API endpoints.
- Add authentication for sensitive endpoints.

---

## Date: 2025-03-18
### Progress
- Enhanced Profile model with tax-related fields.
- Added detailed pre-tax benefit tracking (health insurance, HSA, FSA).
- Improved Profile form UI with organized sections and validation.
- Built tax rate API infrastructure (models, cache, configuration).
- Resolved database migration issues with proper default values.
- Added handling for retirement contributions (pre/post-tax).
- Improved form validation and error handling.
- Enhanced UI with Bootstrap cards and proper input formatting.

### Needs Improvement
- Implement live tax rate API integration.
- Connect tax calculation logic to budget processing.
- Add tax bracket visualization in results.
- Implement caching for tax rate data.
- Create tax calculation documentation.
- Add unit tests for tax calculations.
- Validate tax-related fields.
- Add tooltips for tax-related inputs.
- Implement state-specific tax rules.
- Add tax summary to budget preview.
- Add tax withholding calculator.
- Add annual tax projection report.

---

## Date: 2025-03-16
### Progress
- Fixed `routes.py` so profile, dashboard, expenses, and income pages all commit to DB.
- Database correctly references table IDs.
- Resolved CSRF Token errors.
- View and delete buttons from dashboard function correctly.
- Edit button implemented but needs debugging.

### Needs Improvement
- Budget logic improvements.
- Create budget preview HTML page.
- Enable editing budget directly from dashboard.
- Improve navigation between pages.
- Fix inaccuracies in flash message displays.
   
        