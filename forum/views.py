from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Question, Answer
from .forms import AnswerForm


class QuestionListView(ListView):
    model = Question
    template_name = 'forum/question_list.html'
    context_object_name = 'questions'


def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    answers = question.answers.all()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('login')

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()
            return redirect('question_detail', pk=question.pk)
    else:
        form = AnswerForm()

    return render(request, 'forum/question_detail.html', {
        'question': question,
        'answers': answers,
        'form': form,
    })


class QuestionCreateView(LoginRequiredMixin, CreateView):
    model = Question
    template_name = 'forum/question_form.html'
    fields = ['title', 'content', 'tags']
    success_url = reverse_lazy('question_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


def accept_answer(request, pk):
    answer = get_object_or_404(Answer, pk=pk)
    if request.user == answer.question.author:
        answer.question.answers.update(is_accepted=False)
        answer.is_accepted = True
        answer.save()

    return redirect('question_detail', pk=answer.question.pk)


@login_required
@require_POST
def like_answer(request, pk):
    answer = get_object_or_404(Answer, pk=pk)

    try:
        import json
        data = json.loads(request.body)
        action = data.get('action')
    except:
        action = request.POST.get('action', 'like')

    if action == 'like':
        if answer.likes.filter(id=request.user.id).exists():
            answer.likes.remove(request.user)
        else:
            answer.likes.add(request.user)
            answer.dislikes.remove(request.user)
    elif action == 'dislike':
        if answer.dislikes.filter(id=request.user.id).exists():
            answer.dislikes.remove(request.user)
        else:
            answer.dislikes.add(request.user)
            answer.likes.remove(request.user)

    return JsonResponse({
        'likes_count': answer.likes.count(),
        'dislikes_count': answer.dislikes.count(),
        'success': True
    })


@login_required
@require_POST
def dislike_answer(request, pk):
    request.POST = request.POST.copy()
    request.POST['action'] = 'dislike'
    return like_answer(request, pk)


@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.user == question.author:
        question.delete()
    return redirect('question_list')