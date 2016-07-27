from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest, \
    HttpResponseNotFound, HttpResponseNotAllowed, QueryDict
from django.views.decorators.http import require_http_methods
from django.db.models import Count

import json
import hashlib
import uuid

from models import Session
from worx.models import *

# TODO: push notification for subscribed/watch accounts

# Helper to hash plain text passwords
def hash_password(plain_text):
    return hashlib.sha256(plain_text).hexdigest()

# Helper for getting a reasonably unique session hash
def session_hash():
    return hashlib.sha256(uuid.uuid4().get_hex()).hexdigest()

# Helper to get account from session key
def account_from_session(request):
    # NOTE: Key should be set as X-CWX-SESSION-KEY (framework changes to the below)
    s_key = request.META.get('HTTP_X_CWX_SESSION_KEY', None)
    if s_key is not None:
        try:
            s_obj = Session.objects.get(key=s_key)
            return s_obj.account
        except Session.DoesNotExist:
            raise Account.DoesNotExist
    else: # i.e. is None
        raise Account.DoesNotExist

# Helper to convert message to JSON encodable dict
def encode_message(msg):
    # pull out details of the author
    author, a_img = 'Anonymous', None
    try:
        author = msg.written_by.profile.name
        a_img = msg.written_by.profile.img_data
    except Profile.DoesNotExist:
        pass # remain anonymous

    # create a sub-list of photo data for this message
    m_photos = [{'id': img.id, 'data': img.img_data} for img in msg.images.all()]

    # create the dictionary for this message
    return {
        'id': msg.id,
        # who wrote the message? hash(email), name, image
        'author': (hash_password(msg.written_by.account_key), author, a_img),
        'date_time': msg.written_on.isoformat(),
        'reply_to': msg.reply_to.id if msg.reply_to else None,
        'text': msg.message_text,
        'images': m_photos,
    }

# Helper to convert report to JSON encodable dict
def encode_report(rep):
    # pull out details of the author
    author, a_img = 'Anonymous', None
    try:
        author = rep.reported_by.profile.name
        a_img = rep.reported_by.profile.img_data
    except Profile.DoesNotExist:
        pass # remain anonymous

    # create the dictionary for this report
    return {
        'id': rep.id,
        # who wrote the report originally? hash(email), name, image
        'author': (hash_password(rep.reported_by.account_key), author, a_img),
        'date_time': rep.reported_on.isoformat(),
        'title': rep.title,
        'coord': (rep.latitude, rep.longitude),
    }




# ********* REPORT MANAGEMENT            *********

# Create a new report
# TODO: Do we want a "read all reports" option?
@require_http_methods(["POST"])
def reports(request):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # if we're POST-ing then read the report details and save
    if request.method == "POST":
        r_title = request.POST.get("title", None)
        r_lat = request.POST.get("latitude", None)
        r_lng = request.POST.get("longitude", None)
        # ensure we've been given all three fields
        if r_title is None or r_lat is None or r_lng is None:
            print r_title
            print r_lat
            print r_lng
            return HttpResponseBadRequest('Reports need title, latitude and longitude')
        # make a new report then redirect to the report info url
        n_report = Report(reported_by=account, title=r_title, 
            longitude=r_lng, latitude=r_lat)
        n_report.save()
        return redirect('report-details', report_id=n_report.id)

    # TODO: If adding get all then change this
    return HttpResponseNotAllowed('Not implemented')

# List all reports where title contains given keyword
@require_http_methods(["GET"])
def search_report_title(request, keyword):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # let the database do the hard work
    r_list = [encode_report(r) for r in \
        Report.objects.filter(title__icontains=keyword).annotate(num_msg=Count('messages'))]
    return HttpResponse(content=json.dumps(r_list), content_type='application/json')

# List all reports within a given radius of a point
@require_http_methods(["GET"])
def search_report_location(request, lat, lng, radius):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # TODO: lookup the real set 
    r_list = [encode_report(r) for r in Report.objects.all()[:10]]
    return HttpResponse(content=json.dumps(r_list), content_type='application/json')

