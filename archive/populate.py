import os, shutil
import xml.etree.ElementTree as ET
from django.db import transaction
import django
django.setup()

from browse.models import Collection, Session, File, Language, Person, Genre, TranscriptELAN, Postprocess, TierReference
from django.contrib.postgres.search import SearchVector
from django.core.files import File as DjangoFile
from speach import elan

tier_references = []

def delete_all_data():
    '''
    Function to delete all collection data in the database
    and associated files stored in the uploads folder
    '''
    # Store TierReference values before deleting
    tier_references = TierReference.objects.all()
    
    Collection.objects.all().delete()
    print("Collection successfully deleted")
    
    TierReference.objects.all().delete()
    
    folder_path = './uploads'  
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print("Uploaded files successfully deleted")

    
def parse_xml_coll(xml_path):
    '''
    Function to extract the data stored for a given collection as xml
    @returns the values stored in the xml file for title, synopsis, language,
    wl, loc, region, country, continent, access, depositor, contact
    '''
    try:
        with open(xml_path, 'r', encoding='utf-8') as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()
                
            title = root.find('Title')
            title = title.text if title is not None else ''
                                    
            synopsis = root.find('ProjectDescription').text
            synopsis = synopsis if synopsis is not None else ''
                
            #if no languages are specified, we add Tsuut'ina as the default
            language = root.find('VernacularISO3CodeAndName')
            if language is not None:
                code, _ = language.text.split(':')
                language, created = Language.objects.get_or_create(name=code.strip())

            else:
                language, created = Language.objects.get_or_create(name="srs")
                
                    
            #if no working languages are specified, we add English as the default
            wl = root.find('AnalysisISO3CodeAndName')
            if wl is not None:
                code, _ = wl.text.split(':')
                wl, created = Language.objects.get_or_create(name=code.strip())
            
            else:
                wl, created = Language.objects.get_or_create(name="eng")

            loc = root.find('Location')
            loc = loc.text if loc is not None else ''
                
            region = root.find('Region')
            region = region.text if region is not None else ''
                
            country = root.find('Country')
            country = country.text if country is not None else ''

            continent = root.find('Continent')
            continent = continent.text if continent is not None else ''
                
            access = root.find('AccessProtocol')
            access = access.text if access is not None else ''
                    
            depositor = root.find('Depositor')
            if depositor is not None:
                depositor, created = Person.objects.get_or_create(name=depositor.text, role="depositor")
                    
            else: 
                depositor, created = Person.objects.get_or_create(name="Unspecified")
                    
            contact = root.find('ContactPerson')
            if contact is not None:
                contact, created = Person.objects.get_or_create(name=contact.text, role="contact")
                    
            else: 
                contact, created = Person.objects.get_or_create(name="Unspecified")
                    
            return title, synopsis, language, wl, loc, region, country, continent, access, depositor, contact
                        
    except Exception as e:
        print(f"Error parsing XML: {e}")

def populate_models_from_directory(collection_path):
    '''
    Finds all collections in a given path and creates an instance for each
    of those collections
    Calls recursively the methods to populate session and people models
    '''
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
        
        print(f"Collection: {title} successfully created")
    
        # Recursively process Session and People directories
        process_sessions(collection, os.path.join(collection_dir, 'Sessions'))
        process_people(os.path.join(collection_dir, 'People'))
        

def parse_xml_person(xml_path):
    '''
    Function to extract the data stored for a given person as xml
    @returns the values stored in the xml file for name and nickname
    '''
    try:
        with open(xml_path, 'r', encoding='utf-8') as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            name = root.find('name')
            name = name.text if name is not None else ''
            
            nickname = root.find('nickName')
            nickname = nickname.text if nickname is not None else ''
            
        return name, nickname
    
    except Exception as e:
        print(f"Error parsing XML: {e}")
       

def parse_xml_session(xml_path):
    '''
    Function to extract the data stored for a given collection as xml
    @returns the values stored in the xml file for title, langlist, 
    wllist, genre, subgenre, synopsis, date, speakerlist, participantlist
    '''
    try:
        with open(xml_path, 'r', encoding='utf-8') as xml_file:
            tree = ET.parse(xml_file)
            root = tree.getroot()
                
            title = root.find('title')
            title = title.text if title is not None else ''
                
            #if no languages are specified, we add English and Tsuut'ina as the default
            languages = root.find('languages')
            langlist = []
            if languages is not None:
                if len(languages.text) > 3:
                    lang = []
                    lang = languages.text.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        langlist.append(l)
                else:
                    lang, created = Language.objects.get_or_create(name=languages.text)
                    langlist.append(lang)
            else:
                eng, created = Language.objects.get_or_create(name="eng")
                tsuu, created = Language.objects.get_or_create(name="srs")
                langlist.append(eng)
                langlist.append(tsuu)
                    

            working_languages = root.find('workingLanguages')
            wllist = []
            if working_languages is not None:
                if len(working_languages.text) > 3:
                    lang = []
                    lang = working_languages.text.split(';')
                    for l in lang:
                        l, created = Language.objects.get_or_create(name=l)
                        wllist.append(l)
                else:
                    lang, created = Language.objects.get_or_create(name=working_languages.text)
                    wllist.append(lang)
            else:
                    eng, created = Language.objects.get_or_create(name="eng")
                    tsuu, created = Language.objects.get_or_create(name="srs")
                    wllist.append(eng)
                    wllist.append(tsuu)

            genre = root.find('genre')
            if genre is not None:
                genre, created = Genre.objects.get_or_create(name=genre.text)
            else:
                genre, created = Genre.objects.get_or_create(name="Unclassified")
                    
            subgenre = root.find('Sub-Genre')
            if subgenre is not None:
                subgenre, created = Genre.objects.get_or_create(name=subgenre.text, parent_genre=genre)
            else:
                subgenre, created = Genre.objects.get_or_create(name="Unclassified", parent_genre=genre)
                    
            synopsis = root.find('synopsis')
            synopsis = synopsis.text if synopsis is not None else ''
                
            date = root.find('date')
            date = date.text if date is not None else ''
                
            contributors = root.find('contributions')
            speakerlist = []
            participantlist = []
            if contributors is not None:
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
 
