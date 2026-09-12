from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from .models import Choice, Question


def index(request):
    latest = Question.objects.order_by("-pub_date")[:5]
    return render(request, "polls/index.html", {"latest_question_list": latest})


def detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    return render(request, "polls/detail.html", {"question": question})


def vote(request, pk):
    question = get_object_or_404(Question, pk=pk)
    try:
        selected = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request,
            "polls/detail.html",
            {"question": question, "error_message": "You didn't select a choice."},
        )
    selected.votes += 1
    selected.save()
    return HttpResponseRedirect(reverse("detail", args=(question.id,)))
