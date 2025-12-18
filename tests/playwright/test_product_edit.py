"""
Django Amazon Clone Product Edit Page Tests
Implements Playwright-Kualitee integration using the Push Model

Each test is mapped to a Kualitee test case using the @pytest.mark.kualitee_id marker
Test results are automatically reported to Kualitee via the conftest.py hook
"""

import pytest
from playwright.sync_api import Page, expect


class TestProductEditPage:
    """Product edit page functionality tests"""

    @pytest.mark.kualitee_id("AGENTIC-136")
    def test_product_edit_shows_last_updated_timestamp(self, page: Page, server_url):
        """Test that product edit page displays last updated timestamp"""
        # Navigate to product edit page (assuming product ID 1 exists)
        # Note: This requires authentication and a valid product ID
        page.goto(f"{server_url}/admindashboard/product_edit/1")

        # Verify page loads
        expect(page.locator("h4")).to_contain_text("Product Edit")

        # Verify "Last Updated" timestamp is visible
        # The timestamp should be in the card header
        last_updated_text = page.locator("text=Last Updated")
        expect(last_updated_text).to_be_visible()

        # Verify timestamp format (should contain date and time)
        # Format: "Last Updated: Month Day, Year Hour:Minute AM/PM"
        timestamp_pattern = r"Last Updated: \w+ \d+, \d{4} \d{1,2}:\d{2} [AP]M"
        timestamp_element = page.locator("small.text-muted:has-text('Last Updated')")
        expect(timestamp_element).to_be_visible()
        
        # Verify the timestamp text matches expected format
        timestamp_text = timestamp_element.inner_text()
        import re
        assert re.search(timestamp_pattern, timestamp_text), \
            f"Timestamp format incorrect. Expected pattern: {timestamp_pattern}, Got: {timestamp_text}"

    @pytest.mark.kualitee_id("AGENTIC-136-UPDATE")
    def test_product_edit_updates_timestamp_on_save(self, page: Page, server_url):
        """Test that product edit updates the timestamp when product is saved"""
        # Navigate to product edit page
        page.goto(f"{server_url}/admindashboard/product_edit/1")

        # Get initial timestamp
        initial_timestamp = page.locator("small.text-muted:has-text('Last Updated')").inner_text()
        
        # Make a change to the product (e.g., update product name)
        product_name_field = page.locator("input[name='product_name']")
        if product_name_field.is_visible():
            current_value = product_name_field.input_value()
            new_value = f"{current_value} (Updated)"
            product_name_field.fill(new_value)
            
            # Submit the form
            submit_button = page.locator("button:has-text('EDIT PRODUCT')")
            submit_button.click()
            
            # Wait for page to reload or redirect
            page.wait_for_timeout(2000)
            
            # Navigate back to edit page to check updated timestamp
            page.goto(f"{server_url}/admindashboard/product_edit/1")
            
            # Get new timestamp
            updated_timestamp = page.locator("small.text-muted:has-text('Last Updated')").inner_text()
            
            # Verify timestamp has changed (this is a basic check - in real scenario,
            # you'd parse and compare the actual datetime values)
            assert updated_timestamp != initial_timestamp, \
                "Timestamp should have been updated after product edit"
        else:
            pytest.skip("Product name field not found - may need authentication or different product ID")

