import unittest
from bs4 import BeautifulSoup
import main


class QuickLeadV662TrustContactQualityTests(unittest.TestCase):
    def test_punctuation_wrapped_pronoun_is_not_identity(self):
        self.assertTrue(main.looks_generic_business_name("me."))
        self.assertTrue(main.looks_generic_business_name("She!"))

    def test_generic_profession_seo_title_is_not_identity(self):
        self.assertTrue(main.looks_generic_business_name("Austin CPA Accounting Firm"))
        self.assertFalse(main.looks_generic_business_name("Dawson Modern Dentistry"))

    def test_all_family_dentistry_recovered_from_visible_copy(self):
        soup = BeautifulSoup(
            """
            <html><head><title>Dentist Matthews – Odontología Familiar</title></head>
            <body>
              <h1>She</h1>
              <p>At All Family Dentistry, we take care of restoring your teeth and improving appearance.</p>
            </body></html>
            """,
            "html.parser",
        )
        value, source, confidence = main.extract_repeated_visible_business_identity_candidate(soup)
        self.assertEqual(value, "All Family Dentistry")
        self.assertEqual(source, "repeated_visible_identity")
        self.assertGreaterEqual(confidence, 88)

    def test_meck_legal_name_recovered_from_visible_copy(self):
        soup = BeautifulSoup(
            """
            <html><head><title>Accounting Firm | CPA Austin | Tax Consultant</title></head>
            <body>
              <h1>Home</h1>
              <p>Meck Noonan &amp; Co., LLC has deep roots in Austin and central Texas.</p>
              <h3>Meck Noonan &amp; Co., LLC</h3>
            </body></html>
            """,
            "html.parser",
        )
        value, source, confidence = main.extract_repeated_visible_business_identity_candidate(soup)
        self.assertEqual(value, "Meck Noonan & Co., LLC")
        self.assertEqual(source, "repeated_visible_identity")
        self.assertGreaterEqual(confidence, 90)

    def test_tanya_cpa_professional_name_recovered(self):
        soup = BeautifulSoup(
            """
            <html><head><title>Austin CPA Accounting Firm</title></head>
            <body><footer>
              <strong>Tanya L. Stokes, CPA</strong>
              <p>Tanya L. Stokes, CPA provides tax and accounting services.</p>
            </footer></body></html>
            """,
            "html.parser",
        )
        value, source, confidence = main.extract_repeated_visible_business_identity_candidate(soup)
        self.assertEqual(value, "Tanya L. Stokes, CPA")
        self.assertEqual(source, "repeated_visible_identity")
        self.assertGreaterEqual(confidence, 90)

    def test_repeated_visible_name_beats_domain_fallback(self):
        soup = BeautifulSoup(
            """
            <html><head><title>Accounting Firm | CPA Austin | Tax Consultant</title></head>
            <body>
              <p>Meck Noonan &amp; Co., LLC has deep roots in Austin and central Texas.</p>
              <h3>Meck Noonan &amp; Co., LLC</h3>
            </body></html>
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

    def test_asset_filename_is_not_email(self):
        html = "video-slackbot-big-mode@2x.mp4 hello@realbusiness.com"
        emails = main.extract_emails(html)
        self.assertNotIn("video-slackbot-big-mode@2x.mp", emails)
        self.assertIn("hello@realbusiness.com", emails)

    def test_url_encoded_email_deduplicates(self):
        html = "%20info@dentistmatthewsnc.com info@dentistmatthewsnc.com"
        self.assertEqual(
            main.extract_emails(html),
            ["info@dentistmatthewsnc.com"],
        )

    def test_numeric_noise_is_rejected(self):
        for value in [
            "0123456789",
            "202599999",
            "20012026",
            "05005011",
        ]:
            self.assertTrue(main.looks_like_low_confidence_phone_candidate(value), value)

    def test_real_phone_shapes_remain_allowed(self):
        for value in [
            "+18889262289",
            "18003304838",
            "(704) 847-0161",
        ]:
            self.assertFalse(main.looks_like_low_confidence_phone_candidate(value), value)

    def test_backend_version_is_v662(self):
        self.assertEqual(main.app.version, "6.6.2")


if __name__ == "__main__":
    unittest.main()
