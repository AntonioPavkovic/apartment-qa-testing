from playwright.sync_api import sync_playwright

def test_simple_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://mostar.api.demo.ch.melon.market/')
        print(f'Page title: {page.title()}')
        print(f'Current URL: {page.url}')
        page.wait_for_timeout(5000)
        browser.close()
        print('Simple test completed!')

if __name__ == '__main__':
    test_simple_navigation()