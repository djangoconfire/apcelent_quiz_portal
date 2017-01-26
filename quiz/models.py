from django.db import models
from django.contrib.auth.models import User
import datetime
import json
from random import sample, shuffle
from itertools import islice, cycle
import random
from django.utils import timezone
now = timezone.now()
question_types = (
        ("mcq", "Multiple Choice"),
        ("subj_ques", "Subjective Question")
    )
attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = ((j, j) for j in range(401))

test_status = (
                ('inprogress', 'Inprogress'),
                ('completed', 'Completed'),
              )


class Profile(models.Model):
    """Profile for a user to store roll number and other details."""
    user            = models.OneToOneField(User)
    roll_number     = models.CharField(max_length=20)
    institute       = models.CharField(max_length=128)
    department      = models.CharField(max_length=64)
    is_admin        = models.BooleanField(default=False)


class Question(models.Model):
    """Question for a quiz."""

    # A one-line summary of the question.
    summary = models.CharField(max_length=256)

    # The question text, should be valid HTML.
    description = models.TextField()

    # Number of points for the question.
    points = models.FloatField(default=1.0)

    # Answer for MCQs.
    test = models.TextField(blank=True)
    # Any multiple choice options. Place one option per line.
    options = models.TextField(blank=True)
    # The type of question.
    type = models.CharField(max_length=24, choices=question_types)

    # Is this question active or not. If it is inactive it will not be used
    # when creating a QuestionPaper.
    active = models.BooleanField(default=True)
    def __unicode__(self):
        return self.summary

class Answer(models.Model):
    """Answers submitted by the users."""

    # The question for which user answers.
    question = models.ForeignKey(Question)

    # The answer submitted by the user.
    answer = models.TextField(null=True, blank=True)

    # Error message when auto-checking the answer.
    error = models.TextField()

    # Marks obtained for the answer. This can be changed by the teacher if the
    # grading is manual.
    marks = models.FloatField(default=0.0)

    # Is the answer correct.
    correct = models.BooleanField(default=False)

    # Whether skipped or not.
    skipped = models.BooleanField(default=False)

    def __unicode__(self):
        return self.answer


class Quiz(models.Model):
    """A quiz that students will participate in. One can think of this
    as the "examination" event.
    """

    # The start date of the quiz.
    start_date_time = models.DateTimeField("Start Date and Time of the quiz",
                                        default=datetime.datetime.now(),
                                        null=True)

    # The end date and time of the quiz
    end_date_time = models.DateTimeField("End Date and Time of the quiz",
                                        default=datetime.datetime(2199, 1, 1, 0, 0, 0, 0),
                                        null=True)

    # This is always in minutes.
    duration = models.IntegerField("Duration of quiz in minutes", default=20)

    # Is the quiz active. The admin should deactivate the quiz once it is
    # complete.
    active = models.BooleanField(default=True)

    # Description of quiz.
    description = models.CharField(max_length=256)

    # Mininum passing percentage condition.
    pass_criteria = models.FloatField("Passing percentage", default=40)

    # Number of attempts for the quiz
    attempts_allowed = models.IntegerField(default=1, choices=attempts)

    time_between_attempts = models.IntegerField("Number of Days",\
            choices=days_between_attempts)

    class Meta:
        verbose_name_plural = "Quizzes"

    def __unicode__(self):
        desc = self.description or 'Quiz'
        return '%s: on %s for %d minutes' % (desc, self.start_date_time,
                                             self.duration)


class QuestionPaper(models.Model):
    """Question paper stores the detail of the questions."""

    # Question paper belongs to a particular quiz.
    quiz = models.ForeignKey(Quiz)

    # Questions that will be mandatory in the quiz.
    fixed_questions = models.ManyToManyField(Question)

    # Option to shuffle questions, each time a new question paper is created.
    shuffle_questions = models.BooleanField(default=False)

    # Total marks for the question paper.
    total_marks = models.FloatField()

    def update_total_marks(self):
        """ Updates the total marks for the Question Paper"""
        marks = 0.0
        questions = self.fixed_questions.all()
        for question in questions:
            marks += question.points
        for question_set in self.random_questions.all():
            marks += question_set.marks * question_set.num_questions
        self.total_marks = marks

    def _get_questions_for_answerpaper(self):
        """ Returns fixed and random questions for the answer paper"""
        questions = []
        questions = list(self.fixed_questions.all())
        for question_set in self.random_questions.all():
            questions += question_set.get_random_questions()
        return questions

    def make_answerpaper(self, user, ip, attempt_num):
        """Creates an  answer paper for the user to attempt the quiz"""
        ans_paper = AnswerPaper(user=user, user_ip=ip, attempt_number=attempt_num)
        ans_paper.start_time = datetime.datetime.now()
        ans_paper.end_time = ans_paper.start_time \
                             + datetime.timedelta(minutes=self.quiz.duration)
        ans_paper.question_paper = self
        questions = self._get_questions_for_answerpaper()
        question_ids = [str(x.id) for x in questions]
        if self.shuffle_questions:
            shuffle(question_ids)
        ans_paper.questions = "|".join(question_ids)
        ans_paper.save()
        return ans_paper