# List all reports that this person is subscribed to
# NOTE: reports are auto-subscribed, but could be unsubscribed
# so we just list the ones that are currently subscribed
@require_http_methods(["GET"])
def subscribed_reports(request):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # lookup reports subscribed by this account
    r_list = [encode_report(r) for r in Report.objects.filter(observers__account=account)]
    return HttpResponse(content=json.dumps(r_list), content_type='application/json')

# Get details of the specific report
@require_http_methods(["GET"])
def report_details(request, report_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the report exists
    try:
        report = Report.objects.get(id=report_id)
        return HttpResponse(content=json.dumps(encode_report(report)), content_type='application/json')
    except Report.DoesNotExist:
        return HttpResponseNotFound('No such report')

# Subscribe (PUT) & unsubscribe (DELETE) to the given report
@require_http_methods(["PUT", "DELETE"])
def report_subscription(request, report_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the report exists
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return HttpResponseNotFound('No such report')
    # decide if this is a subscribe request or unsubscribe request
    if request.method == "PUT":
        the_sub, created = ReportSubscription.objects.get_or_create(account=account, report=report)
        return HttpResponse(content='OK') # TODO: anything else?
    elif request.method == "DELETE":
        # Delete the subscription 
        ReportSubscription.objects.filter(account=account, report=report).delete()
        return HttpResponse(content='OK', status=204)


# ********* POST A NEW REPORT MESSAGE     *********

# Create new message for a report or read list of messages
# C - POST: report/<id>/messages/
# R - GET:  
@require_http_methods(["GET", "POST"])
def messages(request, report_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the report exists
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return HttpResponseNotFound('No such report to add message to')

    # if this was a post then process the fields, otherwise return list
    if request.method == "POST":
        # ok, now we can read the fields and create a new message
        # the only posted fields will be message_text and reply_to
        m_text = request.POST.get('message_text', None)
        m_reply = request.POST.get('reply_to', None)
        # ensure the message text is valid
        if m_text is None:
            print "message text"
            return HttpResponseBadRequest('Message text is required')
        # if in reply then make sure that message exists for this report
        r_msg = None
        if m_reply is not None and m_reply != '' and m_reply != '0':
            try:
                r_msg = Message.objects.get(about_report=report, id=m_reply)
            except Message.DoesNotExist:
                print "reply problem"
                print "'%s'" % m_reply
                return HttpResponseBadRequest('Message reply invalid for this report')
        # all good so create the message and save it
        n_msg = Message(about_report=report, written_by=account, reply_to=r_msg,
            message_text=m_text)
        n_msg.save()

        img_data = request.POST.get("img_data", None)
        if img_data is not None:
        	m_img = MessageImage(on_message=n_msg, img_data=img_data)
	        m_img.save()

        # and return redirect to that message
        return redirect('message-details', report_id=report.id, message_id=n_msg.id)

    elif request.method == "GET": # a little redundant but anyway
        # manually serialize the reports messages into a JSON array
        m_list = [encode_message(m) for m in report.messages.all()]
        # and then transmit as JSON to the client
        return HttpResponse(content=json.dumps(m_list), content_type='application/json')

# Get details about a message
# TODO: do we want to make these updateable??
@require_http_methods(["GET"])
def message(request, report_id, message_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the message+report exists
    try:
        message = Message.objects.get(id=message_id, about_report__id=report_id)
    except Message.DoesNotExist:
        return HttpResponseNotFound('No such report/message exists')
    # as we're simply getting the message json
    return HttpResponse(content=json.dumps(encode_message(message)),
        content_type='application/json')

# Get or add images to the given report/message
@require_http_methods(["GET", "POST"])
def message_images(request, report_id, message_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the message+report exists
    try:
        message = Message.objects.get(id=message_id, about_report__id=report_id)
    except Message.DoesNotExist:
        return HttpResponseNotFound('No such report/message exists')
    # now if we're POST-ing then pull out the image data and create new image
    if request.method == "POST":
        img_data = request.POST.get("img_data", None)
        if img_data is None:
            return HttpResponseBadRequest('Image data must be given')
        m_img = MessageImage(on_message=message, img_data=img_data)
        m_img.save()
        return redirect('message-image', report_id=m_img.on_message.about_report.id, 
            message_id=m_img.on_message.id, image_id=m_img.id)
    elif request.method == "GET":
        # lookp the the set of images for this message and return them
        img_list = [{'id': i.id, 'data': i.img_data} for i in message.images.all()]
        return HttpResponse(content=json.dumps(img_list), content_type='application/json')

# Get the image data for the given image
@require_http_methods(["GET"])
def message_image(request, report_id, message_id, image_id):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401, 
            reason='Session key does not correspond to user account')
    # make sure the image+message+report exists
    try:
        img = MessageImage.objects.get(id=image_id, on_message__id=message_id, 
            on_message__about_report__id=report_id)
        # encode the image data 
        return HttpResponse(content=json.dumps({'id': img.id, 'data': img.img_data}), 
            content_type='application/json')
    except MessageImage.DoesNotExist:
        return HttpResponseNotFound('No such report/message/image exists')


# ********* PROFILE CREATION                    *********

# Create an acccount
# C - POST: auth/profile/
@require_http_methods(["POST"])
def new_account(request):
    # pull out the POSTed fields
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)
    person_name = request.POST.get('real_name', '')
    person_loc = request.POST.get('location', '')
    person_bio = request.POST.get('bio', '')
    person_img = request.POST.get('b64_img', '')

    # ensure both the username and password were given
    if username is None or password is None:
        return HttpResponseBadRequest("Missing username or password")
    
    # create a new account 
    u_norm = username.lower()
    p_hash = hash_password(password)
    n_account = Account(account_key=u_norm, passphrase=p_hash)
    n_account.save()
    # and then a profile for this new account
    n_profile = Profile(name=person_name, location=person_loc,
        bio=person_bio, img_data=person_img, account=n_account)
    n_profile.save()

    # create a session for the new account and send the key
    u_session = Session(key=session_hash(), account=n_account)
    u_session.save()
    return redirect('existing-session', key=u_session.key)

# Update account details
@require_http_methods(["PUT"])
def account(request):
    # ensure the session corresponds to valid user
    try:
        account = account_from_session(request)
    except Account.DoesNotExist:
        return HttpResponse(content='Invalid session', status=401,
            reason='Session key does not correspond to user account')
    # get the profile for this account
    profile, created = Profile.objects.get_or_create(account=account)
    posted = QueryDict(request.body)
    name = posted.get('real_name', profile.name)
    location = posted.get('location', profile.location)
    bio = posted.get('bio', profile.bio)
    img_b64 = posted.get('img_data', profile.img_data)
    profile.name = name
    profile.location = location
    profile.bio = bio
    profile.img_data = img_b64
    profile.save()
    return HttpResponse(content='OK')


# ********* SESSION AUTHENTICATION         *********

# Login / create new session
# C - POST: auth/session/
@require_http_methods(["POST"])
def new_session(request):
    # pull out the POSTed username and password
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)
    print username, password

    # ensure both username and password were given
    if username is None or password is None:
        return HttpResponseBadRequest("Missing username or password")

    # hash the password and lookup the pair
    u_norm = username.lower()
    p_hash = hash_password(password)
    print u_norm, p_hash
    try:
        # lookup the user account, create the session and redirect
        user = Account.objects.get(account_key=u_norm, passphrase=p_hash)
        u_session = Session(key=session_hash(), account=user)
        u_session.save() # persist the session with that key
        return redirect('existing-session', key=u_session.key)
    except Account.DoesNotExist:
        # invalid username or password so return a 401
        return HttpResponse(content='Invalid username or password', status=401,
            reason='Authentication failed')

# Session management
# R - GET:  auth/session/<key>/
# D - DEL:  auth/session/<key>/
@require_http_methods(["GET", "DELETE"])
def session(request, key):
    # All of the three methods require the session object
    try:
        s_obj = Session.objects.get(key=key)
    except Session.DoesNotExist:
        return HttpResponseNotFound("No such session")

    # Check the request method
    if request.method == "GET":
        # Want to get the session file
        return HttpResponse(content=s_obj.to_json(), content_type='application/json')
    elif request.method == "DELETE":
        # Delete the session - i.e. log out
        s_obj.delete()
        return HttpResponse(content='OK', status=204)



