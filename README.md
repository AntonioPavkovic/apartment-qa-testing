# Apartment QA Testing

A comprehensive Python-based QA testing suite for apartment web applications using Playwright automation framework.

## Overview

This project provides automated testing solutions for apartment management web applications, offering both focused admin verification/validation tests and comprehensive full-application testing capabilities.


## Prerequisites

Ensure you have the following installed on your system:

- **Python 3.13+** (tested with Python 3.13.7)
- **pip** (tested with pip 25.2)
- **Virtual Environment** capabilities

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AntonioPavkovic/apartment-qa-testing.git
   cd apartment-qa-testing
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   ```bash
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Install Playwright browsers** (if not already installed)
   ```bash
   playwright install
   ```

## Usage

### Prerequisites for Running Tests

Before executing any tests, ensure you:

1. **Navigate to project directory**
   ```bash
   cd apartment-qa-testing
   ```

2. **Activate virtual environment**
   ```bash
   venv\Scripts\activate
   ```

### Running Tests

#### Admin Verification & Validation Tests

For focused testing of administrative features with verification and validation:

```bash
python test_admin_only.py
```

This test suite covers:
- Admin login functionality
- User management features  
- Administrative dashboard validation
- Permission-based access controls

#### Comprehensive Application Tests

For complete end-to-end testing of the entire apartment application:

```bash
python test_melon_apartment.py
```

This comprehensive suite includes:
- User registration and authentication
- Apartment listing and search functionality
- Booking and reservation processes
- Payment processing workflows
- Admin and user role interactions


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request


## Author

**Antonio Pavkovic**
- GitHub: [@AntonioPavkovic](https://github.com/AntonioPavkovic)

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
