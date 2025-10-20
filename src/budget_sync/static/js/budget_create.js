// budget_sync/static/js/budget_create.js

// Start the category index at 1 because the first card uses index 0.
let categoryIndex = 1;

document.addEventListener('DOMContentLoaded', function () {
  // Handle adding a new category card.
  const addCategoryButton = document.getElementById('add-category');
  if (addCategoryButton) {
    addCategoryButton.addEventListener('click', function() {
      const categoryHTML = `
        <div class="card p-3 mb-4" data-index="${categoryIndex}" style="background-color: #e0f7fa;">
          <h4 class="mb-3">Category</h4>
          <div class="mb-3">
            <input type="text" class="form-control" name="category_name[]" placeholder="Category Name (e.g., Bills, Food)">
          </div>
          <div class="subcategories">
            <h5 class="mb-3">Subcategories</h5>
            <div class="mb-2">
              <input type="text" class="form-control" name="subcategory_${categoryIndex}[]" placeholder="Subcategory Name (e.g., Water, Groceries)">
            </div>
          </div>
          <button type="button" class="btn btn-sm btn-success add-subcategory">Add Subcategory</button>
        </div>
      `;
      document.getElementById('categories').insertAdjacentHTML('beforeend', categoryHTML);
      categoryIndex++;
    });
  }

  // Delegate event for adding subcategory inputs.
  document.addEventListener('click', function(event) {
    if (event.target.classList.contains('add-subcategory')) {
      const card = event.target.closest('.card');
      const index = card.getAttribute('data-index');
      const subcategoryHTML = `
        <div class="mb-2">
          <input type="text" class="form-control" name="subcategory_${index}[]" placeholder="Subcategory Name (e.g., Internet, Cable)">
        </div>
      `;
      card.querySelector('.subcategories').insertAdjacentHTML('beforeend', subcategoryHTML);
    }
  });
});
