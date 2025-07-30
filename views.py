from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponseRedirect,HttpResponse
from django.urls import reverse
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from . models import Club, Trophy, Player,Message,Schedule,TrophyYear,Coach
from .forms import PlayerFilterForm
from datetime import datetime
from django.utils import timezone
from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
import re
# Create your views here.




def index(request):
    if request.method=="POST":
        username=request.POST["username"]
        password=request.POST["password"]

        try:
            user=User.objects.get(username=username)
            user=authenticate(request,username=username,password=password)

            if user is not None:
                login(request,user)
                return redirect("home")
            
            else:
                return render(request,"Assist/login.html",{
                    "message":"Incorrect Password."
                })
            
        except User.DoesNotExist:
             return render(request,"Assist/login.html",{
                    "message":"Incorrect Username."
                })
        
    return render(request, "Assist/login.html")




def sign_up(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not all([username,password,confirm_password]):
            return render(request, "Assist/sign_up.html", {"error":"Please enter all the details."})

        if password != confirm_password:
            return render(request, "Assist/sign_up.html", {
                "error": "Passwords do not match.",
                 "username":username
            })
        
        if len(password) < 8:
            return render(request,"Assist/sign_up.html",{
                "error":"Password must be atleast 8 characters long.",
                "username":username,
            })
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, "Assist/sign_up.html", {
                "error": "Username already exists. Please choose another.",
            })

        user = User.objects.create_user(
            username=username,
            password=password
        )
        user.save()
        
        return redirect('index')
    
    return render(request, "Assist/sign_up.html")




def forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")
        if not User.objects.filter(username=username).exists():
            return render(request, "Assist/forgot_password.html", {
                "error": "Username not found."
            })
        # Redirect to reset password with username
        return render(request, "Assist/reset_password.html", {
            "username": username
        })
    
    return render(request, "Assist/forgot_password.html")




