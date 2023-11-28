import os
import xml.etree.ElementTree as ET
from django.db import transaction
from ..models import Collection, Session, File, Language, Person, Genre
from django.core.files import File as DjangoFile


def parse_xml_coll(xml_path):
        try:
            with open(xml_path, 'r', encoding='utf-8') as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                title = root.find('Title').text
                title = title if title is not None else ''
                                    
                synopsis = root.find('ProjectDescription').text
                synopsis = synopsis if synopsis is not None else ''
                
                #if no languages are specified, we add Tsuut'ina as the default
                language = root.find('VernacularISO3CodeAndName').text
                if language is not None:
                    code, _ = language.split(':')
                    language, created = Language.objects.get_or_create(name=code.strip())

                else:
                    language, created = Language.objects.get_or_create(name="srs")
                
                    
                #if no working languages are specified, we add English as the default
                wl = root.find('AnalysisISO3CodeAndName').text
                if wl is not None:
                    code, _ = wl.split(':')
                    wl, created = Language.objects.get_or_create(name=code.strip())
            
                else:
                    wl, created = Language.objects.get_or_create(name="eng")

                loc = root.find('Location').text
                loc = loc if loc is not None else ''
                
                region = root.find('Region').text
                region = region if region is not None else ''
                
                country = root.find('Country').text
                country = country if country is not None else ''

                continent = root.find('Continent').text
                continent = continent if continent is not None else ''
                
                access = root.find('AccessProtocol').text
                access = access if access is not None else ''
                    
                depositor = root.find('Depositor').text
                if depositor is not None:
                    depositor, created = Person.objects.get_or_create(name=depositor, role="depositor")
                    
                else: 
                    depositor, created = Person.objects.get_or_create(name="Unspecified")
                    
                contact = root.find('ContactPerson').text
                if contact is not None:
                    contact, created = Person.objects.get_or_create(name=contact, role="contact")
                    
                else: 
                    contact, created = Person.objects.get_or_create(name="Unspecified")
                    
                return title, synopsis, language, wl, loc, region, country, continent, access, depositor, contact
                        
        except Exception as e:
            print(f"Error parsing XML: {e}")

def populate_models_from_directory(collection_path):
    # Get the collections directory
    for collection_name in os.listdir(collection_path):
        collection_dir = os.path.join(collection_path, collection_name)
    
        # Find the Collection XML file and get values
        collection_xml_file = os.path.join(collection_dir, f'{collection_name}.sprj')
        title, synopsis, language, wl, loc, region, country,\
            continent, access, depositor, contact = parse_xml_coll(collection_xml_file)

        # Create or update the Collection model
        collection, created = Collection.objects.get_or_create(
            name=collection_name,
            title=title,
            synopsis=synopsis, 
            language=language,
            working_language=wl,
            location=loc,
            region=region,
            country=country,
            continent=continent,
            access=access,
            depositor=depositor,
            contact_person=contact
        )
        
        collection.save()
    
        # Recursively process Session directories
        process_sessions(collection, os.path.join(collection_dir, 'Sessions'))

def parse_xml_session(self, xml_path):
        
    try:
        with open(xml_path, 'r', encoding='utf-8') as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()
                
            title = root.find('Title').text
            title = title if title is not None else ''
                
            #if no languages are specified, we add English and Tsuut'ina as the default
            languages = root.find('languages').text
            langlist = []
            if languages is not None:
                if len(languages) > 3:
                    lang = []
                    lang = languages.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        langlist.append(l)
                else:
                    lang, created = Language.objects.get_or_create(name=languages)
                    langlist.append(l)
            else:
                eng, created = Language.objects.get_or_create(name="eng")
                tsuu, created = Language.objects.get_or_create(name="srs")
                langlist.append(eng)
                langlist.append(tsuu)
                    

            working_languages = root.find('workingLanguages').text
            wllist = []
            if working_languages is not None:
                if len(working_languages) > 3:
                    lang = []
                    lang = working_languages.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        wllist.append(l)
                else:
                    lang, created = Language.objects.get_or_create(name=working_languages)
                    wllist.append(lang)
            else:
                    eng, created = Language.objects.get_or_create(name="eng")
                    tsuu, created = Language.objects.get_or_create(name="srs")
                    wllist.append(eng)
                    wllist.append(tsuu)

            genre = root.find('genre').text
            if genre is not None:
                genre, created = Genre.objects.get_or_create(name=genre)
            else:
                genre, created = Genre.objects.get_or_create(name="Unclassified")
                    
            subgenre = root.find('Sub-Genre').text
            if subgenre is not None:
                subgenre, created = Genre.objects.get_or_create(name=subgenre, parent_genre=genre)
            else:
                subgenre = "Unclassified"
                    
            synopsis = root.find('synopsis').text
            synopsis = synopsis if synopsis is not None else ''
                
            date = root.find('date').text
            date = date if date is not None else "9999-99-99"
                
            contributors = root.find('contributions')
            speakerlist = []
            participantlist = []
            for contributor in contributors.findall('contributor'):
                name = contributor.find('name').text
                role = contributor.find('role').text
                contributor_obj, created = Person.objects.get_or_create(name=name, role=role)
                if role == 'speaker':
                    speakerlist.append(contributor_obj)
                elif role == 'participant':
                    participantlist.append(contributor_obj)
                        
        return title, langlist, wllist, genre, subgenre, synopsis, date, speakerlist, participantlist
    
    except Exception as e:
            print(f"Error parsing XML: {e}")
 
            

def process_sessions(collection, session_dir):
    for session_name in os.listdir(session_dir):
        session_path = os.path.join(session_dir, session_name)
        if os.path.isdir(session_path):
            # Find the Session XML file and parse its content
            session_xml_file = os.path.join(session_path, f'{session_name}.session')
            title, langlist, wllist, genre, subgenre,\
                synopsis, date, speakerlist, participantlist = parse_xml_session(session_xml_file)

            
            # Create or update the Session model
            session, created = Session.objects.get_or_create(
                name=session_name,
                collection=collection,
                title=title,
                genre=genre,
                subgenre=subgenre,
                synopsis=synopsis,
            )
            if date != '':
                session.date = date
                
            session.save()
            
            if len(langlist) > 0:
                for l in langlist:
                    session.languages.add(l)
                    
            if len(wllist) > 0:
                for l in wllist:
                    session.working_languages.add(l)
                    
            if len(speakerlist) > 0:
                for l in speakerlist:
                    session.speakers.add(l)
                    
            if len(participantlist) > 0:
                for l in participantlist:
                    session.participants.add(l)
                    
            # Recursively process File objects
            process_files(session, session_path)

def process_files(session, session_path):
    
    for file_name in os.listdir(session_path):
        file_path = os.path.join(session_path, file_name)
        
        if os.path.isfile(file_path):

            # Check if the file is not a session or meta file
            if not file_name.endswith(('.session', '.meta')):
                
                # Extract the filename without the extension
                file_base_name, file_extension = os.path.splitext(file_name)
                
                # Determine the file type (extension)
                file_type = file_extension.lstrip('.').lower()  # Remove the dot and make it lowercase

                # Upload the file content to the database
                with open(file_path, 'rb') as file_content:
                    file_obj = File(
                        name=file_base_name,
                        type=file_type,
                        session=session,
                    )
                    file_obj.content.save(file_name, DjangoFile(file_content))

                    # Save the file object
                    file_obj.save()

# Usage
collection_path = r'c:\Users\Lorena\Desktop\COLLECTIONS'
with transaction.atomic():
    populate_models_from_directory(collection_path)
