from django.contrib import admin
from django.http import HttpResponse
from .models import Session, Collection, File, Person


class SessionAdmin(admin.ModelAdmin):
    list_display = ("collection", "title", "synopsis")
    
admin.site.register(Session, SessionAdmin)

class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "synopsis", "access")
    
admin.site.register(Collection, CollectionAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "role")
    
admin.site.register(Person, PersonAdmin)

class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    
admin.site.register(File, FileAdmin)