def reset_password(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not all([username,password,confirm_password]):
            return render(request, "Assist/reset_password.html", {
                "username": username,
                "error": "Please enter all the details."
            })


        if password != confirm_password:
            return render(request, "Assist/reset_password.html", {
                "username": username,
                "error": "Passwords do not match."
            })
        
        if len(password) < 8:
            return render(request,"Assist/reset_password.html",{
                "error":"Password must be atleast 8 characters.",
                "username":username,
            })

        try:
            user = User.objects.get(username=username)
            user.set_password(password)  # Django uses its hashing 
            user.save()
            return render(request,"Assist/reset_password.html",{
                "success":"Password updated successfully"
            })
        
        
        except User.DoesNotExist:
            return render(request, "Assist/reset_password.html", {
                "error": "User not found.",
                "username": username
            })
        




@login_required
def home(request):
    if request.user.is_authenticated:
        if Club.objects.filter(user=request.user).exists():
            club = Club.objects.get(user=request.user)
            now = timezone.now()

            next_match = Schedule.objects.filter(
                club=club,
                event_type='Match',
                event_date__gt=now,
            ).order_by('event_date').first()

            return render(request, "Assist/home.html", {
                "club": club,
                "next_match": next_match
            })
        
        else:
            if request.method == "POST":
                club_name = request.POST.get("name")
                stadium_name = request.POST.get("stadium")
                club_logo = request.FILES.get("logo")
                club_sponsor = request.POST.get("sponsor")
                club_transfer_budget = request.POST.get("transfer_budget")
                club_salary_budget = request.POST.get("salary_budget")

                # Check if any required field is missing
                if not all([club_name, stadium_name, club_logo, club_sponsor, club_transfer_budget, club_salary_budget]):
                    return render(request, "Assist/club_details.html", {
                        "message": "All fields are required, please fill the form again."
                    })
                
                if club_logo.content_type not in ["image/jpeg", "image/png"]:
                    return render(request, "Assist/club_details.html", {
                        "message": "Invalid file type.",
                        "club_name": club_name,
                        "stadium_name": stadium_name,
                        "club_logo": club_logo,
                        "club_sponsor": club_sponsor,
                        "club_transfer_budget": club_transfer_budget,
                        "club_salary_budget": club_salary_budget
                    })
                
                if club_logo.size > 10 * 1024 * 1024:
                    return render(request, "Assist/club_details.html", {
                        "message": "File is too large.",
                        "club_name": club_name,
                        "stadium_name": stadium_name,
                        "club_logo": club_logo,
                        "club_sponsor": club_sponsor,
                        "club_transfer_budget": club_transfer_budget,
                        "club_salary_budget": club_salary_budget
                    })


                try:
                    with transaction.atomic():

                        club = Club.objects.create(
                            name=club_name,
                            stadium_name=stadium_name,
                            logo=club_logo,
                            sponsor=club_sponsor,
                            user=request.user,
                            transfer_budget=club_transfer_budget,
                            salary_budget=club_salary_budget,
                        )

                except Exception as e:
                    return render(request, 'Assist/club_details.html', {
                        "message": f"An error occurred while creating the club: {str(e)}"
                    })

                return render(request, 'Assist/home.html', {"club": club})

            else:
                return render(request, "Assist/club_details.html")





def your_players(request):
    
    club = Club.objects.get(user=request.user)

    coaches = club.coach.all()

    # Retrieve all players associated with the club
    all_players = club.players.all()

    
    strikers = all_players.filter(position=Player.STRIKER)
    midfielders = all_players.filter(position=Player.MIDFIELDER)
    defenders = all_players.filter(position=Player.DEFENDER)
    Goalkeepers = all_players.filter(position=Player.GOALKEEPER)


    return render(request, "Assist/your_players.html", {
        "strikers": strikers,
        "midfielders": midfielders,
        "defenders": defenders,
        "goalkeepers": Goalkeepers,
        "coaches":coaches,
    })




def buy_players(request):
    return render(request,"Assist/buy_players.html")




def buy_players_search(request):
    if request.method == "POST":
        player_name = request.POST.get("player_name") 
        try:
            players = Player.objects.all()
            user_club = Club.objects.get(user=request.user)  

            
            player_name = re.sub(r'\s+', ' ', player_name.strip())  # removes extra spaces
            player_name = " ".join([part.capitalize() for part in player_name.split()])
            player_search = players.filter(name__iexact=player_name)
            existing_player = player_search.filter(id__in=user_club.players.values_list('id', flat=True)).first()

            if existing_player:
                # Player already in the club
                return render(request, "Assist/buy_players_search.html", {
                    "already_in_club": f"{existing_player.name} is already in your club.",
                })
            elif player_search.exists():
                return render(request, "Assist/buy_players_search.html", {
                    "player_search": player_search, 
                })
            else:
                return render(request, "Assist/buy_players_search.html", {
                    "no_player": "No players found with the given name.",
                })

        except ObjectDoesNotExist:
            players = None

    return render(request, "Assist/buy_players_search.html")




def buy_players_filter(request):
    user_club = Club.objects.get(user=request.user)

    form = PlayerFilterForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            country = form.cleaned_data.get('country')
            age = form.cleaned_data.get('age')
            position = form.cleaned_data.get('position')

            # Check if at least one filter is selected
            if country or age or position:
                players = Player.objects.all().exclude(club=user_club)

                if country:
                    players = players.filter(country__in=country)
                if age:
                    players = players.filter(age__in=[int(a) for a in age])
                if position:
                    players = players.filter(position__in=position)

                if not players.exists():
                    return render(request, 'Assist/buy_players_filter.html', {
                        'form': form,
                        'message': 'No players found matching the selected filters.'
                    })

                return render(request, 'Assist/buy_players_filter.html', {
                    'form': form,
                    'players': players
                })

    return render(request, 'Assist/buy_players_filter.html', {
        'form': form
    })



def buy_player_club(request):

    clubs=Club.objects.all()
    clubs=clubs.exclude(user=request.user)

    if request.method=="POST":
        club_id=request.POST.get("club")

        if not club_id:
            return render(request,"Assist/buy_player_club.html",{"clubs":clubs,"message":"Please select a club."})

        club=Club.objects.get(id=club_id)
        players=club.players.all()

        strikers=players.filter(position=Player.STRIKER)
        defenders=players.filter(position=Player.DEFENDER)
        midfielders=players.filter(position=Player.MIDFIELDER)
        goalkeepers=players.filter(position=Player.GOALKEEPER)

        return render(request,"Assist/club_players.html",{"club":club,"strikers":strikers,"defenders":defenders,"midfielders":midfielders,"goalkeepers":goalkeepers})


    return render(request,"Assist/buy_player_club.html",{"clubs":clubs})



def add_player(request, player_id):
    player = Player.objects.get(id=player_id)
    sender_club = Club.objects.get(user=request.user) 
    recipient_club_name = player.club.name
    recipient_club = Club.objects.get(name=recipient_club_name)

    if request.method == 'POST':
        # Check if the sender club has enough transfer budget
        if sender_club.transfer_budget < player.market_value:
            return render(request, 'Assist/send_message.html', {
                "player": player,
                "message": "Your transfer budget is not enough to sign this player."
            })

        
        try:
            with transaction.atomic():
            
                Message.objects.create(
                    sender_club=sender_club,
                    recipient_club=recipient_club,
                    player=player,
                    market_value=player.market_value
                )

             

        except Exception as e:
            return render(request, 'Assist/send_message.html', {
                "player": player,
                "message": f"An error occurred: {str(e)}"
            })

        return redirect('home')

    return render(request, 'Assist/send_message.html', {'player': player})






def add_free_agent(request, player_id):
    
    player = Player.objects.get(id=player_id)
    club = Club.objects.get(user=request.user)

    if request.method=="POST":

        if club.transfer_budget < player.market_value:
           return render(request,"Assist/add_free_agent.html",{"player":player,"message":"Your budget is not enough to sign this player."})

        else:

            try:
                with transaction.atomic():
                    # Update club's salary budget
                    club.salary_budget -= player.market_value
                    club.save()

                    # Assign player to the club
                    player.club = club
                    player.save()
                    return redirect('your_players')

            except Exception as e:

                # Handle the error and return a response
                return render(request, "Assist/add_free_agent.html", {
                "message": f"An error occurred: {str(e)}",
                "player":player
                })  


    return render(request,"Assist/add_free_agent.html",{"player":player})





def transfer_requests(request):
    club = Club.objects.get(user=request.user)  
    sent_messages = Message.objects.filter(sender_club=club,sender_deleted=False)
    received_messages=Message.objects.filter(recipient_club=club,recipient_deleted=False) 
    
    return render(request, 'Assist/transfer_requests.html', {'received_messages': received_messages, "sent_messages":sent_messages})




@transaction.atomic
def view_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)

    if Club.objects.get(user=request.user) == message.sender_club:
        club=message.sender_club


    else:
        club=None


    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'accept':
            message.accepted = True
            message.rejected = False  # Ensure rejection is cleared if accepted
            
            sender_club=message.sender_club
            recipient_club=message.recipient_club
            player=message.player

            sender_club = Club.objects.select_for_update().get(id=sender_club.id)
            recipient_club = Club.objects.select_for_update().get(id=recipient_club.id)
            player = Player.objects.select_for_update().get(id=player.id)


            sender_club.transfer_budget -= message.player.market_value
            sender_club.salary_budget-=message.player.salary
            recipient_club.transfer_budget += message.player.market_value
            recipient_club.salary_budget+=message.player.salary
            sender_club.save()
            recipient_club.save()

    
            player.club=sender_club
            player.save()

        elif action == 'reject':
            message.accepted = False
            message.rejected = True  # Ensure acceptance is cleared if rejected
        
        message.save() 

        Message.objects.create(
            sender_club=message.recipient_club,
            recipient_club=message.sender_club,
            player=message.player,
            market_value=message.market_value,
            accepted=message.accepted,
            rejected=message.rejected
        )
        return redirect('view_message', message_id=message.id)  # Redirect to the same page

    return render(request, 'Assist/view_message.html', {'message': message,'club':club })





