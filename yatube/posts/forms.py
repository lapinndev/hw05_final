from django import forms
from .models import Post, Group, Comment, Follow


class PostForm(forms.ModelForm):
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='Группа',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control'})
        }


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ('user', 'author')
