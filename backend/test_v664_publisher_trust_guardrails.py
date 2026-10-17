import unittest

from bs4 import BeautifulSoup

import main


class QuickLeadV664PublisherTrustGuardrailsTests(unittest.TestCase):
    def test_customer_story_brand_cannot_replace_zoom_publisher(self):
        soup = BeautifulSoup(
            """
            <html>
              <head>
                <title>One platform to connect | Zoom</title>
                <meta property="og:site_name" content="Zoom" />
              </head>
              <body>
                <h2>Capital One</h2>
                <p>See how Capital One uses Zoom.</p>
              </body>
            </html>
            """,
            "html.parser",
        )
        self.assertFalse(
            main.business_identity_has_publisher_evidence(soup, "Capital One")
        )
        result = main.apply_publisher_identity_guard(
            soup, "Capital One", "json_ld_name", 95, "Zoom", True
        )
        self.assertEqual(result[0], "Zoom")
        self.assertTrue(result[1].startswith("publisher_"))

    def test_campaign_heading_cannot_replace_wipro_publisher(self):
        soup = BeautifulSoup(
            """
            <html>
              <head>
                <title>Wipro | Technology Services &amp; Consulting</title>
                <meta property="og:site_name" content="Wipro" />
              </head>
              <body>
                <h1>BREAKTHROUGHS TO BUSINESS VALUE</h1>
              </body>
            </html>
            """,
            "html.parser",
        )
        result = main.apply_publisher_identity_guard(
            soup,
            "BREAKTHROUGHS TO BUSINESS VALUE",
            "visible_h1_identity",
            92,
            "Wipro",
            True,
        )
        self.assertEqual(result[0], "Wipro")

    def test_legal_professional_identity_is_not_replaced_by_generic_domain_brand(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>CPA In Austin | Austin Accounting</title></head>
              <body><p>Tanya L. Stokes, CPA serves Austin businesses.</p></body>
            </html>
            """,
            "html.parser",
        )
        result = main.apply_publisher_identity_guard(
            soup,
            "Tanya L. Stokes, CPA",
            "json_ld_name",
            95,
            "CPA In Austin",
            True,
        )
        self.assertEqual(result[0], "Tanya L. Stokes, CPA")

    def test_booking_dotcom_canonical_spelling_is_preserved(self):
        soup = BeautifulSoup(
            """
            <html>
              <head>
                <title>Booking.com | Official site</title>
                <meta property="og:site_name" content="Booking.com" />
              </head>
            </html>
            """,
            "html.parser",
        )
        result = main.apply_publisher_identity_guard(
            soup, "Booking", "domain_inference", 82, "Booking", True
        )
        self.assertEqual(result[0], "Booking.com")

    def test_bare_short_tel_ids_are_rejected_before_phone_normalization(self):
        soup = BeautifulSoup(
            """
            <html><body>
              <a href="tel:+1 (800) 315-5939">Sales</a>
              <a href="tel:20012026">noise</a>
              <a href="tel:05005011">noise</a>
            </body></html>
            """,
            "html.parser",
        )
        phones = main.extract_phone_numbers(soup, str(soup))
        self.assertIn("+18003155939", phones)
        self.assertNotIn("20012026", phones)
        self.assertNotIn("05005011", phones)

    def test_body_h2_is_not_publisher_evidence(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Zoom</title></head>
              <body><h2>Capital One</h2></body>
            </html>
            """,
            "html.parser",
        )
        self.assertFalse(
            main.business_identity_has_publisher_evidence(soup, "Capital One")
        )
        self.assertTrue(
            main.business_identity_has_publisher_evidence(soup, "Zoom")
        )

    def test_backend_version_is_v664(self):
        self.assertEqual(main.app.version, "6.6.4")


if __name__ == "__main__":
    unittest.main()
