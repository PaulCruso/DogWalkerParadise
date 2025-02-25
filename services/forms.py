from django import forms
from .models import Appointment, UserProfile, Comment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'dog_type', 'other_dog_type', 'dog_size', 'dog_age', 'dog_number',
            'special_requirement', 'appointment_date', 'duration', 'location'
        ]
        widgets = {
            'appointment_date': forms.TextInput(attrs={'placeholder': 'Select Date', 'class': 'datepicker'}),
            'location': forms.TextInput(attrs={'id': 'autocomplete', 'placeholder': 'Enter a location', 'class': 'location-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        dog_type = cleaned_data.get('dog_type')
        other_dog_type = cleaned_data.get('other_dog_type')

        if dog_type == 'Other' and not other_dog_type:
            self.add_error('other_dog_type', 'Please specify the dog type.')

        return cleaned_data

    def clean_location(self):
        location = self.cleaned_data.get('location')
        if not location:
            raise forms.ValidationError("Location is required.")
        return location

    def clean_dog_walker(self):
        dog_walker = self.cleaned_data.get('dog_walker')
        if dog_walker and not dog_walker.is_active:
            raise forms.ValidationError("The selected dog walker is not active.")
        return dog_walker

    def clean_status(self):
        status = self.cleaned_data.get('status')
        valid_statuses = ['Scheduled', 'Completed', 'Started', 'Cancelled', 'Inprogress']
        if status not in valid_statuses:
            raise forms.ValidationError(f"Invalid status: {status}.")
        return status
    
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar', 'about']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        
class RatingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }