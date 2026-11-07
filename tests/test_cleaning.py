import unittest

import pandas as pd

from stageradar.cleaning import nettoyer, normaliser_site


class TestCleaning(unittest.TestCase):
    def setUp(self):
        self.raw = pd.DataFrame({
            "nom ": ["Alpha Studio", "alpha studio", "Beta 【900 Dh 】", "test", "Gamma"],
            "TYPE": ["web & développement", "Web & Développement", "design", "marketing digital", "publicite"],
            "ville": ["marrakech", "Marrakech", "fes", "rabat", "Casablanca"],
            "site_web": ["HTTPS://www.Alpha.ma/", "alpha.ma", "https://beta.ma/contact", "https://t.ma", None],
            "Statut ": ["NON POSTULE", "", "A postuler", "x", "Entretien"],
            "Source": ["gmaps", "google maps", "Clutch", "", "tavily"],
        })

    def test_pipeline(self):
        df, rap = nettoyer(self.raw)
        self.assertEqual(len(df), 3)                       # doublon + ligne « test » supprimés
        self.assertIn("Marrakech", set(df["Ville"]))
        self.assertIn("Fès", set(df["Ville"]))
        self.assertTrue(set(df["Statut"]) <= {"Non encore postulé", "Entretien", "Accepté", "Refusé"})
        self.assertEqual(df.loc[df["Nom"].str.startswith("Beta"), "Nom"].iloc[0], "Beta")
        self.assertTrue(df["Latitude"].notna().all())
        self.assertEqual(rap.lignes_entree, 5)
        self.assertEqual(rap.lignes_sortie, 3)

    def test_site(self):
        self.assertEqual(normaliser_site("HTTPS://www.Alpha.ma/contact"), "https://alpha.ma")
        self.assertEqual(normaliser_site("alpha.ma"), "https://alpha.ma")
        self.assertEqual(normaliser_site(None), "")
        self.assertEqual(normaliser_site("pas un site"), "")


if __name__ == "__main__":
    unittest.main()
