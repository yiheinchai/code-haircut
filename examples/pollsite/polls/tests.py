from django.test import TestCase
from django.utils import timezone

from .models import Choice, Question


class PollsTests(TestCase):
    def setUp(self):
        self.question = Question.objects.create(
            question_text="Is sliced Django enough?",
            pub_date=timezone.now(),
        )
        self.choice = Choice.objects.create(
            question=self.question,
            choice_text="Yes",
            votes=0,
        )

    def test_index_lists_question(self):
        response = self.client.get("/polls/")
        self.assertContains(response, "Is sliced Django enough?")

    def test_detail_shows_question(self):
        response = self.client.get(f"/polls/{self.question.id}/")
        self.assertContains(response, "Is sliced Django enough?")
        self.assertContains(response, "Yes")

    def test_vote_increments_choice(self):
        response = self.client.post(
            f"/polls/{self.question.id}/vote/",
            {"choice": self.choice.id},
        )
        self.assertRedirects(response, f"/polls/{self.question.id}/")
        self.choice.refresh_from_db()
        self.assertEqual(self.choice.votes, 1)
