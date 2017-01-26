from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from models import Profile
from models import  Quiz, Question
from django.forms.models import inlineformset_factory
import datetime
#from string import letters, punctuation, digits
import datetime
from string import ascii_letters, punctuation, digits
UNAME_CHARS = ascii_letters + "._" + digits
PWD_CHARS = ascii_letters + punctuation + digits
attempts = [(i, i) for i in range(1, 6)]
attempts.append((-1, 'Infinite'))
days_between_attempts = ((j, j) for j in range(401))

question_types = (
    ("select", "Select Question Type"),
    ("mcq", "Multiple Choice"),
    ("subj_ques", "Subjective Question")    
    )
class UserRegisterForm(forms.Form):
    username            = forms.CharField(max_length=30, help_text='Letters, digits,period and underscores only.')
    email               = forms.EmailField()
    password            = forms.CharField(max_length=30, widget=forms.PasswordInput())
    confirm_password    = forms.CharField\
                            (max_length=30, widget=forms.PasswordInput())
    first_name          = forms.CharField(max_length=30)
    last_name           = forms.CharField(max_length=30)
    roll_number         = forms.CharField\
                            (max_length=30, help_text="Use a dummy if you don't have one.")
    institute           = forms.CharField\
                            (max_length=128, help_text='Institute/Organization')
    department          = forms.CharField\
                            (max_length=64, help_text='Department you work/study at')
    isTeacher           = forms.BooleanField(required=False)            
    def clean_username(self):
        u_name = self.cleaned_data["username"]
        if u_name.strip(UNAME_CHARS):
            msg = "Only letters, digits, period and underscore characters are"\
                  " allowed in username"
            raise forms.ValidationError(msg)
        try:
            User.objects.get(username__exact=u_name)
            raise forms.ValidationError("Username already exists.")
        except User.DoesNotExist:
            return u_name
    def clean_password(self):
        pwd = self.cleaned_data['password']
        if pwd.strip(PWD_CHARS):
            raise forms.ValidationError("Only letters, digits and punctuation are allowed in password")
        return pwd
    def clean_confirm_password(self):
        c_pwd = self.cleaned_data['confirm_password']
        pwd = self.data['password']
        if c_pwd != pwd:
            raise forms.ValidationError("Passwords do not match")
        return c_pwd
    def save(self):
        u_name = self.cleaned_data["username"]
        u_name = u_name.lower()
        pwd = self.cleaned_data["password"]
        email = self.cleaned_data['email'] 
        new_user = User.objects.create_user(u_name, email, pwd)
        new_user.first_name = self.cleaned_data["first_name"]
        new_user.last_name = self.cleaned_data["last_name"]
        new_user.save()
        cleaned_data = self.cleaned_data
        new_profile = Profile(user=new_user)
        new_profile.roll_number = cleaned_data["roll_number"]
        new_profile.institute = cleaned_data["institute"]
        new_profile.department = cleaned_data["department"]
        if cleaned_data["isTeacher"]==True:
            new_profile.is_teacher=True
        new_profile.save()
        return u_name, pwd


class UserLoginForm(forms.Form):
    """Creates a form which will allow the user to log into the system."""

    username = forms.CharField(max_length=30)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput())

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if not user or not user.is_active:
            raise forms.ValidationError("Sorry, that login was invalid. Please try again.")
        return self.cleaned_data

    def login(self, request):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        return user    


class QuestionForm(forms.Form):
    """Creates a form to add or edit a Question.
    It has the related fields and functions required."""

    summary         = forms.CharField(widget=forms.Textarea\
                                        (attrs={'cols': 40, 'rows': 1}))
    description     = forms.CharField(widget=forms.Textarea\
                                            (attrs={'cols': 40, 'rows': 1}))
    points          = forms.FloatField()
    test            = forms.CharField(widget=forms.Textarea\
                                    (attrs={'cols': 40, 'rows': 1}), required=False)
    options         = forms.CharField(widget=forms.Textarea\
                              (attrs={'cols': 40, 'rows': 1}), required=False)
    type            = forms.CharField(max_length=8, widget=forms.Select\
                           (choices=question_types))
    active          = forms.BooleanField(required=False)

    def save(self):
        summary = self.cleaned_data.get("summary")
        description = self.cleaned_data.get("description")
        points = self.cleaned_data.get("points")
        test = self.cleaned_data.get("test")
        options = self.cleaned_data.get("options")
        type = self.cleaned_data.get("type")
        active = self.cleaned_data.get("active")

        new_question = Question()
        new_question.summary = summary
        new_question.description = description
        new_question.points = points
        new_question.test = test
        new_question.options = options
        new_question.type = type
        new_question.active = active
        new_question.save()
        return new_question    

class QuizForm(forms.Form):
    """Creates a form to add or edit a Quiz.
    It has the related fields and functions required."""
    start_date          = forms.DateField(initial=datetime.date.today(), required=False)
    start_time          = forms.TimeField(initial=datetime.datetime.now().time(), required=False)
    end_date            = forms.DateField(initial=datetime.date(2199, 1, 1), required=False)
    end_time            = forms.TimeField(initial=datetime.time(0, 0, 0, 0), required=False)
    duration            = forms.IntegerField(help_text='Will be taken in minutes')
    active              = forms.BooleanField(required=False)
    description         = forms.CharField(max_length=256, widget=forms.Textarea\
                                  (attrs={'cols': 20, 'rows': 1}))
    pass_criteria       = forms.FloatField(initial=40,
                                     help_text='Will be taken as percentage')
    attempts_allowed    = forms.IntegerField(widget=forms.Select(choices=attempts))
    time_between_attempts = forms.IntegerField\
            (widget=forms.Select(choices=days_between_attempts),
                    help_text='Will be in days')

    def save(self):
        start_date = self.cleaned_data["start_date"]
        start_time = self.cleaned_data["start_time"] 
        end_date = self.cleaned_data["end_date"]
        end_time = self.cleaned_data["end_time"] 
        duration = self.cleaned_data["duration"]
        active = self.cleaned_data['active']
        description = self.cleaned_data["description"]
        pass_criteria = self.cleaned_data["pass_criteria"]
        attempts_allowed = self.cleaned_data["attempts_allowed"]
        time_between_attempts = self.cleaned_data["time_between_attempts"]
        new_quiz = Quiz()
        new_quiz.start_date_time = datetime.datetime.combine(start_date,
                                                    start_time)
        new_quiz.end_date_time = datetime.datetime.combine(end_date,
                                                    end_time)
        new_quiz.duration = duration
        new_quiz.active = active
        new_quiz.description = description
        new_quiz.pass_criteria = pass_criteria
        new_quiz.attempts_allowed = attempts_allowed
        new_quiz.time_between_attempts = time_between_attempts
        new_quiz.save()      


