#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import time

def take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            print('Loading GitHub Pages site...')
            page.goto('https://prefect421.github.io/mvidarr', wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            print('Taking screenshot...')
            page.screenshot(path='/home/mike/mvidarr/github_pages_current.png', full_page=True)
            print('Screenshot saved as github_pages_current.png')
            
            # Check what CSS files are loading
            css_links = page.query_selector_all('link[rel="stylesheet"]')
            print(f'\nFound {len(css_links)} CSS files:')
            for link in css_links:
                href = link.get_attribute('href')
                print(f'  - {href}')
                
            # Check if our custom CSS is in head
            head_content = page.inner_html('head')
            if '--mvidarr-dark' in head_content:
                print('\n✅ Custom MVidarr CSS variables found in head')
            else:
                print('\n❌ Custom MVidarr CSS variables NOT found in head')
                
            # Check page background color
            body_style = page.evaluate('window.getComputedStyle(document.body).backgroundColor')
            html_style = page.evaluate('window.getComputedStyle(document.documentElement).backgroundColor')
            print(f'\nPage colors:')
            print(f'  HTML background: {html_style}')
            print(f'  Body background: {body_style}')
            
            # Check if head-custom.html content is present
            if 'mvidarr-primary' in head_content:
                print('\n✅ head-custom.html content found')
                # Show a snippet
                start = head_content.find('mvidarr-primary')
                snippet = head_content[max(0, start-50):start+100]
                print(f'Snippet: ...{snippet}...')
            else:
                print('\n❌ head-custom.html content NOT found')
                
        except Exception as e:
            print(f'Error: {e}')
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    take_screenshot()