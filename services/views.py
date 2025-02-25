from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Appointment, Comment, UserProfile, Notification
from .forms import AppointmentForm, ProfileForm, CommentForm, RatingForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.http import HttpResponse
import json
from datetime import timedelta
from . import models
from django.db.models import Q
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods


def login_view(request):
    if request.user.is_authenticated:
        return redirect('main')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('main')
            else:
                messages.error(request, 'Invalid username or password.')
        except Exception as e:
            messages.error(request, 'An error occurred during login.')
            
    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('main')
        
    if request.method == 'POST':
        firstname = request.POST.get('firstname', '').strip()
        lastname = request.POST.get('lastname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Basic validation
        if not all([firstname, lastname, username, email, password, confirm_password]):
            messages.error(request, 'All fields are required.')
            return render(request, 'register.html')
            
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'register.html')
            
        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'register.html')
                
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists.')
                return render(request, 'register.html')
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=firstname,
                last_name=lastname
            )
            
            login(request, authenticate(username=username, password=password))
            return redirect('main')
            
        except Exception as e:
            messages.error(request, 'An error occurred during registration.')
                
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def main_view(request):
    return render(request, 'main.html')

@login_required
def book_appointment(request):
    api_key = 'AIzaSyD0vhH-P6vHsEDErOAs01mkK02RqbjDB3E'
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.dog_owner = request.user  
            appointment.status = 'Scheduled'
            appointment.save()
            messages.success(request, 'Appointment confirmed successfully.')
            return redirect('existing_appointment')  
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AppointmentForm()

    return render(request, 'book_appointment.html', {'form': form, 'GOOGLE_PLACES_API_KEY': api_key})

@login_required
def help_walk(request):
    # Filter appointments based on the conditions
    appointments = models.Appointment.objects.filter(
        ~Q(dog_owner=request.user),  # Exclude appointments where the user is the dog owner
        status='Scheduled'  # Only show appointments with status 'Scheduled'
    ).order_by('appointment_date')

    # Serialize the data to pass to the template
    appointments_data = [
        {
            "id": appointment.id,
            "date": appointment.appointment_date.strftime('%b %d, %Y'),
            "time": f"{appointment.appointment_date.strftime('%I:%M %p')} ~ {(appointment.appointment_date + timedelta(minutes=int(appointment.duration))).strftime('%I:%M %p')}",
            "location": appointment.location,
            "dog_type": appointment.dog_type,
            "dog_size": appointment.dog_size,
        }
        for appointment in appointments
    ]
    context = {
        "appointments_json": json.dumps(appointments_data),
    }
    return render(request, "help_walk.html", context)

@login_required
def existing_appointment(request):
    return render(request, 'existing_appointment.html')

