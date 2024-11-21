#!/bin/bash

echo "Running pre-commit checks..."

echo "Updating pip and tools..."
pip3 install --upgrade isort black pipreqs

echo "Sorting imports with isort..."
isort .

echo "Formatting code with Black..."
black .

echo "Updating requirements.txt with pipreqs..."
pipreqs --force .