def process_people(people_dir):
    '''
    Finds all people in a given path and creates an instance for each
    of those people
    '''
    for person_name in os.listdir(people_dir):
        person_path = os.path.join(people_dir, person_name)
        if os.path.isdir(person_path):
            # Find the Person XML file and parse its content
            person_xml_file = os.path.join(person_path, f'{person_name}.person')
            name, nickname = parse_xml_person(person_xml_file)
            
            if nickname:
                # Update people models
                models = Person.objects.filter(name=name)

                for p in models:
                    p.tier = nickname
                
                    p.save()
            

def process_sessions(collection, session_dir):
    '''
    Finds all sessions in a given path and creates an instance for each
    of those sessions
    Calls recursively the methods to populate the file model
    '''
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
    '''
    Finds all files in a given path and creates an instance for each
    of those files
    Calls recursively the methods to populate TranscriptELAN models
    '''
    
    for file_name in os.listdir(session_path):
        file_path = os.path.join(session_path, file_name)
        
        if os.path.isfile(file_path):

            # Check if the file is not a session or meta file
            if not file_name.endswith(('.session', '.meta', '.log', '.pfsx')):
                
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
                    
                if file_name.endswith('.eaf'):
                    # Extract tiers
                    process_elan_text(file_obj, file_path)

def store_tier_values(tier, vid, file, postp):
    '''
    Finds all annotations in the tiers spoken by a given speaker and 
    creates an instance for each one of them
    '''
    for ann in tier:                
        annotationID = ann.ID.rjust(4, ' ')
        annotation = ann.text
        textType = tier.type_ref.ID
        startTime = ann.from_ts
        endTime = ann.to_ts                

        annotation, created = TranscriptELAN.objects.get_or_create(
            annotationID=annotationID,
            startTime=startTime,
            endTime=endTime, 
            annotation=annotation,
            transcriptELANfile=file,
            textType=textType,
            video=vid
        )
        
        annotation.save()
            
        #see if there is any postprocess needed
        for i in range(0,len(postp)):
            if postp[i][0].overlap(ann) > 0:
                annotation.postprocess.add(postp[i][1])

def get_postprocess_tier(tier, file):
    '''
    Finds all annotations in the postprocesstier and creates an instance
    for each one of them
    @returns a list of tuples with the annotation and its instance in
    the database
    '''
    postprocess = []
    
    for ann in tier:
        annotationID = ann.ID.rjust(4, ' ')
        startTime = ann.from_ts
        endTime = ann.to_ts
        text = ann.text
            
        # Create or update the Postprocess model
        postp, created = Postprocess.objects.get_or_create(
            annotationID=annotationID,
            startTime=startTime,
            endTime=endTime, 
            annotation=text,
            transcriptELANfile=file
        )
        
        postp.save()

        postprocess.append((ann, postp))
    
    return postprocess

                    
def process_elan_text(file, file_path):
    '''
    Populates the model TranscriptElan based on information of a given
    .eaf file
    '''
    speakers = list(file.session.speakers.values_list('tier', flat=True))
    eaf = elan.read_eaf(file_path)
    
    #retrieve name of linked multimedia
    vid_path = eaf.media_path()
    vid_name, vid_type = os.path.splitext(os.path.basename(vid_path))
    vid_type = vid_type.lstrip('.').lower()
    
    # If not yet uploaded, upload the file content to the database
    with open(vid_path, 'rb') as file_content:
        vid = File(
        name=vid_name,
        type=vid_type,
        session=file.session,
        )
        vid.content.save(vid_name, DjangoFile(file_content))

        # Save the file object
        vid.save()
                    
    
    for tier in eaf:
        if tier.ID == "Postprocess":
            pp_anns = get_postprocess_tier(tier, file)
    
    for tier in eaf:
        if tier.participant in speakers:
            store_tier_values(tier, vid, file, pp_anns)


# Usage

collection_path = r'c:\Users\Lorena\Desktop\COLLECTIONS'

try:
    with transaction.atomic():
        # Call the function to delete all data
        delete_all_data()
        populate_models_from_directory(collection_path)

        for tier_reference in tier_references:
            # Check if the file with the name exists in the new collections or files
            if Collection.objects.filter(name=tier_reference.collection.name).exists() \
                or File.objects.filter(name=tier_reference.transcriptELANfile.name).exists():
                TierReference.objects.create(**tier_reference.__dict__)
                print("TierReference successfully recreated")
                
    #compute_search_vector:
    searchv = SearchVector('annotation')
    TranscriptELAN.objects.update(search_vector=searchv)

except Exception as e:
    print(f"Error during data population: {e}")