def delete_message(request, message_id):


    message = get_object_or_404(Message, id=message_id)
    club = Club.objects.get(user=request.user)

    try:

        with transaction.atomic():
            message.delete_for_club(club)

    except Exception as e:
        # Handle any error that occurs during the transaction
        return render(request,"Assist/transfer_requests.html",{"error":f"An error occurred: {str(e)}"},status=500)

    return redirect('transfer_requests')





def player_details(request,player_id):
    player=Player.objects.get(id=player_id)

    return render(request,"Assist/player_details.html",{ 
        "player":player 
        })




def remove_player(request, player_id):
    player = Player.objects.get(pk=player_id)
    club = Club.objects.get(user=request.user)

    try:
    
        with transaction.atomic():
            club.salary_budget += player.salary
            club.save()

            player.club = None
            player.save()

    except Exception as e:
        # Handle the exception if something goes wrong during the transaction
        return HttpResponse(f"An error occurred: {str(e)}", status=500)

    return redirect('your_players')





def schedule(request):
    club=Club.objects.get(user=request.user)  
    upcoming_schedule = Schedule.objects.filter(club=club, event_date__gte=timezone.now()).order_by('event_date')
    return render(request, 'Assist/schedule.html', {'upcoming_schedule': upcoming_schedule})





def add_schedule(request):
    club = Club.objects.get(user=request.user)
    clubs = Club.objects.exclude(id=club.id)

    if request.method == 'POST':
        event_type = request.POST.get('event_type')
        opponent_id = request.POST.get('opponent')
        event_date_str = request.POST.get('event_date')

        if not all([event_type, event_date_str]):
            return render(request, 'Assist/add_schedule.html', {
                'clubs': clubs,
                "message": "Please select an event type and event date."
            })

        if event_type == "Match" and not opponent_id:
            return render(request, 'Assist/add_schedule.html', {
                'clubs': clubs,
                "message": "Please select an opponent."
            })

        opponent = None
        if event_type == 'Match':
            opponent = get_object_or_404(Club, id=opponent_id)
            location = opponent.stadium_name
        else:
            location = club.stadium_name

        try:
            with transaction.atomic():
                event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
                event_date = timezone.make_aware(event_date)

                Schedule.objects.create(
                    event_type=event_type,
                    opponent=opponent,
                    event_date=event_date,
                    location=location,
                    club=club
                )

        except Exception as e:
            return render(request, 'Assist/add_schedule.html', {
                "clubs": clubs,
                "message": "An error occurred while saving the schedule. Please try again."
            }, status=500)

        return redirect('schedule')

    return render(request, 'Assist/add_schedule.html', {'clubs': clubs})






