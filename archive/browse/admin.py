from django.contrib import admin
from django.http import HttpResponse
#from .models import ProcessedXML
#from .forms import UploadXMLForm
#import xml.etree.ElementTree as E
from .models import MetaText


class MetaTextAdmin(admin.ModelAdmin):
    list_display = ("textEAF", "collection", "session", "title", "synopsis", "date", "fileType")
    
admin.site.register(MetaText, MetaTextAdmin)