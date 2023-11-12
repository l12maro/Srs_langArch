from django.contrib import admin
from django.http import HttpResponse
from .models import Session, Collection, File, Person, Genre, TierReference, Postprocess, TranscriptELAN, Language

class LanguageAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

admin.site.register(Language, LanguageAdmin)

class SessionAdmin(admin.ModelAdmin):
    list_display = ("collection", "title", "synopsis")
    
admin.site.register(Session, SessionAdmin)

class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "synopsis", "access")
    
admin.site.register(Collection, CollectionAdmin)

class PersonAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "role")
    
admin.site.register(Person, PersonAdmin)

class FileAdmin(admin.ModelAdmin):
    list_display = ("name", "type")

admin.site.register(File, FileAdmin)

class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "parent_genre")
    
admin.site.register(Genre, GenreAdmin)
    
class TierReferenceAdmin(admin.ModelAdmin):
    list_display = ("transcriptELANfile", "collection", "sourceTierType", "destTierType")

admin.site.register(TierReference, TierReferenceAdmin)

class PostprocessAdmin(admin.ModelAdmin):
    list_display = ("annotationID", "transcriptELANfile", "annotation", "startTime", "endTime")
    
admin.site.register(Postprocess, PostprocessAdmin)

class TranscriptELANAdmin(admin.ModelAdmin):
    list_display = ("annotationID", "transcriptELANfile", "annotation", "startTime", "endTime", "textType")
    
admin.site.register(TranscriptELAN, TranscriptELANAdmin)
