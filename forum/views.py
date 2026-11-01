import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from Dashboard.models import notify

from .forms import AnswerForm, QuestionForm
from .models import Answer, Question


class QuestionListView(ListView):
    model = Question
    template_name = 'forum/question_list.html'
    context_object_name = 'questions'
    paginate_by = 10

    def get_queryset(self):
        qs = Question.objects.select_related('author').annotate(answer_count=Count('answers')).order_by('-created_at')
        q = self.request.GET.get('q', '').strip()
        tag = self.request.GET.get('tag', '').strip()
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        if tag:
            qs = qs.filter(tags__icontains=tag)
        if self.request.GET.get('filter') == 'unanswered':
            qs = qs.filter(answer_count=0)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['tag'] = self.request.GET.get('tag', '')
        ctx['current_filter'] = self.request.GET.get('filter', '')
        tags = {}
        for value in Question.objects.exclude(tags='').values_list('tags', flat=True):
            for t in value.replace(',', ' ').split():
                t = t.lstrip('#').lower()
                tags[t] = tags.get(t, 0) + 1
        ctx['popular_tags'] = sorted(tags.items(), key=lambda x: -x[1])[:12]
        ctx['total_questions'] = Question.objects.count()
        ctx['total_answers'] = Answer.objects.count()
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        return ctx


def question_detail(request, pk):
    question = get_object_or_404(Question.objects.select_related('author'), pk=pk)
    answers = question.answers.select_related('author').prefetch_related('likes', 'dislikes').order_by(
        '-is_accepted', 'created_at')

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()
            if question.author_id != request.user.id:
                notify(question.author,
                       _("%(user)s ответил на ваш вопрос «%(title)s»") % {
                           'user': request.user.username, 'title': question.title},
                       reverse('question_detail', args=[question.pk]))
            messages.success(request, _("Ваш ответ опубликован."))
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
    form_class = QuestionForm
    template_name = 'forum/question_form.html'
    success_url = reverse_lazy('question_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, _("Вопрос опубликован!"))
        return super().form_valid(form)


@require_POST
@login_required
def accept_answer(request, pk):
    answer = get_object_or_404(Answer, pk=pk)
    if request.user == answer.question.author:
        answer.question.answers.update(is_accepted=False)
        answer.is_accepted = True
        answer.save(update_fields=['is_accepted'])
    return redirect('question_detail', pk=answer.question.pk)


@login_required
@require_POST
def like_answer(request, pk, action=None):
    answer = get_object_or_404(Answer, pk=pk)
    if action is None:
        try:
            action = json.loads(request.body or '{}').get('action', 'like')
        except (ValueError, AttributeError):
            action = request.POST.get('action', 'like')

    user = request.user
    if action == 'dislike':
        if answer.dislikes.filter(id=user.id).exists():
            answer.dislikes.remove(user)
        else:
            answer.dislikes.add(user)
            answer.likes.remove(user)
    else:
        if answer.likes.filter(id=user.id).exists():
            answer.likes.remove(user)
        else:
            answer.likes.add(user)
            answer.dislikes.remove(user)

    return JsonResponse({
        'likes_count': answer.likes.count(),
        'dislikes_count': answer.dislikes.count(),
        'liked': answer.likes.filter(id=user.id).exists(),
        'disliked': answer.dislikes.filter(id=user.id).exists(),
        'success': True,
    })


@login_required
@require_POST
def dislike_answer(request, pk):
    return like_answer(request, pk, action='dislike')


@require_POST
@login_required
def delete_question(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.user == question.author or request.user.is_superuser:
        question.delete()
        messages.info(request, _("Вопрос удалён."))
    return redirect('question_list')
