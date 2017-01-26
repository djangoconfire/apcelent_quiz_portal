from django.shortcuts import render
from forms import UserRegisterForm, UserLoginForm,QuestionForm,QuizForm
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, render,redirect,get_object_or_404
from django.template import RequestContext
from models import Quiz, Question, QuestionPaper
from models import Profile, Answer, AnswerPaper, User
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import Http404
import random
import string
import os
import stat
from os.path import dirname, pardir, abspath, join, exists
import datetime
import collections
from itertools import chain
import json
from django.db.models import Sum
import datetime
from django.utils import timezone
now = timezone.now()

def is_admin(user1):
    s=Profile.objects.get(user=user1)
    
    if s.is_teacher==True:
        return True
    else:
        return False    

def user_register(request):
	user = request.user
	ci = RequestContext(request)
	if  user.is_authenticated() and user.is_active:
		return redirect("/quizzes/")
	if request.method == "POST":
		form = UserRegisterForm(request.POST)
		if form.is_valid():
			data = form.cleaned_data
			u_name, pwd = form.save()
			new_user = authenticate(username=u_name, password=pwd)
			login(request, new_user)
			return redirect("/home/")
		else:
			return render_to_response('register.html', {'form': form},
											context_instance=ci)
	else:
		form = UserRegisterForm()
		return render_to_response('register.html', {'form': form},
											context_instance=ci)
def home(request):
    ci = RequestContext(request)
    form = UserLoginForm(request.POST or None)
    if request.POST and form.is_valid():
        user = form.login(request)
        if user:
            login(request, user)
            u=request.user
            val=is_admin(u)
            if val==True:
                return redirect("/manage/")# Redirect to a success page.
            else:
                return redirect("/quizzes/")# Redirect to a success page.
    else:
        return render(request, 'home.html', {'form': form },context_instance=ci)

@login_required
def quizlist_user(request):
    """Show All Quizzes that is available to logged-in user."""
    user = request.user
    avail_quizzes = list(QuestionPaper.objects.filter(quiz__active=True))
    user_answerpapers = AnswerPaper.objects.filter(user=user)
    enabled_quizzes = []
    disabled_quizzes = []
    unexpired_quizzes = []
    for paper in avail_quizzes:
        quiz_disable_time = paper.quiz.end_date_time
        quiz_enable_time = paper.quiz.start_date_time 
        if quiz_enable_time <= now <= quiz_disable_time:
            unexpired_quizzes.append(paper)
    quizzes_taken = None if user_answerpapers.count() == 0 else user_answerpapers
    context = {
                'quizzes': avail_quizzes,
                'user': user,
                'quizzes_taken': quizzes_taken,
                'unexpired_quizzes': unexpired_quizzes
            }
    return render_to_response("quizzes_user.html", context)

def validate_answer(user, user_answer, question, json_data=None):
    """
        Checks whether the answer submitted by the user is right or wrong.
    """

    result = {'success': True, 'error': 'Incorrect answer'}
    correct = False

    if user_answer is not None:
        if question.type == 'mcq':
            if user_answer.strip() == question.test.strip():
                correct = True
                message = 'Correct answer'
        elif question.type == 'mcc':
            answers = set(question.test.splitlines())
            if set(user_answer) == answers:
                correct = True
                message = 'Correct answer'
    return correct, result
                
def _save_skipped_answer(old_skipped, user_answer, paper, question):
    
    if old_skipped:
        skipped_answer = old_skipped[0]
        skipped_answer.answer=user_answer
        skipped_answer.save()
    else:
        skipped_answer = Answer(question=question, answer=user_answer,
            correct=False, skipped=True)
        skipped_answer.save()
        paper.answers.add(skipped_answer)

def _check_previous_attempt(attempted_papers, already_attempted, attempt_number):
    next_attempt = False if already_attempted == attempt_number else True
    if already_attempted == 0:
        return False, None, next_attempt
    else:
        previous_attempt = attempted_papers[already_attempted-1]
        previous_attempt_day = previous_attempt.start_time
        today = datetime.datetime.today()
        if previous_attempt.status == 'inprogress':
            end_time = previous_attempt.end_time
            quiz_time = previous_attempt.question_paper.quiz.duration*60
        else:
            return False, previous_attempt, next_attempt
        
