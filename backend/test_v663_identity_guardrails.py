import asyncio
import unittest
from unittest.mock import patch

import httpx
from bs4 import BeautifulSoup

import main


class QuickLeadV663IdentityGuardrailsTests(unittest.TestCase):
    def test_navigation_concatenation_is_not_identity(self):
        self.assertTrue(
            main.looks_generic_business_name("WG About Us Proven Process")
        )

    def test_dotcom_brand_is_equivalent_to_bare_brand(self):
        self.assertTrue(
            main.business_names_equivalent("Booking.com", "Booking")
        )

    def test_single_token_overlap_is_not_strong_domain_consensus(self):
        self.assertFalse(
            main.strong_business_identity_matches_domain(
                "WG About Us Proven Process",
                "WG CPA",
            )
        )

    def test_zoom_domain_aligned_identity_beats_customer_story_name(self):
        soup = BeautifulSoup(
            """
            <html>
              <head>
                <title>One platform to connect | Zoom</title>
                <meta property="og:site_name" content="Zoom" />
              </head>
              <body>
                <h2>Trusted by millions. Built for you.</h2>
                <p>A connected, collaborative workforce drives innovation at Capital One.</p>
              </body>
            </html>
            """,
            "html.parser",
        )

        result = main.resolve_business_identity_conflict(
            soup,
            "Zoom",
            "meta_site_identity",
            91,
            "Zoom",
            "",
            True,
            False,
        )

        self.assertEqual(result[0], "Zoom")
        self.assertEqual(result[1], "meta_site_identity")

    def test_walker_glantz_beats_responsive_menu_text(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Home - Walker Glantz</title></head>
              <body>
                <nav><span>About WG About Us Proven Process</span></nav>
                <p>Walker Glantz exists to help business owners succeed.</p>
                <footer>Copyright 2025 Walker Glantz</footer>
              </body>
            </html>
            """,
            "html.parser",
        )

        repeated = main.extract_repeated_visible_business_identity_candidate(soup)
        self.assertEqual(repeated[0], "")

        result = main.resolve_business_identity_conflict(
            soup,
            "Walker Glantz",
            "title_identity",
            90,
            "WG CPA",
            "",
            True,
            False,
        )

        self.assertEqual(result[0], "Walker Glantz")

    def test_staff_first_name_loses_to_primary_multiword_brand(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Arrowood Dental – Odontología Familiar</title></head>
              <body>
                <h4>This place is friendly! Marvin is attentive and hardworking.</h4>
                <p>Grateful to the entire team at Arrowood Dental.</p>
              </body>
            </html>
            """,
            "html.parser",
        )

        result = main.resolve_business_identity_conflict(
            soup,
            "Marvin",
            "json_ld_name",
            95,
            "Dentistmatthewsnc",
            "",
            True,
            False,
        )

        self.assertEqual(result[0], "Arrowood Dental")
        self.assertEqual(result[1], "title_identity")

    def test_domain_aligned_one_word_brand_stays_valid(self):
        self.assertTrue(
            main.strong_business_identity_matches_domain("Zoom", "Zoom")
        )
        self.assertTrue(
            main.strong_business_identity_matches_domain("Nike", "Nike")
        )

    def test_all_retina_media_pseudo_emails_are_rejected(self):
        html = " ".join(
            [
                "hp-channels@2x.mp",
                "hp-channels@2x.webm",
                "hp-workflows@2x.mp",
                "hp-workflows@2x.webm",
                "claude-ai@2x.webm",
                "anthropic@2x.mp",
                "hello@realbusiness.com",
            ]
        )

        self.assertEqual(
            main.extract_emails(html),
            ["hello@realbusiness.com"],
        )

    def test_unknown_locale_drops_short_numeric_tel_noise_in_full_scan(self):
        html = """
        <html lang="en">
          <head>
            <title>Mailchimp</title>
            <meta property="og:site_name" content="Mailchimp" />
            <meta name="description" content="Email marketing platform" />
          </head>
          <body>
            <a href="tel:+1 (800) 315-5939">Sales</a>
            <a href="tel:20012026">noise</a>
            <a href="tel:05005011">noise</a>
            <h1>Email marketing</h1>
          </body>
        </html>
        """

        async def fake_fetch(_client, _url):
            request = httpx.Request("GET", "https://mailchimp.com")
            response = httpx.Response(
                200,
                request=request,
                text=html,
            )
            return response, ["https://mailchimp.com"]

        async def run_scan():
            with patch.object(
                main,
                "fetch_url_with_fallback",
                side_effect=fake_fetch,
            ):
                return await main.process_single_url(
                    None,
                    "https://mailchimp.com",
                )

        result = asyncio.run(run_scan())
        self.assertEqual(result["phones"], ["+18003155939"])

    def test_meck_legal_recovery_still_survives_stricter_guardrails(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Accounting Firm | CPA Austin | Tax Consultant</title></head>
              <body>
                <p>Meck Noonan &amp; Co., LLC has deep roots in Austin.</p>
                <h3>Meck Noonan &amp; Co., LLC</h3>
              </body>
            </html>
            """,
            "html.parser",
        )

        result = main.resolve_business_identity_conflict(
            soup,
            "Meckcpaaustin",
            "domain_inference",
            82,
            "Meckcpaaustin",
            "",
            True,
            False,
        )

        self.assertEqual(result[0], "Meck Noonan & Co., LLC")
        self.assertEqual(result[1], "repeated_visible_identity")

    def test_backend_version_is_v663(self):
        self.assertEqual(main.app.version, "6.6.3")


if __name__ == "__main__":
    unittest.main()
