import unittest
from bs4 import BeautifulSoup
import main


class QuickLeadV661FinalPolishTests(unittest.TestCase):
    def test_runtime_message_and_pronouns_are_not_business_names(self):
        rejected = [
            "JavaScript is disabled",
            "She",
            "He",
            "Her",
            "Tax Consultant",
            "CPA Firm in Austin, TX",
        ]
        for value in rejected:
            self.assertTrue(main.looks_generic_business_name(value), value)

    def test_real_names_remain_valid(self):
        valid = [
            "Arrowood Dental",
            "Meck Noonan & Co., LLC",
            "Reeves Snyder LLP",
            "Greg Copp & Company, Inc.",
        ]
        for value in valid:
            self.assertFalse(main.looks_generic_business_name(value), value)

    def test_meta_description_recovers_legal_business_name(self):
        soup = BeautifulSoup(
            '''
            <html><head>
              <title>Accounting Firm | CPA Austin | Tax Consultant</title>
              <meta name="description" content="Meck Noonan &amp; Co., LLC. is a full service tax, accounting firm located in Austin, TX." />
            </head><body></body></html>
            ''',
            "html.parser",
        )
        value, source, confidence = main.extract_meta_description_business_identity_candidate(soup)
        self.assertEqual(value, "Meck Noonan & Co., LLC")
        self.assertEqual(source, "meta_description_identity")
        self.assertGreaterEqual(confidence, 88)

    def test_arrowood_title_survives_when_visible_pronoun_is_noise(self):
        soup = BeautifulSoup(
            '''
            <html><head><title>Arrowood Dental – Odontología Familiar</title></head>
            <body><h1>She</h1></body></html>
            ''',
            "html.parser",
        )
        title = main.extract_page_title_identity_candidate(soup, "Dentist Matthews NC")
        self.assertEqual(title[0], "Arrowood Dental")
        visible = main.extract_visible_business_identity_candidate(soup)
        self.assertEqual(visible[0], "")

    def test_global_organization_address_abstains_on_global_surface(self):
        soup = BeautifulSoup(
            '''
            <html lang="en-US"><head>
              <link rel="alternate" hreflang="en-US" href="/us" />
              <link rel="alternate" hreflang="en-CA" href="/ca" />
              <link rel="alternate" hreflang="en-IN" href="/in" />
              <link rel="alternate" hreflang="fr-FR" href="/fr" />
              <script type="application/ld+json">
              {"@type":"Organization","name":"Global SaaS","address":{"@type":"PostalAddress","addressCountry":"US"}}
              </script>
            </head><body>Global product</body></html>
            ''',
            "html.parser",
        )
        locale = main.detect_locale_signals(soup, "https://example.com", [], str(soup))
        self.assertIsNone(locale["country_hint"])
        self.assertEqual(locale["country_confidence"], "Unknown")
        self.assertFalse(locale["country_evidence"]["structured_country_is_local"])

    def test_global_localbusiness_schema_remains_strong(self):
        soup = BeautifulSoup(
            '''
            <html lang="en-US"><head>
              <link rel="alternate" hreflang="en-US" href="/us" />
              <link rel="alternate" hreflang="en-CA" href="/ca" />
              <link rel="alternate" hreflang="en-IN" href="/in" />
              <script type="application/ld+json">
              {"@type":"LocalBusiness","name":"Example Dental","address":{"@type":"PostalAddress","addressCountry":"US"}}
              </script>
            </head><body></body></html>
            ''',
            "html.parser",
        )
        locale = main.detect_locale_signals(soup, "https://example.com", [], str(soup))
        self.assertEqual(locale["country_hint"], "US")
        self.assertEqual(locale["country_confidence"], "High")
        self.assertTrue(locale["country_evidence"]["structured_country_is_local"])

    def test_backend_version_is_v661(self):
        self.assertEqual(main.app.version, "6.6.1")


if __name__ == "__main__":
    unittest.main()
