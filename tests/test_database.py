import tempfile
import unittest
from pathlib import Path

from stageradar import analytics, database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._old = database.DB_PATH
        database.DB_PATH = Path(self.tmp.name) / "t.db"
        database.init_db()

    def tearDown(self):
        database.DB_PATH = self._old
        self.tmp.cleanup()

    def test_agences_et_statuts(self):
        self.assertTrue(database.add_agence("Acme", "Web & Développement", "Marrakech", "https://acme.ma"))
        self.assertFalse(database.add_agence("Acme", "Web & Développement", "Marrakech", "https://acme.ma"))
        df = database.load_agences()
        database.set_statut(int(df.iloc[0]["id"]), "Entretien", "preuve")
        self.assertEqual(database.load_agences().iloc[0]["statut"], "Entretien")
        with self.assertRaises(ValueError):
            database.set_statut(1, "Inconnu")

    def test_reglages(self):
        database.set_reglage("k", "1")
        database.set_reglage("k", "2")
        self.assertEqual(database.get_reglage("k"), "2")

    def test_analytics(self):
        database.add_agence("A", "Web & Développement", "Marrakech", "https://a.ma", "SEO web")
        database.add_agence("B", "Design & Créa", "Rabat", "https://b.ma", "logo")
        df = database.load_agences()
        f = analytics.focus_ville(df)
        self.assertEqual(f["n"], 1)
        self.assertEqual(f["part"], 50.0)
        self.assertEqual(analytics.compter(df, "ville").sum(), 2)


if __name__ == "__main__":
    unittest.main()
