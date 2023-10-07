from django.contrib import admin
from django.http import HttpResponse
from .models import MetaText, Classify, Language, Person


class MetaTextAdmin(admin.ModelAdmin):
    list_display = ("textEAF", "collection", "session", "title", "synopsis", "date", "fileType")
    
    
admin.site.register(MetaText, MetaTextAdmin)

class ClassifyAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "title", "synopsis", "access")
    
admin.site.register(Classify, ClassifyAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "role")
    
admin.site.register(Person, PersonAdmin)