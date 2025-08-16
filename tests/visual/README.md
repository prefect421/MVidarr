# Visual Testing Suite

Comprehensive visual testing infrastructure for MVidarr using Playwright and pytest.

## Overview

The visual testing suite provides:
- **Screenshot Automation**: Automated capture of pages and UI components
- **Visual Regression Testing**: Baseline comparison with diff analysis  
- **Responsive Design Testing**: Multi-viewport validation
- **Cross-Browser Support**: Chromium and Firefox testing capability
- **UI Component Validation**: Comprehensive UI element testing

## Test Structure

```
tests/visual/
├── __init__.py                    # Visual tests package
├── conftest.py                   # Playwright fixtures and configuration
├── test_page_screenshots.py     # Page and component screenshots
├── test_visual_regression.py    # Visual regression testing
├── test_comprehensive_ui.py     # Comprehensive UI testing
├── screenshots/                 # Generated screenshots
├── baselines/                  # Baseline images for regression testing
└── README.md                   # This file
```

## Running Visual Tests

### Basic Usage

```bash
# Run all visual tests
pytest tests/visual/ -v

# Run only screenshot tests
pytest tests/visual/test_page_screenshots.py -v

# Run only regression tests
pytest tests/visual/test_visual_regression.py -v

# Run comprehensive UI tests
pytest tests/visual/test_comprehensive_ui.py -v
```

### Filtering by Markers

```bash
# Run only visual tests
pytest -m visual -v

# Run only regression tests
pytest -m regression -v

# Run slow visual tests
pytest -m "visual and slow" -v

# Skip visual tests
pytest -m "not visual" -v
```

### Browser Selection

```bash
# Run with specific browser
pytest tests/visual/ --browser chromium -v
pytest tests/visual/ --browser firefox -v

# Run headless (default)
pytest tests/visual/ --headed -v  # Run with visible browser
```

## Visual Test Types

### 1. Page Screenshots (`test_page_screenshots.py`)

Captures screenshots of all major pages:
- Homepage, Videos, Artists, Discover, Settings, MvTV pages
- UI components (navigation, header, main content)
- Different themes (light/dark)
- Error states and empty states
- Interactive elements (modals, forms)

### 2. Visual Regression Testing (`test_visual_regression.py`)

Compares current screenshots with baselines:
- Creates baselines on first run
- Compares subsequent runs with baselines
- Generates diff images for failed comparisons
- Supports responsive regression testing
- Component-level regression testing

### 3. Comprehensive UI Testing (`test_comprehensive_ui.py`)

Tests UI functionality and behavior:
- Page accessibility testing
- Interactive element detection
- Form element validation
- Navigation functionality testing
- Responsive behavior validation
- Video player UI testing
- Error state UI testing

## Configuration

### Visual Test Configuration

Configuration is handled in `conftest.py`:

```python
# Application URL
BASE_URL = "http://localhost:5000"

# Comparison thresholds
PIXEL_THRESHOLD = 0.2    # 20% pixel difference
GLOBAL_THRESHOLD = 0.1   # 10% global difference

# Responsive breakpoints
BREAKPOINTS = {
    "mobile": {"width": 375, "height": 667},
    "tablet": {"width": 768, "height": 1024}, 
    "desktop": {"width": 1280, "height": 720},
    "wide": {"width": 1920, "height": 1080}
}
```

### Browser Configuration

```python
# Browser launch args
browser_type_launch_args = {
    "headless": True,
    "slow_mo": 100,  # Slow down for better screenshots
}

# Browser context args
browser_context_args = {
    "viewport": {"width": 1280, "height": 720},
    "ignore_https_errors": True,
}
```

## Screenshots and Artifacts

### Generated Files

- **screenshots/**: Current test screenshots
- **baselines/**: Baseline images for regression testing
- **\*_diff.png**: Diff images showing visual changes
- **\*.json**: Test analysis and metadata files

### Analysis Files

The test suite generates analysis files:
- `accessible_pages.json`: Page accessibility analysis
- `interactive_elements.json`: Interactive element analysis  
- `form_elements.json`: Form element analysis
- `navigation_analysis.json`: Navigation functionality analysis
- `responsive_tests.json`: Responsive design test results
- `video_player_analysis.json`: Video player UI analysis
- `error_states_analysis.json`: Error state analysis

## Dependencies

Visual testing requires additional dependencies:

```bash
# Install visual testing dependencies
pip install -r requirements-dev.txt

# Install Playwright browsers
playwright install chromium firefox
```

Required packages:
- `playwright==1.40.0`
- `pytest-playwright==0.4.3`
- `Pillow==10.3.0`
- `imagehash==4.3.1`

## Best Practices

### Writing Visual Tests

1. **Use descriptive test names**: Include what you're testing
2. **Set test names**: Use `screenshot_helper.set_test_name()`
3. **Handle failures gracefully**: Use `pytest.skip()` for missing pages
4. **Capture multiple states**: Test different UI states and themes
5. **Use appropriate timeouts**: Wait for content to load

### Screenshot Management

1. **Baseline creation**: Run tests once to create baselines
2. **Review changes**: Check diff images when tests fail
3. **Update baselines**: Regenerate when UI changes are intentional
4. **Clean up**: Remove old screenshots and baselines periodically

### Performance Considerations

1. **Use headless mode**: Default headless mode for faster execution
2. **Limit external resources**: Block images/fonts for faster loading
3. **Batch similar tests**: Group related screenshots in single test
4. **Skip missing pages**: Don't fail on expected missing functionality

## Troubleshooting

### Common Issues

1. **"Playwright not installed"**
   ```bash
   playwright install chromium
   ```

2. **"Page not accessible"**
   - Check if application is running on correct port
   - Verify BASE_URL in configuration
   - Check application logs

3. **"Visual regression detected"**
   - Check diff images in screenshots directory
   - Verify if changes are intentional
   - Update baselines if needed

4. **Tests timing out**
   - Increase timeouts in test configuration
   - Check if application is responding slowly
   - Use `pytest -s` for debugging output

### Debugging

```bash
# Run with visible browser for debugging  
pytest tests/visual/ --headed -v -s

# Run single test with full output
pytest tests/visual/test_page_screenshots.py::TestPageScreenshots::test_homepage_screenshot -v -s --headed

# Enable Playwright debugging
DEBUG=pw:api pytest tests/visual/ -v
```

## Integration with CI/CD

Visual tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions integration
- name: Install Playwright
  run: playwright install chromium

- name: Run Visual Tests
  run: pytest tests/visual/ -v --browser chromium

- name: Upload Screenshots  
  uses: actions/upload-artifact@v3
  with:
    name: visual-test-results
    path: tests/visual/screenshots/
```

## Future Enhancements

Planned improvements:
- Cross-browser visual comparison
- Automated baseline updates
- Performance monitoring integration
- Mobile device emulation
- Accessibility testing integration