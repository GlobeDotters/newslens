# Getting Started with NewsLens

We've set up a Python CLI application called NewsLens that analyzes news coverage across the political spectrum. The application is now ready for testing with mock data.

## Testing the Application

1. Make sure you're in your virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install the package in development mode:
   ```bash
   pip install -e .
   ```

3. Run the headlines command to see top news stories:
   ```bash
   newslens headlines
   ```

4. Try the blindspots command to see stories with imbalanced coverage:
   ```bash
   newslens blindspots
   ```

5. View news sources for different countries:
   ```bash
   newslens sources --country US
   newslens sources --country UK
   ```

6. Configure settings, such as changing the default country:
   ```bash
   newslens configure --country UK
   ```

## Notes

- The application is currently set to use mock data by default to avoid network issues. You can switch to real data with:
  ```bash
  newslens configure --use-real
  ```

- To switch back to mock data:
  ```bash
  newslens configure --use-mock
  ```

## Next Steps

1. Test the application with various commands to ensure everything works as expected
2. Start implementing any features from the NEXT_STEPS.md file
3. Consider writing more tests to improve coverage
4. Update documentation if you make significant changes

Enjoy exploring the possibilities of your new CLI tool!
