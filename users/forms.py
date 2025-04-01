# from django import forms
# from .models import CustomUser, Profile

# class UserRegisterForm(UserCreationForm):
#     # already has username and password fields
#     email = forms.EmailField(required=True) # adds email field
    
#     class Meta: # metadata about the model
#         model = CustomUser
#         fields = ['username', 'email']
    
#     def get_user(self): # passes user info 
#         username = self.cleaned_data.get('username')  
#         password = self.cleaned_data.get('password')
        
#         user = CustomUser.objects.get(username=username)  
#         if user.check_password(password): # validates info
#             return user
#         else:
#             return None   

# class UpdateUserForm(UserChangeForm):
#     password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False, help_text="Leave blank to keep current password")
#     confirm_password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)

#     class Meta:
#         model = CustomUser
#         fields = ['username', 'email', 'avatar', 'password']

#     def clean(self): # get data from form
#         cleaned_data = super().clean() 
#         password = cleaned_data.get("password")
#         confirm_password = cleaned_data.get("confirm_password")

#         if password: # check if password given
#             if password != confirm_password:
#                 raise forms.ValidationError("Passwords are different")
#         return cleaned_data
    
#     def save(self, commit=True):
#         user = super().save(commit=False)
#         password = self.cleaned_data.get("password")

#         if password:
#             user.set_password(password)

#         if commit:
#             user.save()
#         return user
    
# class UpdateProfileForm(forms.ModelForm):
#     bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))

#     class Meta:
#         model = Profile
#         fields = ['bio']