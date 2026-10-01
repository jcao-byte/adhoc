from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import time
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


start_time_str = "9:00 pm"
is_boan = False

today = datetime.today()
date_str = (today + timedelta(days=2)).strftime("%m/%d/%Y")
refresh_time_str = datetime.strptime(start_time_str, "%I:%M %p").strftime("%H:%M:%S")

def time_to_seconds(time_str):
    """
    '9:00 am' -> 32400
    """
    dt = datetime.strptime(time_str, "%I:%M %p")
    return dt.hour * 3600 + dt.minute * 60

def refresh_at(page, target_time_str, early_second=0):
    """
    target_time_str: '09:00:00'
    """
    print("Starting refresh at")
    while True:
        early_target_time_str = (datetime.strptime(target_time_str, '%H:%M:%S') - timedelta(seconds=early_second)).strftime('%H:%M:%S')
        now = datetime.now().strftime("%H:%M:%S")
        if now >= early_target_time_str:
            page.reload()
            print(f"🔄 Page refreshed at {now}")
            break
        time.sleep(0.1)  # 100ms precision

def try_click_slot_and_add_to_cart(
        page,
        date_str,
        start_time_str,
        max_retries=100,
        refresh_wait=1.0
):
    seconds = time_to_seconds(start_time_str)

    slot_selector = (
        f"a[href*='GlobalSalesArea_ARItemBeginDate={date_str}']"
        f"[href*='GlobalSalesArea_ARItemBeginTime={seconds}']"
    )

    for attempt in range(1, max_retries + 1):
        print(f"🔁 Attempt {attempt}")

        try:
            # Wait for calendar to load
            page.wait_for_selector("a.calendar__block", timeout=10000)

            # Click slot
            page.locator(slot_selector).click(timeout=200)

            # Click Add To Cart
            page.locator("button:has-text('Add To Cart')").click(timeout=5000)

            print("✅ Slot added to cart!")
            return True

        except PlaywrightTimeoutError:
            print("⏳ Not clickable yet — refreshing")
            page.reload(wait_until="domcontentloaded")
            time.sleep(refresh_wait)

    print("❌ Max retries reached")
    return False


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # visible browser
    context = browser.new_context()
    page = context.new_page()

    # Open site
    page.goto("https://myfitrec.bu.edu/webtrac/web/")

    # Click "My Account"
    page.locator(
        "span.menuitem__subtitle",
        has_text="My Account"
    ).click()

    # Click "LOG IN WITH BU.EDU EMAIL"
    page.locator(
        "a",
        has_text="LOG IN WITH BU.EDU EMAIL"
    ).click()

    # Fill username & password
    page.wait_for_selector("#j_username")
    if is_boan:
        page.fill("#j_username", "")
        page.fill("#j_password", "")
    else:
        page.fill("#j_username", "")
        page.fill("#j_password", "")

    # Submit login
    page.keyboard.press("Enter")

    try:
        # Wait for the "Continue with Login" button to appear
        page.wait_for_selector("#loginresumesession_buttoncontinue", timeout=30000)

        # Click it
        page.click("#loginresumesession_buttoncontinue")
        print("Clicked post-Duo continue button.")

    # except TimeoutError:
    except Exception as e:
        # If the button didn't appear in 5 seconds, skip
        print("Post-Duo continue button not present, skipping.")


    # # Wait for the "Continue with Login" button to appear
    # page.wait_for_selector("#loginresumesession_buttoncontinue", timeout=30000)
    #
    # # Click it
    # page.click("#loginresumesession_buttoncontinue")


    # Wait until back on myfitrec
    page.wait_for_function(
        "() => window.location.hostname.includes('myfitrec.bu.edu')",
        timeout=120_000
    )

    # Navigate to reservation search page
    page.goto(
        # "https://myfitrec.bu.edu/webtrac/web/search.html?BeginDate=03/01/2026&BeginMonth=3&BeginYear=2026&category=&Date=03/01/2026&daysofweek=&Display=Calendar&EndDate=03/31/2026&instructor=&keyword=&keywordoption=Match%20One&Module=ar&primarycode=&sort=ActivityNumber&type=ttcreservations&_csrf_token=Sp6F1H1205642F431D4O3T5N5N4D5O52005J4S5G4Z0E5M4K626F186R4G6G5C1E6R4I5I5A1C4S5W514L086S4E6F4S0F5U5Q556I1H5H3R6I686T5K4B5265724N4R56"
        "https://myfitrec.bu.edu/webtrac/web/search.html?BeginDate=09/23/2026&BeginMonth=9&BeginYear=2026&category=&Date=09/23/2026&daysofweek=&Display=Calendar&EndDate=09/30/2026&instructor=&keyword=&keywordoption=Match%20One&Module=ar&primarycode=&sort=ActivityNumber&type=ttcreservations&_csrf_token=jn0P16701E1A2K35234H2M4K6Z5U486I055N5Z5P670A5S4O5B6C715S4F544008735T575F6Y5O606P54706X5Z5B510E5S4Q6F4X1S6S4U586H0A5M4F6L4W1D4L4U5E"
    )

    print(f"today is {today}; target datetime {date_str} {start_time_str}; will refresh at {refresh_time_str}")

    refresh_at(page, refresh_time_str, early_second=5)

    try_click_slot_and_add_to_cart(
        page,
        date_str=date_str,
        start_time_str=start_time_str,
        max_retries=600,
        refresh_wait=0
    )

    # Keep browser open for debugging
    time.sleep(1000)
    browser.close()
