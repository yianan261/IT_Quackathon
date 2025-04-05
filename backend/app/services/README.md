# Service Modules

This directory contains service modules that provide functionality for the application. Each service is responsible for interacting with a specific external system or providing a specific type of functionality.

## Available Services

### Canvas Service

The `canvas_service.py` file contains the `CanvasService` class, which is responsible for interacting with the Canvas LMS API to retrieve course, assignment, and announcement information.

### Stevens Service

The `stevens_service.py` file contains the `StevensService` class, which is responsible for providing information specific to Stevens Institute of Technology.

### Workday Service

The `workday_service.py` file contains the `WorkdayService` class, which provides browser automation capabilities for interacting with Stevens Institute of Technology's Workday system. The service allows for programmatic login, navigation to academic pages, course searching, and extraction of HTML content.

#### Vision-based Validation

The Workday service includes capabilities for capturing screenshots and validating pages using AI vision:

- The `check_if_on_registration_page()` method captures a full-page screenshot that can be analyzed by an AI vision model to determine if the page is a registration page.
- Screenshots are saved in the `browser_dumps/screenshots` directory with timestamped filenames.

#### Course Registration Automation

The service also includes a method for automating course registration:

- The `automate_course_registration(course_code)` method navigates to the registration page and attempts to register for a specific course.
- Screenshots are captured at each step for analysis and validation.

#### Requirements for Workday Service

- Python 3.8+
- Playwright (`pip install playwright`)
- After installing Playwright, install browser binaries: `playwright install chromium`

#### Workday Service Setup

1. Add the Playwright package to your environment:

   ```
   pip install playwright
   playwright install chromium
   ```

2. Set up your credentials:
   ```
   export WORKDAY_USERNAME="your_username"
   export WORKDAY_PASSWORD="your_password"
   ```
   Or provide them directly to the functions when calling them.

#### Workday Service Testing

You can test the Workday service using the `test_workday.py` script:

```bash
# From the backend directory
cd backend

# Test login
python -m app.services.test_workday --username "your_username" --password "your_password" --action login

# Test navigating to academics
python -m app.services.test_workday --action academics

# Test searching for courses in a specific term
python -m app.services.test_workday --action academics --term "Fall 2023" --subject "Computer Science"

# Extract a specific page with a full-page screenshot
python -m app.services.test_workday --action extract --step "registration_page"

# Validate if the current page is a registration page
python -m app.services.test_workday --action validate

# Test course registration automation
python -m app.services.test_workday --action register --course "CS 101"
```

### Browser Utilities

The `browser_utils` directory contains utilities for browser automation, including a wrapper around Playwright that provides methods for common browser operations. These utilities are used by the Workday service but can also be used by other services that require browser automation.

Key features include:

- Full-page screenshot capture
- HTML content extraction
- Element interaction (clicking, filling forms)
- Waiting for page navigation and elements

## Integration with User Functions

The following Workday service functions are registered in `user_functions.py` and can be called by the AI agent:

- `login_to_workday` - Log in to Workday
- `navigate_to_academics` - Navigate to the Academics section
- `search_workday_courses` - Search for courses by term/subject
- `extract_workday_page` - Extract HTML from the current page
- `validate_registration_page` - Take a screenshot and check if the current page is a registration page
- `automate_course_registration` - Automate the course registration process for a specific course

## Using Vision Features with Azure AI

To use the vision features with Azure AI:

1. Call the `validate_registration_page()` function to capture a screenshot
2. The function returns a screenshot path
3. Use the screenshot path to send the image to Azure AI Vision API or GPT-4o-mini with vision capabilities
4. The AI can analyze the screenshot to determine page contents and verify registration page fields

Example usage in your Azure Foundry agent:

```python
# In your agent code when deciding if you can proceed with registration
registration_page_check = validate_registration_page()
if registration_page_check["success"]:
    # Send the screenshot to Azure AI Vision or GPT-4o-mini
    vision_analysis = analyze_image(registration_page_check["screenshot_abs_path"])

    # Based on the vision analysis, decide if it's a registration page
    if "registration form" in vision_analysis or "course selection" in vision_analysis:
        # Proceed with registration
        result = automate_course_registration("CS 101")
    else:
        # Not on the right page
        return "Could not find the registration page. Please navigate to it first."
```