def update_schedule(request, schedule_id):

    schedule = get_object_or_404(Schedule, pk=schedule_id)

    
    club = Club.objects.get(user=request.user)
    clubs = Club.objects.exclude(id=club.id)

    if request.method == 'POST':

        event_type = request.POST.get('event_type')
        opponent_id = request.POST.get('opponent')   
        event_date_str = request.POST.get('event_date')
       
        if not all([event_type, event_date_str]):
            return render(request, 'Assist/add_schedule.html', {
                'clubs': clubs,
                "message": "Please select an event type and event date."
            })

        if event_type == "Match" and not opponent_id:
            return render(request, 'Assist/add_schedule.html', {
                'clubs': clubs,
                "message": "Please select an opponent."
            })

        opponent = None
        if event_type == 'Match':
            opponent = get_object_or_404(Club, id=opponent_id)
            location = opponent.stadium_name
        else:
            location = club.stadium_name


        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
            event_date = timezone.make_aware(event_date)
            
            with transaction.atomic():
                # Update the schedule with the new data
                schedule.event_type = event_type
                schedule.opponent = opponent
                schedule.event_date = event_date
                schedule.location = location
                schedule.save()

        except Exception as e:
            # Handle errors (for example, if saving the schedule fails)
            return render(request,"Assist/update_schedule.html",{'schedule': schedule, 'clubs': clubs ,"message":f"An error occurred: {str(e)}"}, status=500)

        return redirect('schedule')

    return render(request, 'Assist/update_schedule.html', {'schedule': schedule, 'clubs': clubs})






def delete_schedule(request,schedule_id):
    schedule=get_object_or_404(Schedule,pk=schedule_id)
    schedule.delete()
    return redirect('schedule')





