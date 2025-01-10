#!/bin/bash

# First, create a valid pyproject.toml with proper project name
echo "Creating Poetry project..."
poetry new my_python_project
cd my_python_project

# Core packages grouped by functionality
packages=(
    # Data Science & Machine Learning
    "numpy==1.24.3"
    "pandas>=2.0.0"
    "scikit-learn>=1.2.2"
    "torch>=2.0.0"
    
    # API Development
    "fastapi>=0.100.0"
    "uvicorn[standard]>=0.22.0"
    "python-multipart>=0.0.6"
    "pydantic>=2.0.0"
    
    # Data Visualization
    "plotly>=5.15.0"
    "streamlit>=1.24.0"
    
    # AI/LLM Tools
    "openai>=0.27.8"
    "langchain>=0.0.27"
    "tiktoken>=0.4.0"
    
    # Utilities
    "python-dotenv>=1.0.0"
    "requests>=2.31.0"
    "PyYAML>=6.0"
    
    # Image Processing
    "pillow>=10.0.0"
    "opencv-python-headless>=4.8.0"
    
    # Geographic Data
    "geopy>=2.3.0"
    "folium>=0.14.0"
    
    # Database
    "SQLAlchemy>=2.0.0"
)

# Install each package
echo "Installing packages..."
for package in "${packages[@]}"; do
    echo "Installing $package..."
    poetry add "$package" || {
        echo "Failed to install $package - retrying with --no-cache..."
        poetry add "$package" --no-cache || echo "Failed to install $package after retry"
    }
done

echo "Installation complete!"