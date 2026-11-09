import json
import unittest

from stageradar import cv_render
from stageradar.ai import cv
from stageradar.ai.profile import Profil, parse_competences


def profil():
    return Profil(
        nom="Sara Alami", email="sara@example.com", telephone="0600000000", liens="github.com/sara",
        formation="Technicien spécialisé en développement digital, OFPPT Marrakech\nBaccalauréat sciences",
        competences=["Python", "SQL", "React"],
        experiences="Stagiaire web — Agence X (juillet 2025)\nIntégration de maquettes\nCorrection de bugs",
        projets="Ntic Radar\nPlateforme Streamlit de suivi des candidatures",
        interets="IA, web", langues="Arabe, Français, Anglais",
    )


class FakeLLM:
    def __init__(self, reponse, available=True):
        self.reponse, self.available, self.model = reponse, available, "fake"

    def complete(self, *a, **k):
        return self.reponse


class TestCV(unittest.TestCase):
    def test_cv_local(self):
        r = cv.generer_cv(profil())
        c = r["cv"]
        self.assertEqual(r["origine"], "local")
        self.assertEqual(c["experiences"][0]["poste"], "Stagiaire web")
        self.assertEqual(c["experiences"][0]["organisation"], "Agence X")
        self.assertEqual(c["experiences"][0]["periode"], "juillet 2025")
        self.assertEqual(c["experiences"][0]["points"], ["Intégration de maquettes", "Correction de bugs"])
        self.assertEqual(c["competences"], ["Python", "SQL", "React"])
        self.assertEqual(len(c["formation"]), 2)
        self.assertEqual(c["langues"], ["Arabe", "Français", "Anglais"])

    def test_garde_fou_anti_invention(self):
        faux = {"titre": "Développeur", "resume": "Profil motivé.",
                "formation": [{"intitule": "A"}, {"intitule": "B"}, {"intitule": "Master Harvard"}],
                "experiences": [{"poste": "Dev", "organisation": "X", "periode": "", "points": ["a"]},
                                {"poste": "CTO", "organisation": "Google", "periode": "", "points": ["b"]}],
                "projets": [{"nom": "P1", "points": []}, {"nom": "Inventé", "points": []}],
                "competences": ["python", "Kubernetes", "SQL"], "langues": ["Arabe", "Français", "Anglais", "Chinois"],
                "interets": "IA"}
        r = cv.generer_cv(profil(), llm=FakeLLM("Voici : ```json\n" + json.dumps(faux) + "\n```"))
        c = r["cv"]
        self.assertEqual(r["origine"], "IA")
        self.assertEqual(len(c["formation"]), 2)
        self.assertEqual(len(c["experiences"]), 1)
        self.assertEqual(len(c["projets"]), 1)
        self.assertNotIn("Kubernetes", c["competences"])
        self.assertEqual(len(c["langues"]), 3)
        self.assertGreaterEqual(len(r["alertes"]), 4)

    def test_repli_si_llm_illisible(self):
        r = cv.generer_cv(profil(), llm=FakeLLM("pas du json"))
        self.assertEqual(r["origine"], "local")
        self.assertTrue(r["alertes"])

    def test_cible_agence(self):
        r = cv.generer_cv(profil(), {"nom": "WebPlus", "type": "Web & Développement", "ville": "Marrakech"})
        self.assertIn("Web & Développement", r["cv"]["titre"])

    def test_parse_json(self):
        self.assertEqual(cv.parse_cv_json('x {"a": 1} y'), {"a": 1})
        self.assertIsNone(cv.parse_cv_json("rien"))
        self.assertIsNone(cv.parse_cv_json("{cassé"))

    def test_competences(self):
        self.assertEqual(parse_competences("Python; SQL,\nReact"), ["Python", "SQL", "React"])


class TestRender(unittest.TestCase):
    def test_exports(self):
        c = cv.generer_cv(profil())["cv"]
        pdf = cv_render.cv_pdf(c)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(cv_render.nom_fichier(c, "pdf"), "CV_Sara_Alami.pdf")

    def test_caracteres_speciaux_et_cv_minimal(self):
        c = {"nom": "A & B <x>", "langue": "English", "experiences": [{"poste": "R&D <dev>", "points": ["œuvre ’ ok"]}]}
        self.assertTrue(cv_render.cv_pdf(c).startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
