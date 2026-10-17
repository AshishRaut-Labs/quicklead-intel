import asyncio
import unittest
from unittest.mock import patch

import httpx

import main


class QuickLeadV666SalesFreezeTests(unittest.TestCase):
    def test_strict_locales_reject_ambiguous_short_numbers(self):
        for country in [None, "US", "CA", "IN"]:
            self.assertTrue(main.reject_ambiguous_short_phone_for_locale("20-01-2026", country))
            self.assertTrue(main.reject_ambiguous_short_phone_for_locale("05-005-011", country))

    def test_short_number_market_is_not_globally_disabled(self):
        self.assertFalse(
            main.reject_ambiguous_short_phone_for_locale("6123 4567", "SG")
        )

    def test_mailchimp_style_formatted_noise_is_removed_after_us_locale_hint(self):
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
            <footer>20-01-2026 | 05-005-011</footer>
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

    def test_backend_version_is_v666(self):
        self.assertEqual(main.app.version, "6.6.6")


if __name__ == "__main__":
    unittest.main()