@login_required
def intro(request, questionpaper_id):
    """Show introduction page before quiz starts"""
    user = request.user
    ci = RequestContext(request)
    quest_paper = QuestionPaper.objects.get(id=questionpaper_id)
    attempt_number = quest_paper.quiz.attempts_allowed
    time_lag = quest_paper.quiz.time_between_attempts
    quiz_enable_time = quest_paper.quiz.start_date_time
    quiz_disable_time = quest_paper.quiz.end_date_time
    quiz_expired = False if quiz_enable_time <= now \
                                <= quiz_disable_time else True
    attempted_papers = AnswerPaper.objects.filter(question_paper=quest_paper,
            user=user)
    already_attempted = attempted_papers.count()
    inprogress, previous_attempt, next_attempt = _check_previous_attempt(attempted_papers,
                                                                            already_attempted,
                                                                            attempt_number)
    if previous_attempt:
        if inprogress:
            return show_question(request,
                    previous_attempt.current_question(),
                    previous_attempt.attempt_number,
                    previous_attempt.question_paper.id)
        days_after_attempt = (datetime.datetime.today() - \
                previous_attempt.start_time).days

        if next_attempt:
            if days_after_attempt >= time_lag:
                context = {'user': user,
                            'paper_id': questionpaper_id,
                            'attempt_num': already_attempted + 1,
                            'enable_quiz_time': quiz_enable_time,
                            'disable_quiz_time': quiz_disable_time,
                            'quiz_expired': quiz_expired
                        }
                return render_to_response('intro.html', context,
                                             context_instance=ci)
        else:
            return redirect("/quizzes/")

    else:
        context = {'user': user,
                    'paper_id': questionpaper_id,
                    'attempt_num': already_attempted + 1,
                    'enable_quiz_time': quiz_enable_time,
                    'disable_quiz_time': quiz_disable_time,
                    'quiz_expired': quiz_expired
                }
        return render_to_response('intro.html', context,
                                     context_instance=ci)
        
@login_required
def complete(request, reason=None, attempt_num=None, questionpaper_id=None):
    """Show a page to inform user that the quiz has been compeleted."""

    user = request.user
    if questionpaper_id is None:
        logout(request)
        message = reason or "You are successfully logged out."
        context = {'message': message}
        return render_to_response('complete.html', context)
    
    else:
    
        unattempted_questions, submitted_questions = get_question_labels(request,
                                                     attempt_num, questionpaper_id)
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
        paper = AnswerPaper.objects.get(user=user, question_paper=q_paper,
                attempt_number=attempt_num)
        paper.update_marks_obtained()
        paper.update_percent()
        paper.update_passed()
        paper.end_time = datetime.datetime.now()
        paper.update_status()
        paper.save()
        obt_marks = paper.marks_obtained
        tot_marks = paper.question_paper.total_marks
        if obt_marks == paper.question_paper.total_marks:
            context = {'message': "Hurray ! You did an excellent job.you answered all the questions correctly.You have been logged out successfully,Thank You !",
                       'unattempted': unattempted_questions,
                       'submitted': submitted_questions}
            return render_to_response('complete.html', context)
        else:
            message = reason or "You are successfully logged out"
            context = {'message':  message,
                         'unattempted': unattempted_questions,
                         'submitted': submitted_questions}
            return render_to_response('complete.html', context)
    no = False
    message = reason or 'The quiz has been completed. Thank you.'
    if user.groups.filter(name='moderator').count() > 0:
        message = 'You are successfully Logged out.'
    if request.method == 'POST' and 'no' in request.POST:
        no = True
    if not no:
        # Logout the user and quit with the message given.
        answer_paper = AnswerPaper.objects.get(id=answerpaper_id)
        answer_paper.end_time = datetime.datetime.now()
        answer_paper.save()
        return redirect('/quizzes/')
    else:
        return redirect('/home/')        
@login_required
def results_user(request):
    """Show list of Results of Quizzes that is taken by logged-in user."""
    user = request.user
    papers = AnswerPaper.objects.filter(user=user)
    quiz_marks = []
    for paper in papers:
        marks_obtained = paper.marks_obtained
        max_marks = paper.question_paper.total_marks
        if marks_obtained==None:
            percentage=0.0;
        else:
            percentage = round((marks_obtained/max_marks)*100, 2)
        temp = paper.question_paper.quiz.description, marks_obtained,\
               max_marks, percentage
        quiz_marks.append(temp)
    context = {'papers': quiz_marks}
    return render_to_response("results_user.html", context)