class AnswerPaper(models.Model):
    """A answer paper for a student -- one per student typically.
    """
    # The user taking this question paper.
    user = models.ForeignKey(User)

    # All questions that remain to be attempted for a particular Student
    # (a list of ids separated by '|')
    questions = models.CharField(max_length=128)

    # The Quiz to which this question paper is attached to.
    question_paper = models.ForeignKey(QuestionPaper)

    # The attempt number for the question paper.
    attempt_number = models.IntegerField()

    # The time when this paper was started by the user.
    start_time = models.DateTimeField()

    # The time when this paper was ended by the user.
    end_time = models.DateTimeField()

    # User's IP which is logged.
    user_ip = models.CharField(max_length=15)

    # The questions successfully answered (a list of ids separated by '|')
    questions_answered = models.CharField(max_length=128)

    # All the submitted answers.
    answers = models.ManyToManyField(Answer)

    # Teacher comments on the question paper.
    comments = models.TextField()

    # Total marks earned by the student in this paper.
    marks_obtained = models.FloatField(null=True, default=None)

    # Marks percent scored by the user
    percent = models.FloatField(null=True, default=None)

    # Result of the quiz, True if student passes the exam.
    passed = models.NullBooleanField()

    # Status of the quiz attempt
    status = models.CharField(max_length=20, choices=test_status,\
            default='inprogress')

    def current_question(self):
        """Returns the current active question to display."""
        qu = self.get_unanswered_questions()
        if len(qu) > 0:
            return qu[0]
        else:
            return ''

    def questions_left(self):
        """Returns the number of questions left."""
        qu = self.get_unanswered_questions()
        return len(qu)

    def get_unanswered_questions(self):
        """Returns the list of unanswered questions."""
        qa = self.questions_answered.split('|')
        qs = self.questions.split('|')
        qu = [q for q in qs if q not in qa]
        return qu

    def completed_question(self, question_id):
        """
            Adds the completed question to the list of answered 
            questions and returns the next question.
        """
        qa = self.questions_answered
        if len(qa) > 0:
            self.questions_answered = '|'.join([qa, str(question_id)])
        else:
            self.questions_answered = str(question_id)
        self.save()

        return self.skip(question_id)

    def skip(self, question_id):
        """
            Skips the current question and returns the next sequentially
             available question.
        """
        qu = self.get_unanswered_questions()
        qs = self.questions.split('|')

        if len(qu) == 0:
            return ''

        try:
            q_index = qs.index(unicode(question_id))
        except ValueError:
            return qs[0]

        start = q_index + 1
        stop = q_index + 1 + len(qs)
        q_list = islice(cycle(qs), start, stop)
        for next_q in q_list:
            if next_q in qu:
                return next_q

        return qs[0]

    def time_left(self):
        """Return the time remaining for the user in seconds."""
        dt = datetime.datetime.now() - self.start_time.replace(tzinfo=None)
        try:
            secs = dt.total_seconds()
        except AttributeError:
            # total_seconds is new in Python 2.7. :(
            secs = dt.seconds + dt.days*24*3600
        total = self.question_paper.quiz.duration*60.0
        remain = max(total - secs, 0)
        return int(remain)

    def get_answered_str(self):
        """Returns the answered questions, sorted and as a nice string."""
        qa = self.questions_answered.split('|')
        answered = ', '.join(sorted(qa))
        return answered if answered else 'None'

    def update_marks_obtained(self):
        """Updates the total marks earned by student for this paper."""
        marks = sum([x.marks for x in self.answers.filter(marks__gt=0.0)])
        self.marks_obtained = marks

    def update_percent(self):
        """Updates the percent gained by the student for this paper."""
        total_marks = self.question_paper.total_marks
        if self.marks_obtained is not None:
            percent = self.marks_obtained/self.question_paper.total_marks*100
            self.percent = round(percent, 2)

    def update_passed(self):
        """
            Checks whether student passed or failed, as per the quiz
            passing criteria.
        """
        if self.percent is not None:
            if self.percent >= self.question_paper.quiz.pass_criteria:
                self.passed = True
            else:
                self.passed = False

    def update_status(self):
        """ Sets status to completed """
        self.status = 'completed'

    def get_question_answers(self):
        """
            Return a dictionary with keys as questions and a list of the
            corresponding answers.
        """
        q_a = {}
        for answer in self.answers.all():
            question = answer.question
            if question in q_a:
                q_a[question].append(answer)
            else:
                q_a[question] = [answer]
        return q_a

    def __unicode__(self):
        u = self.user
        return u'Question paper for {0} {1}'.format(u.first_name, u.last_name)