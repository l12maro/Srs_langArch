from django.contrib import admin
from django.http import HttpResponse
#from .models import ProcessedXML
#from .forms import UploadXMLForm
#import xml.etree.ElementTree as E
from .models import MetaText


class MetaTextAdmin(admin.ModelAdmin):
    list_display = ("textEAF", "collection", "session", "title", "synopsis", "date")
    
admin.site.register(MetaText, MetaTextAdmin)

'''
class ProcessedXMLAdmin(admin.ModelAdmin):
    change_list_template = 'admin/upload_xml.html'
    
    def get_urls(self):
        from django.urls import path
        urlpatterns = super().get_urls()
        urlpatterns += [
            path('upload-xml/', self.upload_xml, name='upload-xml'),
        ]
        return urlpatterns
    
    def upload_xml(self, request):
        if request.method == 'POST':
            form = UploadXMLForm(request.POST, request.FILES)
            if form.is_valid():
                xml_content = form.cleaned_data['xml_file'].read().decode('utf-8')
                
                # Process the XML content (for demonstration, just echoing it)
                try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            self.title = root.find('title').text

            #if no languages are specified, we add English and Tsuut'ina as the default
            languages = root.find('languages').text
            if languages is not None:
                if len(languages) > 3:
                    lang = []
                    lang = lang.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        self.languages.add(l)
                else:
                    languages, created = Language.objects.get_or_create(name=languages)
                    self.languages.add(languages)
            else:
                eng, created = Language.objects.get_or_create(name="eng")
                tsuu, created = Language.objects.get_or_create(name="srs")
                self.languages.add(eng)
                self.languages.add(tsuu)
                
            
            working_languages = root.find('workingLanguages').text
            if working_languages is not None:
                if len(working_languages) > 3:
                    lang = []
                    lang = lang.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        self.languages.add(l)
                else:
                    languages, created = Language.objects.get_or_create(name=working_languages)
                    self.languages.add(languages)
            else:
                eng, created = Language.objects.get_or_create(name="eng")
                tsuu, created = Language.objects.get_or_create(name="srs")
                self.languages.add(eng)
                self.languages.add(tsuu)
                
            genre = root.find('genre').text
            if genre is not None:
                self.genre, created = Genre.objects.get_or_create(name=genre)
            else:
                self.genre, created = Genre.objects.get_or_create(name="Unclassified")
                
            subgenre = root.find('Sub-Genre').text
            if subgenre is not None:
                self.subgenre, created = Genre.objects.get_or_create(name=subgenre, parent_genre=self.genre)
            else:
                self.subgenre = None
                
            synopsis = root.find('synopsis').text
            if synopsis is not None:
                self.synopsis = synopsis
            
            date = root.find('date').text
            if date is not None:
                self.date = date
            
            contributors = root.find('contributions')
            for contributor in contributors.findall('contributor'):
                name = contributor.find('name').text
                role = contributor.find('role').text
                contributor_obj, created = Person.objects.get_or_create(name=name)
                if role == 'speaker':
                    self.speakers.add(contributor_obj)
                elif role == 'participant':
                    self.participants.add(contributor_obj)
                except Exception as e:
                    print(f"Error parsing XML: {e}")
                
                # Save the processed data to the database
                ProcessedXML.objects.create(data=processed_data)
                
                # Delete the uploaded XML file
                request.FILES['xml_file'].close()
                
                return HttpResponse('XML uploaded and processed successfully.')
        else:
            form = UploadXMLForm()
        
        context = {
            'form': form,
        }
        
        return self.render_change_form(request, context)
        
admin.site.register(ProcessedXML, ProcessedXMLAdmin)
'''