@login_required
def start(request, attempt_num=None, questionpaper_id=None):
    """Check the user cedentials and if any quiz is available,
    start the exam."""
    user = request.user
    if questionpaper_id is None:
        return redirect('/quizzes/')
    try:
        questionpaper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        msg = 'Quiz not found, please contact your '\
            'instructor/administrator. Please login again thereafter.'
        return complete(request, msg, attempt_num, questionpaper_id)
    try:
        old_paper = AnswerPaper.objects.get(
            question_paper=questionpaper, user=user, attempt_number=attempt_num)
        q = old_paper.current_question()
        return show_question(request, q, attempt_num, questionpaper_id)
    except AnswerPaper.DoesNotExist:
        ip = request.META['REMOTE_ADDR']
        key = gen_key(10)
        new_paper = questionpaper.make_answerpaper(user, ip, attempt_num)
        # Make user directory.
        #user_dir = get_user_dir(user)
        return start(request, attempt_num, questionpaper_id)           
        
@login_required
def prof_manage(request):
    """Take credentials of the user with professor/moderator
rights/permissions and log in."""
    user = request.user
    if user.is_authenticated() and is_admin(user):
        question_papers = QuestionPaper.objects.all()
        users_per_paper = []
        for paper in question_papers:
            answer_papers = AnswerPaper.objects.filter(question_paper=paper)
            users_passed = AnswerPaper.objects.filter(question_paper=paper,
                    passed=True).count()
            users_failed = AnswerPaper.objects.filter(question_paper=paper,
                    passed=False).count()
            temp = paper, answer_papers, users_passed, users_failed
            users_per_paper.append(temp)
        context = {'user': user, 'users_per_paper': users_per_paper}
        return render_to_response('manage.html', context)
    return redirect('/home/')
    
       