def free_player(request):
    if request.method == "POST":
        player_name = request.POST.get("name")
        player_dob = request.POST.get("dob")
        player_country = request.POST.get("country")
        player_market_value = request.POST.get("market_value")
        player_salary = request.POST.get("salary")
        player_position = request.POST.get("position")
        player_jersey_no=request.POST.get("jersey_no")

        # Check for missing fields
        if not all([player_name, player_dob, player_country, player_market_value, player_salary, player_position,player_jersey_no]):
            return render(request, "Assist/free_player.html", {
                "message": "All fields are required, please enter them again."
            })

        player_name = re.sub(r'\s+', ' ', player_name.strip()) 
        player_name = " ".join([part.capitalize() for part in player_name.split()])

        player_salary = int(player_salary)
        player_jersey_no=int(player_jersey_no)
        
        club = Club.objects.get(user=request.user)

        if player_salary > club.salary_budget:
            return render(request, "Assist/free_player.html", {
                "message": "Club salary budget is not enough to sign this player.",
                "player_name": player_name,
                "player_age": player_dob,
                "player_country": player_country,
                "player_market_value": player_market_value,
                "player_salary": player_salary,
                "player_position": player_position,
                "player_jersey_no": player_jersey_no,
            })

        try:
            # Use transaction.atomic to ensure that both the club's salary update
            # and the player creation are done atomically
            with transaction.atomic():
                club.salary_budget -= player_salary
                club.save()  

                # Create the player
                Player.objects.create(
                    name=player_name,
                    birth_day=player_dob,
                    country=player_country,
                    market_value=player_market_value,
                    salary=player_salary,
                    position=player_position,
                    club=club,
                    jersey_no=player_jersey_no
                )

        except Exception as e:
            # If any errors, rollback both the club update and player creation
            return render(request, "Assist/free_player.html", {
                "error": f"An error occurred: {str(e)}",
                "player_name": player_name,
                "player_age": player_dob,
                "player_country": player_country,
                "player_market_value": player_market_value,
                "player_salary": player_salary,
                "player_position": player_position
            })

        return redirect("your_players")

    return render(request, "Assist/free_player.html")


def update_club_details(request):
    club = Club.objects.get(user=request.user)

    if request.method == "POST":
        name = request.POST.get("name")
        stadium = request.POST.get("stadium")
        sponsor = request.POST.get("sponsor")
        transfer_budget = request.POST.get("transfer_budget")
        salary_budget = request.POST.get("salary_budget")

        if not all([name, stadium, sponsor, transfer_budget, salary_budget]):
            return render(request, "Assist/update_club_details.html", {
                "message": "Please fill all the fields.",
                "club":club
            })

        transfer_budget = int(transfer_budget)
        salary_budget = int(salary_budget)

        try:
            with transaction.atomic():

                club.name = name
                club.stadium_name = stadium
                club.sponsor = sponsor
                club.transfer_budget = transfer_budget
                club.salary_budget = salary_budget
                club.save()

        except Exception as e:
            # Handle any errors
            return render(request, "Assist/update_club_details.html", {
                "message": f"An error occurred: {str(e)}",
                "club":club
            })

        return redirect('home')

    return render(request, "Assist/update_club_details.html", {
        "club": club
    })




def update_club_logo(request):
    if request.method=="POST":
        logo=request.FILES.get("logo")

        if not logo:
            return render(request,"Assist/update_club_logo.html",{
                "message":"Please select a file."
            })
        
        if logo.content_type not in ["image/jpeg","image/png"]:
            return render(request,"Assist/update_club_logo.html",{
                "message":"Ivalid file type."
            })
        
        if logo.size > 10 * 1024 * 1024:
            return render(request,"Assist/update_club_logo.html",{
                "message":"File is too large."
            })
        
        club=Club.objects.get(user=request.user)
        club.logo=logo
        club.save()
        return redirect('home')
        
    return render(request,"Assist/update_club_logo.html")





