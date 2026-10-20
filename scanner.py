import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '/var/www/motionhr')
django.setup()

from django.urls import get_resolver
from django.apps import apps
from django.db import models

print("|||START|||")

def get_all_urls(urllist, prefix=''):
    urls = []
    for entry in urllist:
        if hasattr(entry, 'url_patterns'):
            try: urls.extend(get_all_urls(entry.url_patterns, prefix+str(entry.pattern)))
            except: pass
        else:
            p = str(prefix+str(entry.pattern)).replace('^','').replace('$','')
            cb = getattr(entry, 'callback', None)
            nm = getattr(entry, 'name', '') 
            cl = ""
            mt = "GET"
            if cb:
                if hasattr(cb, 'cls'):
                    cl = cb.cls.__name__
                    acts = cb.actions
                    if acts:
                        ml=[]
                        if 'list' in acts or 'retrieve' in acts: ml.append('GET')
                        if 'create' in acts: ml.append('POST')
                        if 'update' in acts: ml.append('PUT')
                        if 'partial_update' in acts: ml.append('PATCH')
                        if 'destroy' in acts: ml.append('DELETE')
                        mt="/".join(ml)
            if '/admin/' not in p and p != '':
                urls.append(f"{mt} | {p} | {nm} ({cl})")
    return urls

try:
    res=get_resolver()
    u_list=sorted(list(set(get_all_urls(res.url_patterns)))
    print("---API_START---")
    for x in u_list: print(x)
    print("---API_END---")
except Exception as e: print(e)

try:
    models_list = apps.get_models()
    print("---MODEL_START---")
    for m in models_list:
        app=m._meta.app_label; name=m.__name__
        flds=[]; rels=[]
        for f in m._meta.get_fields():
            n=f.name; t=type(f).__name__
            if isinstance(f, models.ForeignKey): rels.append(f"[FK] {n}")
            elif isinstance(f, models.ManyToManyField): rels.append(f"[M2M] {n}")
            elif isinstance(f, models.OneToOneField): rels.append(f"[O2O] {n}")
            else: flds.append(f"{n}:{t}")
        
        print(f"[TABLE] {app}.{name}")
        if flds:
            print("  [COLUMNS]")
            for f in flds: print(f"    . {f}")
        if rels:
            print("  [LINKS]")
            for r in rels: print(f"    >> {r}")
            
    print("---MODEL_END---")
except Exception as e: print(e)

print("|||END|||")