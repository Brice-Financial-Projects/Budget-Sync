"""run.py"""

import os
import sys

# Add the src directory to Python path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from budget_sync import create_app



# Create the budget_sync instance using the factory function
app = create_app()

if __name__ == '__main__':
    # Run the budget_sync
    app.run(port=5000)