def upload_club_kit(request):
    club=Club.objects.get(user=request.user)

    if request.method=="POST":
        kit=request.FILES.get("kit")

        if not kit:
            return render(request,"Assist/update_club_kit.html",{
                "message":"Please select a file."
            })
        
        if kit.content_type not in ["image/jpeg","image/png"]:
            return render(request,"Assist/upload_club_kit.html",{
                "message":"Invalid file type."
            })
        
        if kit.size > 10 *1024 * 1024:
            return render(request,"Assist/upload_club_kit.html",{
                "message":"File is too large."
            })
        
        club.kit=kit
        club.save()
        return redirect('home')
    
    return render(request,'Assist/update_club_kit.html')
    




def edit_player_details(request, player_id):
    player = Player.objects.get(id=player_id)
    club = Club.objects.get(user=request.user)

    if request.method == "POST":
        market_value = request.POST.get("market_value")
        salary = request.POST.get("salary")
        jersey_no = request.POST.get("jersey")

        if not all([market_value, salary,jersey_no]):
            return render(request, "Assist/edit_player_details.html", {
                "message": "Please fill all the fields.",
                "player": player
            })
        
        # Check if another player has the same jersey number
        elif Player.objects.filter(club=club, jersey_no=jersey_no).exclude(id=player_id).exists():
            return render(request, "Assist/edit_player_details.html", {
                "message": "The given jersey number already belongs to another player.",
                "player": player
            })

        else:
            jersey_no = int(jersey_no)
            if jersey_no > 99 or jersey_no < 1:
                return render(request, "Assist/edit_player_details.html", {
                    "message": "Jersey number should be between 1 and 99.",
                    "player": player
                })

            else:
                market_value = int(market_value)
                salary = int(salary)

                try:
                    with transaction.atomic():
                        
                        player.jersey_no = jersey_no
                        player.market_value = market_value
                        player.salary = salary
                        player.save()

                except Exception as e:
                    
                    return render(request, "Assist/edit_player_details.html", {
                        "message": f"An error occurred: {str(e)}",
                        "player": player
                    })

                return render(request, 'Assist/player_details.html', {"player": player})

    return render(request, 'Assist/edit_player_details.html', {"player": player})





def edit_player_picture(request,player_id):
    player=Player.objects.get(id=player_id)

    if request.method=="POST":
        picture=request.FILES.get("picture")

        if not picture:
            return render(request,"Assist/edit_player_picture.html",{
                "message":"Please select a file.",
                "player":player
            })
        
        if picture.content_type not in ["image/jpeg","image/png"]:
            return render(request,"Assist/edit_player.html",{
                "message":"invalid file type.",
                "player":player
            })
        
        if picture.size > 10 * 1024 * 1024:
            return render(request,"Assist/edit_player_picture.html",{
                "message":"File is too large.",
                "player":player
            })
        
        player.picture=picture
        player.save()
        return render(request,'Assist/player_details.html',{"player":player})

    return render(request,'Assist/edit_player_picture.html',{"player": player})





def trophies(request):
    club = Club.objects.get(user=request.user)
    trophies = club.trophies.all()

    if request.method == 'POST':
            trophy_id = request.POST.get('trophy_id')
            trophy = get_object_or_404(Trophy, id=trophy_id)
            year=now().year
            
            updated_trophy= TrophyYear.objects.get_or_create(trophy=trophy, year=year)
            return redirect('trophies')


    return render(request, 'Assist/trophies.html', {
        'club': club,
        'trophies': trophies,
    })





