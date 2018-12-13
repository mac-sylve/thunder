from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render,get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from thunderapp.models import Member, Message, Hobby
from django.db import IntegrityError
import datetime as D
from django.http import QueryDict
from django.db.models import Q

from django.core import serializers
from datetime import datetime

from django.contrib.auth.models import User


from thunderapp.templatetags.extras import display_message

appname = "Thunder"

# decorator that tests whether user is logged in
def loggedin(view):
    def mod_view(request):
        if 'username' in request.session:
            username = request.session['username']
            try: user = Member.objects.get(username=username)
            except Member.DoesNotExist: raise Http404('Member does not exist')
            return view(request, user)
        else:
            context = {'appname': appname}
            return render(request,'thunderapp/not-logged-in.html',context)
    return mod_view

@loggedin
def logout(request, user):
    request.session.flush()

    context = { 'appname': appname, 'loggedin': False}
    return render(request,'thunderapp/index.html', context)

@csrf_exempt
def home(request):
    return render(request, 'thunderapp/base.html', {})


def index(request):
    context = { 'appname': appname }
    return render(request,'thunderapp/index.html',context)


def get_friend_profile(request,member_id):
    member = get_object_or_404(Member, pk=member_id)
    hobby = Hobby.objects.all()
    context = {'member': member,
               'Hobby': hobby}
    return render(request, 'thunderapp/profile.html', context)


@loggedin
def profile(request,user):
    member = get_object_or_404(Member, username=user.username)
    hobby = Hobby.objects.all()
    context = {
        'member':member,
        'appname': appname,
        'loggedin': True,
        'Hobby': hobby
    }
    return render(request, 'thunderapp/profile.html', context)



@loggedin
def matchlist(request, user):
    currentMember = get_object_or_404(Member, username=user.username)
    matches = []
    followers = Member.objects.filter(following__pk=currentMember.id)

    for member in currentMember.following.all():
        if member in followers:
            matches.append(member)

    matchRank = []

    for match in matches:
        count = 0
        for hobby in currentMember.hobbies.all():
            if hobby in match.hobbies.all():
                count += 1
        matchRank.append(count)

    insertionSort(matches, matchRank)

    context = {'appname': appname, 'currentMember': matches, 'loggedin': True}
    return render(request,'thunderapp/matchlist.html', context)

@csrf_exempt
def messages(request, user):
    # Whose messages are we viewing?
    if 'view' in request.GET:
        view = request.GET['view']
        try: view_user = Member.objects.get(username=view)
        except Member.DoesNotExist: raise Http404('Member does not exist')
        profile = view_user.profile
        # public messages that 'view_user' has received
        m1 = Message.objects.filter(recip=view_user,public=True)
        # public messages that 'view_user' has sent
        m2 = Message.objects.filter(sender=view_user,public=True)
        # messages 'user' sent 'view_user'
        m3 = Message.objects.filter(sender=user,recip=view_user)
        # messages 'view_user' sent 'user'
        m4 = Message.objects.filter(sender=view_user,recip=user)
        # union of the four query sets
        messages = m1.union(m2,m3,m4).order_by('-time')
    else:
        view = user.username
        profile = user.firstName
        # all messages I sent
        m1 = Message.objects.filter(sender=user)
        # all messages I received
        m2 = Message.objects.filter(recip=user)
        # union of the two query sets
        messages = m1.union(m2).order_by('-time')
    return render(request, 'thunderapp/messages.html', {
        'appname': appname,
        'username': user.username,
        'profile': profile,
        'view': view,
        'messages': messages,
        'loggedin': True}
                  )

@csrf_exempt
def register(request):
    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        g = request.POST.get('gender')
        d = request.POST.get('DofB')
        e = request.POST.get('email')
        fn = request.POST.get('firstname')
        ln = request.POST.get('lastname')
        #todo add hobby to profile
        hobby = request.POST.getlist('hobby[]')
        if len(hobby)==0:
            return JsonResponse({"success":False})

        b_date = datetime.strptime(d, '%Y-%m-%d')

        age = ((datetime.today() - b_date).days/365)

        if age < 18 or age  > 100:
            return JsonResponse({"success":False,"ageError":True})



        try:
            Member.objects.create(username=u,password=p,gender=g,dateOfBirth=d,email=e,firstName=fn,lastName=ln)
            member = Member.objects.get(username=u)
            for hobbyVal in hobby:
                print(hobbyVal)
                hob = Hobby.objects.filter(hobby=hobbyVal)
                member.hobbies.add(hob[0])
            context = {
                'appname' : appname,
                'username' : u
            }
            #return HttpResponseRedirect('profile', args=(member.username))
            return JsonResponse({"success":True})
        except IntegrityError:
            return JsonResponse({"success":False,"usernameError":True})
    else:
        hobby = Hobby.objects.all()
        context = {
            'appname': appname,
            'hobby': hobby
            }
        return render(request, 'thunderapp/signup.html', context)


