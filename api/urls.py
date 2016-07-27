from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'civiworx.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # authentication / session management
    url(r'^auth/profile/me/$', 'account', name='my-account'),
    url(r'^auth/profile/$', 'new_account', name='new-account'),
    url(r'^auth/session/(?P<key>[a-z0-9]{64})/$', 'session', name='existing-session'),
    url(r'^auth/session/$', 'new_session', name='new-session'),

    # message control for reports
    url(r'^report/(?P<report_id>\d+)/message/(?P<message_id>\d+)/image/(?P<image_id>\d+)/$', 'message_image', name='message-image'),
    url(r'^report/(?P<report_id>\d+)/message/(?P<message_id>\d+)/images/$', 'message_images', name='message-images'),
    url(r'^report/(?P<report_id>\d+)/message/(?P<message_id>\d+)/$', 'message', name='message-details'),
    url(r'^report/(?P<report_id>\d+)/messages/$', 'messages', name='report-messages'),

    # report management
    url(r'^report/(?P<report_id>\d+)/subscribe/$', 'report_subscription', name='report-subscription'),
    url(r'^report/(?P<report_id>\d+)/$', 'report_details', name='report-details'),
    url(r'^reports/search/title/(?P<keyword>[a-zA-Z0-9]+)/$', 'search_report_title', name='search-reports-by-title'),
    url(r'^reports/search/area/(?P<lat>\-?\d+\.\d+)/(?P<lng>\-?\d+\.\d+)/(?P<radius>\d+\.\d+)/$',
    	'search_report_location', name='search-reports-by-location'),
    url(r'^reports/subscribed/$', 'subscribed_reports', name='subscribed-reports'),
    url(r'^reports/$', 'reports', name='all-reports'),

)