def add_trophy(request):
    club = Club.objects.get(user=request.user)
    current_year = now().year

    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.FILES.get('picture')
        year_input = request.POST.get('year')

        if not all([name,year_input]):
            return render(request, "Assist/add_trophy.html", {
                "message": "Please enter all the details.",
                "year": current_year
            })


        # Convert year to int
        try:
            year = int(year_input)
        except (TypeError, ValueError):
            return render(request, "Assist/add_trophy.html", {
                "message": "Please enter a valid year.",
                "year": current_year
            })

        # File validation (only if picture is uploaded)
        if picture:
            valid_types = ['image/jpeg', 'image/png']
            max_size = 10 * 1024 * 1024  # 10MB

            if picture.content_type not in valid_types or picture.size > max_size:
                return render(request, "Assist/add_trophy.html", {
                    "message": "Please select a valid PNG or JPG file under 10MB.",
                    "year": current_year
                })

        # check year
        if year < 1900 or year > current_year:
            return render(request, "Assist/add_trophy.html", {
                "message": f"Year must be between 1900 and {current_year}.",
                "year": current_year
            })

        if not name:
            return render(request, "Assist/add_trophy.html", {
                "message": "Enter a trophy name.",
                "year": current_year
            })

        try:
            
            with transaction.atomic():
                trophy = Trophy.objects.create(
                    name=name,
                    club=club,
                    picture=picture
                )

                # Create or get the TrophyYear for the specific year
                TrophyYear.objects.get_or_create(trophy=trophy, year=year)

        except Exception as e:
            # Handle any errors
            return render(request, "Assist/add_trophy.html", {
                "message": f"An error occurred: {str(e)}",
                "year": current_year
            })

        return redirect('trophies')

    return render(request, 'Assist/add_trophy.html', {"year": current_year})





def update_trophy(request, trophy_id):
    trophy = get_object_or_404(Trophy, id=trophy_id, club__user=request.user)
    current_year = now().year

    if request.method == 'POST':
        name = request.POST.get('name')
        years_input = request.POST.get('years')

        if not all([name,years_input]):
            return render(request, 'Assist/update_trophy.html', {
                "trophy": trophy,
                "message": "Please enter all the details.",
                "year": current_year,
            })

        try:

            with transaction.atomic():
                trophy.name = name
                trophy.save()

                # Update years only if the user entered new ones
                if years_input:
                    raw_years = [y.strip() for y in years_input.split(',') if y.strip()]
                    valid_years = []
                    invalid_years = []

                    for y in raw_years:
                        if not y.isdigit():
                            invalid_years.append(y)
                            continue

                        year_int = int(y)
                        if 1900 <= year_int <= current_year:
                            valid_years.append(year_int)
                        else:
                            invalid_years.append(y)

                    if invalid_years:
                        return render(request, "Assist/update_trophy.html", {
                            "trophy": trophy,
                            "message": f"Invalid year(s): {', '.join(invalid_years)}. Please enter years between 1900 and {current_year}.",
                            "year": current_year,
                            "existing_years": ", ".join([str(y.year) for y in trophy.years.order_by('year')])
                        })

                    # Replace old years with new ones
                    trophy.years.all().delete()

                    # Create or get the TrophyYear objects
                    for year in valid_years:
                        TrophyYear.objects.get_or_create(trophy=trophy, year=year)


        except Exception as e:
            # if any errors handle them
            return render(request, "Assist/update_trophy.html", {
                "trophy": trophy,
                "message": f"An error occurred: {str(e)}",
                "year": current_year,
                "existing_years": ", ".join([str(y.year) for y in trophy.years.order_by('year')])
            })

        return redirect('trophies')


    return render(request, 'Assist/update_trophy.html', {
        "trophy": trophy,
        "year": current_year,
        "existing_years": ", ".join([str(y.year) for y in trophy.years.order_by('year')])
    })






def add_coach(request):
    if request.method == "POST":
        coach_name = request.POST.get("name")
        coach_dob = request.POST.get("dob")
        coach_country = request.POST.get("country")
        coach_salary = request.POST.get("salary")
        coach_type = request.POST.get("type")

        # Check for missing fields
        if not all([coach_name, coach_dob, coach_country, coach_salary, coach_type]):
            return render(request, "Assist/free_player.html", {
                "message": "All fields are required, please enter them again."
            })

        coach_name = re.sub(r'\s+', ' ', coach_name.strip()) 
        coach_name = " ".join([part.capitalize() for part in coach_name.split()])

        salary = int(coach_salary)
        
        club = Club.objects.get(user=request.user)

        if salary > club.salary_budget:
            return render(request, "Assist/add_coach.html", {
                "message": "Club salary budget is not enough to sign this coach.",
                "coach_name": coach_name,
                "coach_age": coach_dob,
                "coach_country": coach_country,
                "coach_salary": coach_salary,
            })
        
        try:

            with transaction.atomic():
                club.salary_budget -= salary
                club.save()

                # Create the coach
                Coach.objects.create(
                    name=coach_name,
                    birth_day=coach_dob,
                    country=coach_country,
                    salary=salary,
                    club=club,
                    type=coach_type,
                )

        except Exception as e:

            return render(request, "Assist/add_coach.html", {
                "message": f"An error occurred: {str(e)}"
            })

        return redirect("your_players")

    return render(request, "Assist/add_coach.html")





