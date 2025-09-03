#!/bin/bash

# Run backend tests for MealCrafter

echo "🧪 Running MealCrafter Backend Tests..."
echo "======================================="

# Activate virtual environment
source venv/bin/activate

# Run tests with different options
if [ "$1" == "coverage" ]; then
    echo "Running tests with coverage report..."
    pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
    echo "Coverage report generated in htmlcov/index.html"
elif [ "$1" == "verbose" ]; then
    echo "Running tests in verbose mode..."
    pytest tests/ -v
elif [ "$1" == "fast" ]; then
    echo "Running tests (excluding slow tests)..."
    pytest tests/ -m "not slow"
elif [ "$1" == "unit" ]; then
    echo "Running unit tests only..."
    pytest tests/ -m "unit"
else
    echo "Running all tests..."
    pytest tests/ --tb=short
fi

echo ""
echo "✅ Test run complete!"