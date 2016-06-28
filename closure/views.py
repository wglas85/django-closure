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
import fcntl
from hashlib import sha256

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
    
def lock_closure_config(exclusive):

    configfile = getattr(settings,"CLOSURE_CONFIG","closure-config.json")
    
    absfile = finders.find(configfile)
    
    fh = io.open(absfile+".lock",mode="w")
    
    try:
        fcntl.lockf(fh,fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
    except:
        fh.close()
        raise
    
    return fh

def open_closure_cache(mode):

    configfile = getattr(settings,"CLOSURE_CONFIG","closure-config.json")
    
    absfile = finders.find(configfile)
    
    return io.open(absfile+".cache",mode=mode)

def get_main_js_urls():
        
    with lock_closure_config(True):
    
        with open_closure_cache("r") as inp:

            state = json.load(inp)
            return state["main_js_urls"]

def closure_paths():
    '''
    Register a view under ``/closure/paths.js``, which return a closure
    dependency file consisting of ``goog.addDependency()`` calls representing
    the dependencies found in the javascript files referenced by the closure-util
    JSON config in the section ``lib``.
    
    Calling this method also fills the module variables ``base_modules``, ``base_module``,
    ``entry_points``, ``entry_point``, ``module_files`` and ````
    
    :return: An array with a single URL configuration, if django has been configured
             in debug mode. In production mode, an empty array is returned.
    '''
    
    if not settings.DEBUG:
        return []
    
    with lock_closure_config(True):
    
        try:
            with open_closure_cache("r") as inp:
                oldstate = json.load(inp)
        except:
            oldstate = None
    
        old_module_files = None if oldstate is None else oldstate.get("module_urls")
        old_base_modules = None if oldstate is None else oldstate.get("base_modules")
    
        base_modules = []
        entry_points = []
        module_files = {}

        rootdir,config = load_closure_config()
        
        libs = config["lib"]
        compile_opt = config.get("compile")
        
        entry_point_module = compile_opt.get("closure_entry_point") if compile_opt else None
        
        rootpath = Path(rootdir)
        
        for libfile in libs + ["node_modules/closure-util/.deps/library/*/closure/goog/base.js"]:
            
            log.info("Scanning javascript files in [%s] under [%s]."%(libfile,rootpath))
            
            for file in rootpath.glob(libfile):

                mtime = file.stat().st_mtime
                relpath = file.relative_to(rootpath)
                my_url = settings.STATIC_URL + str(relpath)

                old_state = None if old_module_files is None else old_module_files.get(my_url)

                if old_state and old_state.get("mtime") == mtime:
                    
                    module_files[my_url] = old_state
                    isbase = old_base_modules and my_url in old_base_modules
                    modules = old_state.get("modules")

                    if isbase:
                        
                        if len(base_modules) == 0:
                            log.info("closure's base.js found under [%s]."%my_url)
                        else:
                            log.warn("Additional closure's base.js found under [%s], this file will be ignored."%my_url)
                        
                        base_modules.append(my_url)
                    
                    if entry_point_module and modules and entry_point_module in modules:
                        if len(entry_points) == 0:
                            log.info("Entry point [%s] found under [%s]."%(entry_point_module,my_url))
                        else:
                            log.warn("Entry point [%s] also found under [%s], this file will be ignored."%(entry_point_module,my_url))
                        
                        entry_points.append(my_url)
                    
                with file.open(encoding='utf-8') as fh:
    
                    if not my_url in module_files:
                        
                        try:
                            
                            javascript = fh.read()
                            checksum = sha256(javascript.encode('utf-8')).hexdigest()
                            
                            modules,requirements,isbase = analyze_modules(javascript)
                            
                            if isbase:
                                
                                if len(base_modules) == 0:
                                    log.info("closure's base.js found under [%s]."%my_url)
                                else:
                                    log.warn("Additional closure's base.js found under [%s], this file will be ignored."%my_url)
                                
                                base_modules.append(my_url)
                            
                            if entry_point_module and entry_point_module in modules:
                                if len(entry_points) == 0:
                                    log.info("Entry point [%s] found under [%s]."%(entry_point_module,my_url))
                                else:
                                    log.warn("Entry point [%s] also found under [%s], this file will be ignored."%(entry_point_module,my_url))
                                
                                entry_points.append(my_url)
                                
                            module_files[my_url] = {"mtime":mtime,"sha256":checksum,"modules":modules,"requirements":requirements}
                        
                        except Exception as e:
                            log.warn("Ignoring file [%s] with javascript parse error: %s"%(file,e))
                            module_files[my_url] = {"mtime":mtime,"sha256":checksum}
        
        main_js_urls = []
    
        if len(base_modules) == 0:
            log.warn("closure's base.js not found, expect any sort of problems.")
        else:
            main_js_urls.append(base_modules[0])
        
        main_js_urls.append(PATHS_URL)
        
        if entry_point_module and len(entry_points) == 0:
            log.warn("Entry point [%s] not found, expect any sort of problems.")
        else:
            main_js_urls.append(entry_points[0])
    
        log.info("Main debug URLs are %s"%main_js_urls)

        cachestate = { "module_urls": module_files, "main_js_urls": main_js_urls, "base_modules": base_modules, "entry_points": entry_points }

        with open_closure_cache("w") as out:
            json.dump(cachestate,out)

    def paths_view(request):
        
        with lock_closure_config(True):
    
            with open_closure_cache("r") as inp:
                
                state = json.load(inp)
                module_files = state["module_urls"]
                base_modules = state["base_modules"]
                
                base_module = base_modules[0]
                depth = base_module.count("/")-1
                relpfx = "../" * depth
                relpfx = relpfx[:-1]
        
                with io.StringIO("// This file was autogenerated by django-closure.\n// Please do not edit.\n") as out:
                    
                    for my_url in sorted(module_files):
                        
                        url_data = module_files[my_url]
                        
                        modules = url_data.get("modules")
                        requirements = url_data.get("requirements")
                        
                        if modules or requirements:
                            out.write("goog.addDependency(%s,%s,%s);\n"%(json.dumps(relpfx+my_url),json.dumps(modules),json.dumps(requirements)))
                    
                    response = HttpResponse(out.getvalue(),content_type="application/javascript",charset='utf-8')
                    response["Cache-Control"] = "no-cache"
                    response["Pragma"] = "no-cache"
                    response["Expires"] = "0"
        
                    return response
    
    return [ url("^"+PATHS_URL[1:],paths_view) ]
