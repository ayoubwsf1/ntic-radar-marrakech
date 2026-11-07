import unittest

from stageradar.ai.email_ai import classifier_hybride, parse_reponse
from stageradar.classification import classify


class FakeLLM:
    def __init__(self, reponse, available=True):
        self.reponse, self.available = reponse, available

    def complete(self, *a, **k):
        return self.reponse


class TestClassification(unittest.TestCase):
    def test_regles(self):
        self.assertEqual(classify("Entretien", "Pouvez-vous donner vos disponibilités ?")[0], "Entretien")
        self.assertEqual(classify("Votre candidature", "Malheureusement nous ne pouvons pas donner suite.")[0], "Refusé")
        self.assertEqual(classify("Félicitations", "Votre candidature est retenue")[0], "Accepté")
        self.assertIsNone(classify("Newsletter", "Nos offres du mois")[0])

    def test_parse_json(self):
        self.assertEqual(parse_reponse('```json\n{"statut": "Entretien", "raison": "invitation"}\n```')[0], "Entretien")
        self.assertIsNone(parse_reponse('{"statut": "Aucun", "raison": ""}')[0])
        self.assertIsNone(parse_reponse("pas du json")[0])

    def test_hybride(self):
        llm = FakeLLM('{"statut": "Refusé", "raison": "refus poli"}')
        # les règles ne trouvent rien -> le LLM tranche
        self.assertEqual(classifier_hybride("Suite", "Nous poursuivons avec une autre piste.", llm)[0], "Refusé")
        # les règles trouvent -> le LLM n'est pas sollicité
        self.assertEqual(classifier_hybride("Entretien", "rendez-vous", FakeLLM('{"statut":"Refusé"}'))[0], "Entretien")
        # sans LLM disponible -> None
        self.assertIsNone(classifier_hybride("Suite", "rien", FakeLLM("", available=False))[0])


if __name__ == "__main__":
    unittest.main()
