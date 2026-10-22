import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/var/www/motionhr')
django.setup()

from django.urls import get_resolver
from django.apps import apps
from django.db import models

print("|||START_DEEP_SCAN|||")

# --- PART 1: EXTRACT URLS (APIs) ---
def get_all_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            try:
                urls.extend(get_all_urls(pattern.url_patterns, prefix + str(pattern.pattern)))
            except:
                pass
        else:
            full_path = str(prefix + str(pattern.pattern)).replace('^','').replace('$','').replace('//','/')
            callback = getattr(pattern, 'callback', None)
            view_name = getattr(pattern, 'name', 'N/A') or 'N/A'
            cls_name = ""
            methods = "GET"
            
            if callback:
                if hasattr(callback, 'cls'):
                    cls_name = callback.cls.__name__
                    # Basic method detection for ViewSets
                    actions = callback.actions
                    if actions:
                        m_list = []
                        if 'list' in actions or 'retrieve' in actions: m_list.append('GET')
                        if 'create' in actions: m_list.append('POST')
                        if 'update' in actions: m_list.append('PUT')
                        if 'partial_update' in actions: m_list.append('PATCH')
                        if 'destroy' in actions: m_list.append('DELETE')
                        methods = "/".join(m_list)
            
            # Skip admin/auto URLs to keep list clean
            if 'admin' not in full_path and full_path != '/':
                 urls.append(f"{methods} | {full_path} | {view_name} ({cls_name})")
    return urls

try:
    resolver = get_resolver()
    api_urls = sorted(list(set(get_all_urls(resolver.url_patterns))))
    print("--- APIS_START ---")
    for u in api_urls:
        print(u)
    print("--- APIS_END ---")
except Exception as e:
    print(f"Error extracting APIs: {e}")

# --- PART 2: EXTRACT MODELS & RELATIONS ---
try:
    all_models = apps.get_models()
    print("--- MODELS_START ---")
    
    for model in all_models:
        app_label = model._meta.app_label
        model_name = model.__name__
        
        fields_detail = []
        relations_detail = []
        
        for field in model._meta.get_fields():
            fname = field.name
            ftype = type(field).__name__
            
            if isinstance(field, models.ForeignKey):
                rel_to = field.related_model.__name__
                relations_detail.append(f"[FK] {fname} -> {rel_to}")
            elif isinstance(field, models.ManyToManyField):
                rel_to = field.related_model.__name__
                relations_detail.append(f"[M2M] {fname} <-> {rel_to}")
            elif isinstance(field, models.OneToOneField):
                rel_to = field.related_model.__name__
                relations_detail.append(f"[O2O] {fname} -> {rel_to}")
            else:
                fields_detail.append(f"{fname}: {ftype}")
        
        # Print Model Header
        print(f"[MODEL] {app_label}.{model_name}")
        if fields_detail:
            print(f"  [FIELDS]")
            for f in fields_detail:
                print(f"    - {f}")
        if relations_detail:
            print(f"  [RELATIONS]")
            for r in relations_detail:
                print(f"    - {r}")
                
    print("--- MODELS_END ---")
except Exception as e:
    print(f"Error extracting Models: {e}")

print("|||END_SCAN|||")
python deep_scan.py