@csrf_exempt
def upload_image(request,member_id):
    profileimage = request.FILES.get('profileimage')
    m = get_object_or_404(Member,id=member_id)

    try:
        m.profileImage = profileimage
        m.save()
    except IntegrityError:
        return JsonResponse({"success":False})
    return JsonResponse({"success":True})

@loggedin
def friends(request,user):
    # # list of people user is following
    # following = user.following.all()
    # # list of people that are following me
    # followers = Member.objects.filter(following__username=user.username)
    # # render reponse
    # context = {
    #     'appname': appname,
    #     'username': user.username,
    #     'members': members,
    #     'following': following,
    #     'followers': followers,
    #     'loggedin': True
    # }
    return render(request, 'thunderapp/friendsfriends.html', context)


# view function that responses to Ajax requests on login/register pages

@csrf_exempt
def checkuser(request):
    if 'username' in request.POST:
        try:
            member = Member.objects.get(username=request.POST['username'])
        except Member.DoesNotExist:
            if request.POST['page'] == 'login':
                return HttpResponse("<span class='taken'>&nbsp;&#x2718; Invalid username</span>")
            if request.POST['page'] == 'register':
                return HttpResponse("<span class='available'>&nbsp;&#x2714; This username is available</span>")
    if request.POST['page'] == 'login':
        return HttpResponse("<span class='available'>&nbsp;&#x2714; Valid username</span>")
    if request.POST['page'] == 'register':
        return HttpResponse("<span class='taken'>&nbsp;&#x2718; This username is taken</span>")
    return HttpResponse("<span class='taken'>&nbsp;&#x2718; Invalid request</span>")


@loggedin
def post_message(request, user):
    if request.method=='POST' and 'recip' in request.POST:
        recip = request.POST['recip']
        try: recip_user = Member.objects.get(username=recip)
        except Member.DoesNotExist: raise Http404('Member does not exist')
        text = request.POST['text']
        pm = request.POST['pm'] == '0'
        message = Message(sender=user,recip=recip_user,public=pm,time=timezone.now(),text=text)
        message.save()
        return HttpResponse(display_message(message, user.username))
    else:
        raise Http404('POST not used, or recip missing in POST request')


@loggedin
def erase_message(request, user):
    if 'id' in request.POST:
        msg_id = request.POST['id']
        try: message = Message.objects.get(id=msg_id)
        except Message.DoesNotExist: raise Http404('Message does not exist')
        # Check if user has permission to delete message
        if message.sender==user or message.recip==user:
            message.delete()
            return HttpResponse('message deleted')
        else:
            raise Http404('User does not have permission to delete message')
    else:
        raise Http404('Missing id in POST')

def sortByHobbies(currentMember, members):
    matchRank = []

    for member in members:
        count = 0
        for hobby in currentMember.hobbies.all():
            if hobby in member.hobbies.all():
                count += 1
        matchRank.append(count)
    insertionSort(members, matchRank)

    return members

def insertionSort(matchList, matchRank):
    for i in range(len(matchList)):
        insert(matchRank[i], matchRank, i, matchList, matchList[i])


def insert(k, matchRank, hi, matchList, member):
    for i in range(hi, 0, -1):
        if k < matchRank[i - 1]:
            matchRank[i] = k
            matchList[i] = member
            return
        else:
            matchRank[i] = matchRank[i - 1]
            matchList[i] = matchList[i - 1]
    matchRank[0] = k
    matchList[0] = member


@csrf_exempt
def update_profile_details(request,member_id):

    m = get_object_or_404(Member,id=member_id)

    if request.method == "PUT":
        try:
            put = QueryDict(request.body)
            fname = put.get('updatefirstname')
            lname = put.get('updatelastname')
            gender = put.get('updategender')
            hobby = put.getlist('updatehobby[]')
            if len(hobby)==0:
                return JsonResponse({"success":False})
            if fname == "":
                return JsonResponse({"success":False})

            if lname == "":
                return JsonResponse({"success":False})

            m.firstName = fname
            m.lastName = lname
            m.gender = gender
            for hobbyVal in hobby:
                print(hobbyVal)
                hob = Hobby.objects.filter(hobby=hobbyVal)
                m.hobbies.add(hob[0])

            m.save()

        except Member.DoesNotExist:
            return JsonResponse({"success":False})

    return JsonResponse({"success":True})

