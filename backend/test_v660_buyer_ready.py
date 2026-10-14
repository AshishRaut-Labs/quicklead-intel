import asyncio
import unittest

import httpx
from bs4 import BeautifulSoup

import main


class FakeBlockedClient:
    def __init__(self):
        self.calls = []

    async def get(self, url, headers=None):
        self.calls.append(url)
        request = httpx.Request("GET", url)
        return httpx.Response(403, request=request)


class QuickLeadV660BuyerReadyTests(unittest.TestCase):
    def test_html_entities_are_decoded_in_business_names(self):
        self.assertEqual(
            main.clean_business_name_candidate(
                "Steve Brown &amp; Associates, LLC"
            ),
            "Steve Brown & Associates, LLC",
        )

    def test_generic_and_slogan_identities_are_rejected(self):
        rejected = [
            "Home Page",
            "CPA Austin",
            "Dentist Matthews",
            "only way we make money",
            "Find out what's possible when work connects",
        ]

        for value in rejected:
            self.assertTrue(
                main.looks_generic_business_name(value),
                value,
            )

    def test_marketing_suffix_is_removed_from_brand(self):
        self.assertEqual(
            main.clean_business_name_candidate(
                "Ahrefs—AI Marketing Platform"
            ),
            "Ahrefs",
        )

    def test_real_business_names_are_not_over_rejected(self):
        valid = [
            "Dawson Modern Dentistry",
            "Fort Worth Air",
            "Walker Glantz CPAs",
            "Ryan Rapp Pacheco Sorensen PLC",
            "Steve Brown & Associates, LLC",
        ]

        for value in valid:
            self.assertFalse(
                main.looks_generic_business_name(value),
                value,
            )

    def test_visible_identity_survives_generic_home_page_title(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Home Page</title></head>
              <body><h1>Reeves Snyder LLP</h1></body>
            </html>
            """,
            "html.parser",
        )

        visible = main.extract_visible_business_identity_candidate(soup)
        self.assertEqual(visible[0], "Reeves Snyder LLP")
        self.assertEqual(visible[1], "visible_h1_identity")

    def test_visible_h1_beats_domain_fallback_identity(self):
        soup = BeautifulSoup(
            """
            <html>
              <head><title>Home Page</title></head>
              <body><h1>Reeves Snyder LLP</h1></body>
            </html>
            """,
            "html.parser",
        )

        resolved = main.resolve_business_identity_conflict(
            soup,
            "Rstax CPA",
            "domain_inference",
            75,
            "Rstax CPA",
            "",
            True,
            False,
        )

        self.assertEqual(resolved[0], "Reeves Snyder LLP")
        self.assertEqual(resolved[1], "visible_h1_identity")

    def test_cpa_domain_suffix_is_split_cleanly(self):
        self.assertEqual(
            main.infer_business_name_from_domain("https://coppcpa.com"),
            "Copp CPA",
        )

    def test_global_locale_surface_abstains_from_support_phone_guess(self):
        soup = BeautifulSoup(
            """
            <html lang="en-US">
              <head>
                <link rel="alternate" hreflang="en-US" href="/us" />
                <link rel="alternate" hreflang="en-IN" href="/in" />
                <link rel="alternate" hreflang="pt-BR" href="/br" />
                <link rel="alternate" hreflang="fr-FR" href="/fr" />
              </head>
              <body>Global product website</body>
            </html>
            """,
            "html.parser",
        )

        locale = main.detect_locale_signals(
            soup,
            "https://example.com",
            ["+919876543210"],
            str(soup),
        )

        self.assertIsNone(locale["country_hint"])
        self.assertEqual(locale["country_confidence"], "Unknown")
        self.assertTrue(
            locale["country_evidence"]["global_locale_surface"]
        )

    def test_structured_country_is_high_confidence(self):
        soup = BeautifulSoup(
            """
            <html>
              <head>
                <script type="application/ld+json">
                {
                  "@type":"LocalBusiness",
                  "name":"Example Dental",
                  "address":{
                    "@type":"PostalAddress",
                    "addressCountry":"US"
                  }
                }
                </script>
              </head>
              <body></body>
            </html>
            """,
            "html.parser",
        )

        locale = main.detect_locale_signals(
            soup,
            "https://example.com",
            [],
            str(soup),
        )

        self.assertEqual(locale["country_hint"], "US")
        self.assertEqual(locale["country_confidence"], "High")
        self.assertEqual(
            locale["country_evidence"]["structured_country"],
            "US",
        )

    def test_local_india_evidence_still_wins(self):
        soup = BeautifulSoup(
            """
            <html lang="en-IN">
              <body>
                <footer>
                  Bhubaneswar, Odisha, India 751001
                  +91 98765 43210
                </footer>
              </body>
            </html>
            """,
            "html.parser",
        )

        locale = main.detect_locale_signals(
            soup,
            "https://example.in",
            ["+919876543210"],
            str(soup),
        )

        self.assertEqual(locale["country_hint"], "IN")
        self.assertEqual(locale["country_confidence"], "High")

    def test_repeated_403_is_classified_as_blocked_and_stops_early(self):
        client = FakeBlockedClient()

        with self.assertRaises(main.WebsiteFetchError) as ctx:
            asyncio.run(
                main.fetch_url_with_fallback(
                    client,
                    "https://example.com",
                )
            )

        exc = ctx.exception
        self.assertEqual(exc.status, "Blocked")
        self.assertEqual(exc.failure_type, "ACCESS_BLOCKED")
        self.assertLessEqual(len(client.calls), 4)

    def test_global_product_site_is_deprioritized_for_local_smb_outreach(self):
        data = {
            "business_name": "Stripe",
            "business_name_confidence": 95,
            "title": "Stripe",
            "meta_description": "Payments infrastructure",
            "h1_count": 1,
            "conversion_signals": {},
            "conversion_evidence": {},
            "technical_signals": {},
            "trackers": {},
            "locale_signals": {
                "country_evidence": {
                    "global_locale_surface": True,
                }
            },
            "contactability": {
                "score": 90,
                "level": "HIGH",
                "preferred_email": "sales@example.com",
                "verification_required": False,
            },
            "quality_signals": {},
            "business_signals": {},
            "phones": [],
            "emails": ["sales@example.com"],
        }

        result = main.generate_sales_intel(data)

        self.assertNotEqual(result["prospect_decision"], "CONTACT")
        self.assertLess(result["prospect_score"], 60)

    def test_backend_version_is_v660(self):
        self.assertEqual(main.app.version, "6.6.0")


if __name__ == "__main__":
    unittest.main()
