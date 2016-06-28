from django.conf import settings
from django.conf.urls import url
from django.contrib.staticfiles import finders
from django.http.response import HttpResponse
from closure.tracker import analyze_modules
from pathlib import Path
import logging
import io
import json
import os

log = logging.getLogger(__name__)

PATHS_URL = "/closure/paths.js"

def load_closure_config():
    '''
    Load the JSON closure config from the file given in the
    ``CLOSURE_CONFIG`` setting or from ``closure-cofnig.js``,
    ``CLOSURE_CONFIG`` is not present in the configuration.
    
    :return: The parsed JSON object from the closure-util JSON input file. 
    '''
    
    configfile = getattr(settings,"CLOSURE_CONFIG","closure-config.json")
    
    absfile = finders.find(configfile)
    
    with io.open(absfile) as fh:
        return os.path.dirname(absfile),json.load(fh)
    
base_modules = []
'''
  A list of module URLs, which are known incarnations of google closure's
  ``base.js`` to be included in debug HTML files.
'''

base_module = None
'''
  The first module URL, which is a known incarnation of google closure's
  ``base.js`` to be included in debug HTML files.
'''

entry_points = []
'''
  A list of module URLs, which are providing the configured ``closure_entry_point``
  module to be included in debug HTML files.
'''

entry_point = None
'''
  The first module URLs, which is providing the configured ``closure_entry_point``
  module to be included in debug HTML files.
'''

module_files = {}
'''
  A map from moduel URLs to tuples with the list of provided modules first
  and required modules second.
'''

main_js_urls = []
'''
  A list of main javascript URLs to be included into debug HTML files.
'''

def closure_paths():
    '''
    Register a view under ``/closure/paths.js``, which return a closure
    dependency file consisting of ``goog.addDependency()`` calls representing
    the dependencies found in the javascript files refernced by the closure-util
    JSON config in the section ``lib``.
    
    Calling this method also fills the module variables ``base_modules``, ``base_module``,
    ``entry_points``, ``entry_point``, ``module_files`` and ````
    
    :return: An array with a single URL configuration, if django has been configured
             in debug mode. In production mode, an empty array is returned.
    '''
    
    if not settings.DEBUG:
        return []
    
    rootdir,config = load_closure_config()
    
    libs = config["lib"]
    compile_opt = config.get("compile")
    
    entry_point_module = compile_opt.get("closure_entry_point") if compile_opt else None
    
    rootpath = Path(rootdir)
    
    for libfile in libs + ["node_modules/closure-util/.deps/library/*/closure/**/*.js"]:
        
        log.info("Scanning javascript files in [%s] under [%s]."%(libfile,rootpath))
        
        for file in rootpath.glob(libfile):
            with file.open(encoding='utf-8') as fh:
                
                relpath = file.relative_to(rootpath)
                
                my_url = settings.STATIC_URL + str(relpath)

                if not my_url in module_files:
                    
                    try:
                        modules,requirements,isbase = analyze_modules(fh.read())
                        
                        if isbase:
                            
                            if len(base_modules) == 0:
                                log.info("closure's base.js found under [%s]."%my_url)
                                base_module = my_url
                            else:
                                log.warn("Additional closure's base.js found under [%s], this file will be ignored."%my_url)
                            
                            base_modules.append(my_url)
                        
                        if entry_point_module and entry_point_module in modules:
                            if len(entry_points) == 0:
                                log.info("Entry point [%s] found under [%s]."%(entry_point_module,my_url))
                                entry_point = my_url
                            else:
                                log.warn("Entry point [%s] also found under [%s], this file will be ignored."%(entry_point_module,my_url))
                            
                            entry_points.append(my_url)
                            
                        module_files[my_url] = (modules,requirements)
                    
                    except Exception as e:
                        log.warn("Ignoring file [%s] with javascript parse error: %s"%(file,e))
    
    main_js_urls = []

    if len(base_modules) == 0:
        log.warn("closure's base.js not found, expect any sort of problems.")
    else:
        main_js_urls.append(base_module)
    
    main_js_urls.append(PATHS_URL)
    
    if entry_point_module and len(entry_points) == 0:
        log.warn("Entry point [%s] not found, expect any sort of problems.")
    else:
        main_js_urls.append(entry_point)

    log.info("Main debug URLs are %s"%main_js_urls)

    def paths_view(request, path):
        
        with io.StringIO("// This file was autogenerated by django-closure.\n// Please do not edit.\n") as out:
            
            for my_url in sorted(module_files):
                
                modules,requirements = module_files[my_url]
                
                if modules or requirements:
                    out.write("goog.addDependency(%s,%s,%s)\n",json.dumps(my_url),json.dumps(modules),json.dumps(requirements))
            
            response = HttpResponse(out.getvalue(),content_type="application/javascript",charset='utf-8')
            response["Cache-Control"] = "no-cache"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

            return response
    
    return [ url("^"+PATHS_URL[1:],paths_view) ]
