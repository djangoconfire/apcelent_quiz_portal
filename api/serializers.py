from rest_framework import serializers
from quiz.models import Profile,Quiz,QuestionPaper,AnswerPaper,Question,Answer

class ProfileSerializer(serializers.ModelSerializer):
	class Meta:
		model=Profile
		fields=['user','roll_number','institute','department','is_admin']



class QuizSerializer(serializers.ModelSerializer):
	class Meta:
		model=Quiz
		fields = '__all__'



class QuestionSerializer(serializers.ModelSerializer):
	class Meta:
		model=Question
		fields = '__all__'



class AnswerSerializer(serializers.ModelSerializer):
	class Meta:
		model=Answer
		fields = '__all__'

class QuestionPaperSerializer(serializers.ModelSerializer):
	class Meta:
		model=QuestionPaper
		fields = '__all__'		


class AnswerPaperSerializer(serializers.ModelSerializer):
	class Meta:
		model=AnswerPaper
		fields = '__all__'	