def coach_details(request,coach_id):

    coach=Coach.objects.get(id=coach_id)

    return render(request,"Assist/coach_details.html",{ 
        "coach":coach 
        })






def edit_coach_details(request, coach_id):
    coach = Coach.objects.get(id=coach_id)

    if request.method == "POST":
        coach_salary = request.POST.get("salary")
        coach_type=request.POST.get("coach_type")

        # Check for missing fields
        if not all ([coach_salary,coach_type]):
            return render(request, "Assist/edit_coach_details.html", {
                "message": "Please enter the salary again.",
                "coach":coach
            })


        salary = int(coach_salary)

        club = Club.objects.get(user=request.user)

        if salary > club.salary_budget:
            return render(request, "Assist/edit_coach_details.html", {
                "message": "Club salary budget is not enough to sign this coach.",
                "coach":coach
            })


        try:
            with transaction.atomic():
                # Update the coach details
                coach.salary = salary
                coach.type=coach_type
                coach.save()

                # Update the club's salary budget
                club.salary_budget -= salary
                club.save()

        except Exception as e:
            #error handling
            return render(request, "Assist/edit_coach_details.html", {
                "message": "An error occurred while updating coach details. Please try again.",
                "coach":coach
            })

        return redirect("your_players")

    return render(request, "Assist/edit_coach_details.html", {"coach": coach})





def edit_coach_picture(request,coach_id):
    coach=Coach.objects.get(id=coach_id)

    if request.method=="POST":
        picture=request.FILES.get("picture")

        if not picture:
            return render(request,"Assist/edit_coach_picture.html",{
                "message":"Please select a file.",
                "coach":coach
            })
        
        if picture.content_type not in ["image/jpeg","image/png"]:
            return render(request,"Assist/edit_coach_picture.html",{
                "message":"invalid file type.",
                "coach":coach
            })
        
        if picture.size > 10 * 1024 * 1024:
            return render(request,"Assist/edit_coach_picture.html",{
                "message":"File is too large.",
                "coach":coach
            })
        
        coach.picture=picture
        coach.save()
        return render(request,'Assist/coach_details.html',{"coach":coach})

    return render(request,'Assist/edit_coach_picture.html',{"coach": coach})






def remove_coach(request, coach_id):

    coach = Coach.objects.get(id=coach_id)
    club = Club.objects.get(user=request.user)

    
    try:
        with transaction.atomic():
            # Update the club's salary 
            club.salary_budget += coach.salary
            club.save()

            # Delete the coach
            coach.delete()

    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}", status=500)

    return redirect('your_players')





def trophy_picture(request,trophy_id):
    trophy=Trophy.objects.get(id=trophy_id)

    if request.method=="POST":
        picture = request.FILES.get('picture')

            # File validation
        valid_types = ['image/jpeg', 'image/png']
        max_size = 10 * 1024 * 1024  # 10MB
            
        if picture:

                if picture.content_type not in valid_types:
                    return render(request,"Assist/trophy_picture.html",{"message":"Please select a JPEG or PNG file.","trophy":trophy})
                
                elif picture.size > max_size:
                    return render(request,"Assist/trophy_picture.html",{"message": "File size must be less than 10MB.","trophy":trophy})
                else:
                    trophy.picture=picture
                    trophy.save()
                    return redirect('trophies')
                
        else:
            return render(request,"Assist/trophy_picture.html",{"message": "Please select a file.","trophy":trophy})


    return render(request,"Assist/trophy_picture.html",{"trophy":trophy})




def log_out(request):
    logout(request)
    return redirect('index')