@login_required
def view_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    is_walker = request.user == appointment.dog_walker
    is_owner = request.user == appointment.dog_owner
    
    # Only allow access to owner and walker
    if not (is_walker or is_owner):
        return redirect('main')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if not is_walker:
            return JsonResponse({'error': 'Only dog walker can perform this action'}, status=403)
            
        if action == 'start':
            if appointment.status != 'Inprogress':
                return JsonResponse({'error': 'Invalid appointment status'}, status=400)
            appointment.status = 'Started'
            appointment.save()
            return JsonResponse({'success': True, 'status': 'Started'})
            
        elif action == 'finish':
            if appointment.status != 'Started':
                return JsonResponse({'error': 'Invalid appointment status'}, status=400)
            appointment.status = 'Completed'
            appointment.save()
            return JsonResponse({'success': True, 'status': 'Completed'})
    
    # Prepare appointment data for template
    appointment_data = {
        'id': appointment.id,
        'date': appointment.appointment_date.strftime('%b %d, %Y'),
        'time': appointment.appointment_date.strftime('%I:%M %p'),
        'duration': appointment.duration,
        'location': appointment.location,
        'status': appointment.status,
        'dog_type': appointment.dog_type,
        'dog_size': appointment.dog_size,
        'dog_age': appointment.dog_age,
        'dog_number': appointment.dog_number,
        'special_requirement': appointment.special_requirement or '',
        'dog_owner_username': appointment.dog_owner.username,
        'dog_walker_username': appointment.dog_walker.username if appointment.dog_walker else '',
    }

    context = {
        'appointment_data': json.dumps(appointment_data),
        'is_walker': json.dumps(is_walker),
    }
    return render(request, 'view_appointment.html', context)

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        if 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
            user_profile.save()
            avatar_url = user_profile.avatar.url if user_profile.avatar else '/static/images/default_profile_picture.jpg'
            return JsonResponse({'status': 'success', 'avatar_url': avatar_url})
        
        elif 'about' in request.POST:
            user_profile.about = request.POST.get('about', '').strip()
            user_profile.save()
            return JsonResponse({'status': 'success'})
        
        elif 'content' in request.POST:
            content = request.POST.get('content', '').strip()
            if content:
                comment = Comment.objects.create(
                    user=request.user,
                    profile=user_profile,
                    content=content
                )
                return JsonResponse({
                    'status': 'success',
                    'comment': {
                        'user__username': comment.user.username,
                        'content': comment.content,
                        'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'errors': 'Content cannot be empty'})
    
    else:
        comments = Comment.objects.filter(profile=user_profile).order_by('-timestamp')
        context = {
            'user_profile': user_profile,
            'comments': list(comments.values('user__username', 'content', 'timestamp')),
            'photo_url': user_profile.avatar.url if user_profile.avatar else '/static/images/default_profile_picture.jpg',
            'avatar_url': user_profile.avatar.url if user_profile.avatar else '/static/images/default_profile_picture.jpg',
            'average_rating': user_profile.average_rating, 
            'rating_count': user_profile.rating_count,      
        }   
        return render(request, 'profile.html', context)
    


@login_required
def other_profile_view(request, username):
    user = get_object_or_404(User, username=username)
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    is_owner = request.user == user
    is_owner_json = json.dumps(is_owner)  

    if request.method == 'POST':
        if 'content' in request.POST:
            # Handle comment submission
            content = request.POST.get('content', '').strip()
            if content:
                comment = Comment.objects.create(
                    user=request.user,
                    profile=user_profile,
                    content=content
                )
                return JsonResponse({
                    'status': 'success',
                    'comment': {
                        'user__username': comment.user.username,
                        'content': comment.content,
                        'timestamp': comment.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                })
            else:
                return JsonResponse({'status': 'error', 'errors': 'Content cannot be empty'})
        else:
            # Handle avatar and about updates if owner
            if is_owner:
                if 'avatar' in request.FILES:
                    user_profile.avatar = request.FILES['avatar']
                    user_profile.save()
                    avatar_url = user_profile.avatar.url if user_profile.avatar else '/static/images/default_profile_picture.jpg'
                    return JsonResponse({'status': 'success', 'avatar_url': avatar_url})
                elif 'about' in request.POST:
                    user_profile.about = request.POST.get('about', '').strip()
                    user_profile.save()
                    return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
    else:
        # GET request: Render the profile page
        comments = Comment.objects.filter(profile=user_profile).order_by('-timestamp')
        context = {
            'user_profile': user_profile,
            'comments': list(comments.values('user__username', 'content', 'timestamp')),
            'csrf_token': get_token(request),
            'avatar_url': user_profile.avatar.url if user_profile.avatar else '/static/images/default_profile_picture.jpg',
            'is_owner': is_owner,
            'is_owner_json': is_owner_json,  
            'average_rating': user_profile.average_rating,  # Add average rating
            'rating_count': user_profile.rating_count,      # Add total reviews
        }
        return render(request, 'other_profile.html', context)
  


@csrf_exempt
def update_appointment_status(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            appointment_ids = data.get("appointments", [])
            user = request.user

            # Update the status to 'Inprogress' and set the dog_walker to the current user
            appointment = Appointment.objects.get(id__in=appointment_ids)
            appointment.status = "Inprogress"
            appointment.dog_walker = user
            appointment.save()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method."})


@login_required
def get_appointments(request):
    appointments = Appointment.objects.filter(
        Q(dog_owner=request.user) | Q(dog_walker=request.user)
    ).order_by('-appointment_date')
    
    appointments_data = [{
        'id': apt.id,
        'appointment_date': apt.appointment_date.isoformat(),
        'duration': apt.duration,
        'location': apt.location,
        'status': apt.status,
        'dog_type': apt.dog_type,
        'dog_size': apt.dog_size,
        'dog_age': apt.dog_age,
        'dog_number': apt.dog_number,
        'special_requirement': apt.special_requirement,
        'dog_owner_username': apt.dog_owner.username if apt.dog_owner else None,
        'dog_walker_username': apt.dog_walker.username if apt.dog_walker else None,
    } for apt in appointments]
    
    return JsonResponse(appointments_data, safe=False)

@login_required
@require_http_methods(["POST"])
def cancel_appointment(request, appointment_id):
    try:
        data = json.loads(request.body)
        is_owner = data.get('is_owner', False)
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        if (is_owner and request.user != appointment.dog_owner) or \
           (not is_owner and request.user != appointment.dog_walker):
            return JsonResponse({'error': 'Permission denied'}, status=403)
            
        if appointment.status not in ['Scheduled', 'Inprogress']:
            return JsonResponse({'error': 'Can only cancel scheduled or in-progress appointments'}, status=400)
            
        if is_owner:
            appointment.status = 'Cancelled'
        else:
            appointment.status = 'Scheduled'
            appointment.dog_walker = None
            
        appointment.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Appointment cancelled successfully' if is_owner else 'Withdrawn from appointment successfully'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@login_required
def get_notifications(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')
    return JsonResponse([{
        'message': n.message,
        'appointment_id': n.appointment.id if n.appointment else None,
        'timestamp': n.timestamp.isoformat()
    } for n in notifications], safe=False)
    

@login_required
def mark_notification_read(request, appointment_id):
    if request.method == 'POST':
        Notification.objects.filter(
            user=request.user,
            appointment_id=appointment_id,
            is_read=False
        ).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=405)

@login_required
def submit_review(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, dog_owner=request.user, status='Completed')
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            
            walker_profile, created = UserProfile.objects.get_or_create(user=appointment.dog_walker)
            
            if created:
                walker_profile.rating_count = 1
                walker_profile.average_rating = appointment.rating
            else:
                walker_profile.rating_count += 1
                walker_profile.average_rating = (
                    (walker_profile.average_rating * (walker_profile.rating_count - 1) + appointment.rating)
                    / walker_profile.rating_count
                )
            walker_profile.save()
            
            messages.success(request, 'Review submitted successfully.')
            return redirect('existing_appointment')
    else:
        form = RatingForm(instance=appointment)
    return render(request, 'submit_review.html', {'form': form, 'appointment': appointment})