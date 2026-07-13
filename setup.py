#!/usr/bin/env python
"""Setup script for package installation"""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='quantitative-hedge-fund',
    version='0.1.0',
    author='Kishore Umaprasad',
    author_email='ukishore33@github.com',
    description='End-to-end quantitative trading system for hedge funds',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ukishore33/end-to-end-quantitative-project-thats-been-done-in-advanced-hedge-funds-industry',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
    python_requires='>=3.10',
    install_requires=[
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'scikit-learn>=1.3.0',
        'yfinance>=0.2.0',
        'plotly>=5.0.0',
        'streamlit>=1.25.0',
        'pytest>=7.4.0',
        'black>=23.0.0',
    ],
    extras_require={
        'dev': [
            'pytest-cov>=4.1.0',
            'mypy>=1.4.0',
            'flake8>=6.0.0',
            'sphinx>=7.0.0',
        ],
        'ml': [
            'xgboost>=2.0.0',
            'tensorflow>=2.13.0',
        ],
        'optimization': [
            'cvxpy>=1.3.0',
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
