import asyncio
import unittest
from unittest.mock import patch

import httpx
from bs4 import BeautifulSoup

import main


class QuickLeadV665FreezeCandidateTests(unittest.TestCase):
    def test_booking_dotcom_restored_from_title_brand_evidence(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Booking.com | Official site | Hotels and more</title></head>
              <body><h1>Find your next stay</h1></body>
            </html>
            """,
            "html.parser",
        )
        self.assertEqual(
            main.extract_canonical_dotcom_brand_candidate(
                soup,
                "https://www.booking.com/",
                "Booking",
            ),
            "Booking.com",
        )

    def test_booking_dotcom_restored_from_corporate_footer_evidence(self):
        soup = BeautifulSoup(
            """
            <html><body>
              <footer>
                <a>About Booking.com</a>
                <p>Booking.com is part of Booking Holdings Inc.</p>
                <p>Copyright © 1996–2026 Booking.com™. All rights reserved.</p>
              </footer>
            </body></html>
            """,
            "html.parser",
        )
        self.assertEqual(
            main.extract_canonical_dotcom_brand_candidate(
                soup,
                "https://booking.com",
                "Booking",
            ),
            "Booking.com",
        )

    def test_dotcom_is_not_added_from_a_casual_domain_mention(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Slack | AI Work Platform</title></head>
              <body><p>Visit slack.com/help for documentation.</p></body>
            </html>
            """,
            "html.parser",
        )
        self.assertEqual(
            main.extract_canonical_dotcom_brand_candidate(
                soup,
                "https://slack.com",
                "Slack",
            ),
            "",
        )

    def test_short_bare_tel_noise_stays_rejected_even_after_us_hint(self):
        html = """
        <html lang="en-US">
          <head>
            <title>Mailchimp</title>
            <meta property="og:site_name" content="Mailchimp" />
            <meta name="description" content="Email marketing platform" />
          </head>
          <body>
            <address>Atlanta, GA 30308</address>
            <a href="tel:+1 (800) 315-5939">Sales</a>
            <a href="tel:1-800-330-4838">Support</a>
            <a href="tel:20012026">noise</a>
            <a href="tel:05005011">noise</a>
            <h1>Email marketing</h1>
          </body>
        </html>
        """

        async def fake_fetch(_client, _url):
            request = httpx.Request("GET", "https://mailchimp.com")
            response = httpx.Response(200, request=request, text=html)
            return response, ["https://mailchimp.com"]

        async def run_scan():
            with patch.object(main, "fetch_url_with_fallback", side_effect=fake_fetch):
                return await main.process_single_url(None, "https://mailchimp.com")

        result = asyncio.run(run_scan())
        phone_digits = {
            "".join(ch for ch in phone if ch.isdigit())
            for phone in result["phones"]
        }
        self.assertIn("18003155939", phone_digits)
        self.assertIn("18003304838", phone_digits)
        self.assertNotIn("20012026", phone_digits)
        self.assertNotIn("05005011", phone_digits)

    def test_low_opportunity_render_verify_without_email_is_skip(self):
        html = """
        <html>
          <head>
            <title>Booking.com | Official site</title>
          </head>
          <body>
            <h1>Travel marketplace</h1>
            <p>About Booking.com</p>
            <p>Booking.com is part of Booking Holdings Inc.</p>
          </body>
        </html>
        """

        async def fake_fetch(_client, _url):
            request = httpx.Request("GET", "https://www.booking.com/")
            response = httpx.Response(200, request=request, text=html)
            return response, ["https://www.booking.com/"]

        async def run_scan():
            with patch.object(main, "fetch_url_with_fallback", side_effect=fake_fetch):
                return await main.process_single_url(None, "https://booking.com")

        result = asyncio.run(run_scan())
        self.assertEqual(result["business_name"], "Booking.com")
        intelligence = result["intelligence"]
        if (
            intelligence["opportunity_score"] < 40
            and not result["contactability"].get("preferred_email")
        ):
            self.assertEqual(intelligence["prospect_decision"], "SKIP")

    def test_backend_version_is_v665_or_later_patch(self):
        self.assertRegex(main.app.version, r"^6\.6\.(?:[5-9]|[1-9]\d+)$")


if __name__ == "__main__":
    unittest.main()
