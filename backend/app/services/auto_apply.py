import os
import logging
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

def run_auto_apply(profile, job_url: str):
    """
    Opens a visible Chromium browser via Playwright, navigates to the job_url,
    and attempts to auto-fill common application fields (First Name, Last Name, Email, Resume).
    Leaves the browser open for 5 minutes so the user can review and click submit.
    """
    logger.info(f"Starting auto-apply for {job_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        
        try:
            page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)
            
            names = (profile.full_name or "").split(" ")
            first_name = names[0] if names else ""
            last_name = names[-1] if len(names) > 1 else ""
            email = profile.user.email if profile.user else ""
            
            resume_path = None
            if profile.resume_path:
                resume_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", profile.resume_path))
                if not os.path.exists(resume_path):
                    resume_path = None

            # First Name
            first_name_selectors = ['input[name*="first"][type="text" i]', 'input[name*="firstName" i]', 'input[id*="first_name" i]', 'input[aria-label*="first name" i]']
            for sel in first_name_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.fill(first_name)
                        break
                except Exception:
                    pass

            # Last Name
            last_name_selectors = ['input[name*="last"][type="text" i]', 'input[name*="lastName" i]', 'input[id*="last_name" i]', 'input[aria-label*="last name" i]']
            for sel in last_name_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.fill(last_name)
                        break
                except Exception:
                    pass
                    
            # Full Name
            full_name_selectors = ['input[name="name" i]', 'input[name="fullName" i]', 'input[id="name" i]']
            for sel in full_name_selectors:
                try:
                    if page.locator(sel).count() > 0:
                        page.locator(sel).first.fill(profile.full_name)
                        break
                except Exception:
                    pass

            # Email
            if email:
                email_selectors = ['input[type="email" i]', 'input[name*="email" i]', 'input[id*="email" i]']
                for sel in email_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.fill(email)
                            break
                    except Exception:
                        pass
                        
            # Resume
            if resume_path:
                file_selectors = ['input[type="file" i]', 'input[name*="resume" i]', 'input[name*="cv" i]']
                for sel in file_selectors:
                    try:
                        if page.locator(sel).count() > 0:
                            page.locator(sel).first.set_input_files(resume_path)
                            break
                    except Exception:
                        pass

            # Wait for 5 minutes
            logger.info("Form filled heuristically. Keeping browser open for 5 minutes for user review.")
            page.wait_for_timeout(300000)
            
        except Exception as e:
            logger.error(f"Auto-apply error: {e}")
            page.wait_for_timeout(30000)
        finally:
            browser.close()