@csrf_exempt
@loggedin
def followMember(request, user):
    if request.method == "PUT":
        # try:
        put = QueryDict(request.body)
        member_id = put.get('mID')
        newFriend = Member.objects.get(pk=member_id)
        currentUser = Member.objects.get(pk=user.pk)
        currentUser.following.add(newFriend)
        currentUser.save()

        # except Member.DoesNotExist:
        #     return JsonResponse({"success": False})

    return JsonResponse({"success": True})

@loggedin
def list_of_members(request,user):
    currentMember = get_object_or_404(Member, username=user.username)
    following = user.following.all()
    membersQuerySet = Member.objects.exclude(pk=user.pk)

    members = []

    for member in membersQuerySet.all():
        members.append(member)

    for member in members:
         if member in following:
             members.remove(member)

    members = sortByHobbies(currentMember, members)

    context = {'members': members, 'loggedin': True}
    return render(request, 'thunderapp/listofmembers.html',context)

@loggedin
def search_members(request,user):
    currentMember = get_object_or_404(Member, pk=user.pk)
    following = user.following.all()
    if request.method == "GET":
        search = request.GET.get('search_members')
        gender = request.GET.get('filter_gender')
    else:
        search = ''
        gender = ''

    name = search
    if gender =='':
        membersQuerySet = Member.objects.filter(firstName__contains= name)
        members = []

        for member in membersQuerySet.all():
            members.append(member)

        for member in members:
            if member in following:
                members.remove(member)

        members = sortByHobbies(currentMember, members)

        return render(request, 'thunderapp/searchmembers.html', {'members': members,'loggedin': True})

    membersQuerySet = Member.objects.filter(firstName_contains= name).filter(gender_contains= gender)
    members = []

    for member in membersQuerySet.all():
        members.append(member)

    for member in members:
        if member in following:
            members.remove(member)

    members = sortByHobbies(currentMember, members)
    return render(request, 'thunderapp/searchmembers.html', {'members': members,'loggedin': True})



@loggedin
def search_gender(request,user):
    currentMember = get_object_or_404(Member, pk=user.pk)
    following = user.following.all()
    if "filter_by_gender" in request.GET:
        gender = request.GET.get('filter_by_gender')
        if gender =='':
            membersQuerySet = Member.objects.all().exclude(pk=user.pk)

            members = []

            for member in membersQuerySet.all():
                members.append(member)

            for member in members:
                if member in following:
                    members.remove(member)

            members = sortByHobbies(currentMember, members)
            return render(request, 'thunderapp/searchmembers.html', {'members': members,'loggedin': True})
    else:
        gender = ''

    membersQuerySet = Member.objects.filter(gender=gender).exclude(pk=user.pk)

    members = []

    for member in membersQuerySet.all():
        members.append(member)

    for member in members:
         if member in following:
             members.remove(member)

    members = sortByHobbies(currentMember, members)
    return render(request, 'thunderapp/searchmembers.html', {'members': members,'loggedin': True})

@csrf_exempt
def loginUser(request):
    if 'username' in request.POST and 'password' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
        return checkUser(request,username,password)

    elif request.session.get('username'):
        username = request.session.get('username')
        password = request.session.get('password')
        return checkUser(request,username,password)
    else:
        context = {'appname': appname}
        return render(request, 'thunderapp/login.html', {})

def checkUser(request,username,password):

    try:
        member = Member.objects.get(username=username)
        if member.password != password:
            return JsonResponse({"success":False})
    except Member.DoesNotExist:
        return JsonResponse({"success":False})
    if member.password == password:

        context = {
            "success":True,
            'appname': appname,
            'username': username,
            'member': member,
            'loggedin': True
        }
        request.session['username'] = username
        request.session['password'] = password
        response = render(request, 'thunderapp/login.html',context)
        # response = JsonResponse({"success":True,"redirect":True,"redirect_url":"http://127.0.0.1:8000/profile/",
        #                          "appname":appname,"username":username,"loggedin":True, "member":serialized_obj})
        # remember last login in cookie
        now = D.datetime.utcnow()
        max_age = 365 * 24 * 60 * 60  # one year
        delta = now + D.timedelta(seconds=max_age)
        format = "%a, %d-%b-%Y %H:%M:%S GMT"
        expires = D.datetime.strftime(delta, format)
        response.set_cookie('last_login', now, expires=expires)
        return response


    return HttpResponse()