@login_required
def add_quiz(request, quiz_id=None):
    """To add a new quiz in the database.
    Create a new quiz and store it."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_admin(user):
        raise Http404('You are not allowed to view this page!')
    if request.method == "POST":
        form = QuizForm(request.POST)
        if form.is_valid():
            if quiz_id is None:
                form.save()
                return redirect("/manage/")
                # to be changed later
                #return redirect("/manage/designquestionpaper")
            else:
                d = Quiz.objects.get(id=quiz_id)
                sd = datetime.datetime.strptime(form['start_date'].data, '%Y-%m-%d').date()
                st = datetime.datetime.strptime(form['start_time'].data, "%H:%M:%S").time()
                ed = datetime.datetime.strptime(form['end_date'].data, '%Y-%m-%d').date()
                et = datetime.datetime.strptime(form['end_time'].data, "%H:%M:%S").time()
                d.start_date_time = datetime.datetime.combine(sd, st)
                d.end_date_time = datetime.datetime.combine(ed, et)
                d.duration = form['duration'].data
                d.active = form['active'].data
                d.description = form['description'].data
                d.pass_criteria = form['pass_criteria'].data
                d.attempts_allowed = form['attempts_allowed'].data
                d.time_between_attempts = form['time_between_attempts'].data
                d.save()
                #quiz = Quiz.objects.get(id=quiz_id)
                return redirect("/manage/")
                # to be changed later
                #return redirect("/manage/showquiz")
        else:
            return render_to_response('add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
    else:
        if quiz_id is None:
            form = QuizForm()
            return render_to_response('add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)
        else:
            d = Quiz.objects.get(id=quiz_id)
            form = QuizForm()
            form.initial['start_date'] = d.start_date_time.date()
            form.initial['start_time'] = d.start_date_time.time()
            form.initial['end_date'] = d.end_date_time.date()
            form.initial['end_time'] = d.end_date_time.time()
            form.initial['duration'] = d.duration
            form.initial['description'] = d.description
            form.initial['active'] = d.active
            form.initial['pass_criteria'] = d.pass_criteria
            form.initial['attempts_allowed'] = d.attempts_allowed
            form.initial['time_between_attempts'] = d.time_between_attempts
            return render_to_response('add_quiz.html',
                                         {'form': form},
                                         context_instance=ci)

@login_required
def edit_quiz(request):
    user = request.user
    if not user.is_authenticated() or not is_admin(user):
        raise Http404('You are not allowed to view this page!')
    quiz_list = request.POST.getlist('quizzes')
    start_date = request.POST.getlist('start_date')
    start_time = request.POST.getlist('start_time')
    end_date = request.POST.getlist('end_date')
    end_time = request.POST.getlist('end_time')
    duration = request.POST.getlist('duration')
    active = request.POST.getlist('active')
    description = request.POST.getlist('description')
    pass_criteria = request.POST.getlist('pass_criteria')
    for j, quiz_id in enumerate(quiz_list):
        quiz = Quiz.objects.get(id=quiz_id)
        quiz.start_date_time = datetime.datetime.combine(start_date[j],
                                                    start_time[j])
        quiz.end_date_time = datetime.datetime.combine(end_date[j],
                                                    end_time[j])
        quiz.duration = duration[j]
        quiz.active = active[j]
        quiz.description = description[j]
        quiz.pass_criteria = pass_criteria[j]
        quiz.save()
    return redirect("/manage/showquiz/")

@login_required
def show_all_quiz(request):
    """Generates a list of all the quizzes
    that are currently in the database."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_admin(user):
        raise Http404('You are not allowed to view this page !')

    if request.method == 'POST' and request.POST.get('delete') == 'delete':
        data = request.POST.getlist('quiz')
        if data is None:
            quizzes = Quiz.objects.all()
            context = {'papers': [],
                       'quiz': None,
                       'quizzes': quizzes}
            return render_to_response('show_quiz.html', context,
                                         context_instance=ci)
        else:
            for i in data:
                quiz = Quiz.objects.get(id=i).delete()
            quizzes = Quiz.objects.all()
            context = {'papers': [],
                       'quiz': None,
                       'quizzes': quizzes}
            return render_to_response('show_quiz.html', context,
                                         context_instance=ci)

    elif request.method == 'POST' and request.POST.get('edit') == 'edit':
        data = request.POST.getlist('quiz')
        forms = []
        for j in data:
            d = Quiz.objects.get(id=j)
            form = QuizForm()
            form.initial['start_date'] = d.start_date_time.date()
            form.initial['start_time'] = d.start_date_time.time()
            form.initial['end_date'] = d.end_date_time.date()
            form.initial['end_time'] = d.end_date_time.time()
            form.initial['duration'] = d.duration
            form.initial['active'] = d.active
            form.initial['description'] = d.description
            forms.append(form)
        return render_to_response('edit_quiz.html',
                                     {'forms': forms, 'data': data},
                                     context_instance=ci)
    else:
        quizzes = Quiz.objects.all()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': quizzes}
        return render_to_response('show_quiz.html', context,
                                     context_instance=ci)
@login_required
def get_user_data(username):
    """For a given username, this returns a dictionary of important data
    related to the user including all the user's answers submitted.
    """
    user = User.objects.get(username=username)
    papers = AnswerPaper.objects.filter(user=user)

    data = {}
    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        # Admin user may have a paper by accident but no profile.
        profile = None
    data['user'] = user
    data['profile'] = profile
    data['papers'] = papers
    return data
    

@login_required
def show_all_users(request):
    user = request.user
    if not user.is_authenticated() or not is_admin(user):
        raise Http404('You are not allowed to view this page !')
    user = User.objects.filter(username__contains="")
    questionpaper = AnswerPaper.objects.all()
    context = {'question': questionpaper}
    return render_to_response('showusers.html', context,
                                 context_instance=RequestContext(request))
@login_required
def monitor(request, questionpaper_id=None):
    """Monitor the progress of the papers taken so far."""

    user = request.user
    ci = RequestContext(request)
    if not user.is_authenticated() or not is_admin(user):
        raise Http404('You are not allowed to view this page!')

    if questionpaper_id is None:
        q_paper = QuestionPaper.objects.all()
        context = {'papers': [],
                   'quiz': None,
                   'quizzes': q_paper}
        return render_to_response('monitor.html', context,
                                     context_instance=ci)
    # quiz_id is not None.
    try:
        q_paper = QuestionPaper.objects.get(id=questionpaper_id)
    except QuestionPaper.DoesNotExist:
        papers = []
        q_paper = None
    else:
        papers = AnswerPaper.objects.filter(question_paper=q_paper).annotate(
            total=Sum('answers__marks')).order_by('-total')

    context = {'papers': papers, 'quiz': q_paper, 'quizzes': None}
    return render_to_response('monitor.html', context,
                                 context_instance=ci)                                 

                                