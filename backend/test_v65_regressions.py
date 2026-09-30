import unittest
from bs4 import BeautifulSoup

import main


class QuickLeadV65RegressionTests(unittest.TestCase):
    def test_bare_us_numbers_do_not_become_foreign_countries(self):
        self.assertIsNone(main.get_phone_country("4048724455"))
        self.assertIsNone(main.get_phone_country("7043695200"))
        self.assertIsNone(main.get_phone_country("8174619241"))

    def test_explicit_international_prefix_is_required(self):
        self.assertEqual(main.get_phone_country("+14048724455"), "US")
        self.assertEqual(main.get_phone_country("+917975486266"), "IN")
        self.assertEqual(main.get_phone_country("00442071234567"), "GB")

    def test_us_address_gives_us_locale(self):
        soup = BeautifulSoup(
            "<footer>423 Dodson Lake Drive Arlington, TX 76012</footer>",
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

    def test_us_phone_normalization_rejects_merged_address_digits(self):
        self.assertEqual(
            main.normalize_phone_for_country("404-872-4455", "US"),
            "+14048724455",
        )
        self.assertIsNone(
            main.normalize_phone_for_country("40487244552166", "US")
        )
        self.assertIsNone(
            main.normalize_phone_for_country("282777043695200", "US")
        )

    def test_telemetry_emails_are_filtered(self):
        emails = main.extract_emails(
            "sales@hughes-mech-elect.com "
            "605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com "
            "foo@example.com"
        )
        self.assertEqual(emails, ["sales@hughes-mech-elect.com"])

    def test_hughes_agency_identity_is_overridden(self):
        html = """
        <html lang="en-US">
          <head>
            <title>Hughes Mechanical and Electrical Contractors | Dallas-Fort Worth HVAC Contractor | Arlington, TX</title>
            <script type="application/ld+json">{"@type":"Organization","name":"Sparrow Strategy LLC"}</script>
          </head>
          <body>
            <h2>Hughes</h2>
            <h2>Mechanical and Electrical Contractors</h2>
            <footer>
              423 Dodson Lake Drive Arlington, TX 76012
              <a>Website by Sparrow Strategy LLC</a>
            </footer>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        raw_name, source, confidence = main.extract_business_name(soup)
        self.assertEqual(raw_name, "Sparrow Strategy LLC")

        resolved = main.resolve_business_identity_conflict(
            soup,
            raw_name,
            source,
            confidence,
            main.infer_business_name_from_domain(
                "https://www.hughescontractorsllc.com/"
            ),
            main.infer_business_name_from_email(
                "sales@hughes-mech-elect.com"
            ),
            True,
            True,
        )
        self.assertEqual(
            resolved[0],
            "Hughes Mechanical and Electrical Contractors",
        )

    def test_ballantyne_agency_identity_is_overridden(self):
        html = """
        <html>
          <head>
            <title>Timothy L. Cox, DDS PA – 704-369-5200</title>
            <script type="application/ld+json">{"@type":"Organization","name":"Mindstorm"}</script>
          </head>
          <body>
            <h1>Carolina Dental Arts</h1>
            <footer>
              14825 Ballantyne Village Way Charlotte, NC 28277
              <span>Website by Mindstorm</span>
            </footer>
          </body>
        </html>
        """
        soup = BeautifulSoup(html, "html.parser")
        raw_name, source, confidence = main.extract_business_name(soup)
        resolved = main.resolve_business_identity_conflict(
            soup,
            raw_name,
            source,
            confidence,
            main.infer_business_name_from_domain("https://ballantynesmiles.com"),
            "",
            True,
            False,
        )
        self.assertEqual(resolved[0], "Carolina Dental Arts")


if __name__ == "__main__":
    unittest.main()
