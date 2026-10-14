import unittest

import main


class QuickLeadV656IdentityRegressionTests(unittest.TestCase):
    def test_known_false_identities_are_rejected(self):
        self.assertTrue(main.looks_generic_business_name("JavaScript"))
        self.assertTrue(main.looks_like_non_brand_phrase("Website Builder"))
        self.assertTrue(
            main.looks_like_non_brand_phrase(
                "Free DPDP Compliance Scanner for Indian Websites"
            )
        )
        self.assertTrue(
            main.looks_like_non_brand_phrase(
                "Nike. Just Do It. Nike.com"
            )
        )

    def test_real_business_names_are_preserved(self):
        valid_names = [
            "Microsoft",
            "Jivrus Technologies",
            "Unitherm Engineers Limited",
            "Atlanta Dental Arts",
        ]

        for name in valid_names:
            self.assertFalse(main.looks_generic_business_name(name), name)
            self.assertFalse(main.looks_like_non_brand_phrase(name), name)


if __name__ == "__main__":
    unittest.main()
