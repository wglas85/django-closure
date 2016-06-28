'''
Created on 27. Juni 2016

@author: wglas
'''

from slimit.parser import Parser
from slimit import ast
import logging
import json

log = logging.getLogger(__name__)

def analyze_modules(script):
    '''
    Parses the given javascript file given as a string an returns the
    the provided modules as per ``goog.provide()`` and the required modules
    as per ``goog.require()``.
    
    :param script: The javascript string.
    :return: A tuple with the list of provided modules first,
             the required modules second and a boolean, which is true,
             if the given javascript file is closue 'base.js' file
             declaring ``goog.ENABLE_DEBUG_LOADER``.
    '''
    
    parser = Parser()
    tree = parser.parse(script)
    
    modules = []
    requirements = []
    isbase = False
    
    if isinstance(tree,ast.Program):
        for node in tree:
            
            # filter top-level goog.{provide|require}("foo.bar") statements.
            if (isinstance(node,ast.ExprStatement) and
                isinstance(node.expr,ast.FunctionCall) and
                isinstance(node.expr.identifier,ast.DotAccessor) and
                isinstance(node.expr.identifier.node,ast.Identifier) and
                node.expr.identifier.node.value == "goog" and
                isinstance(node.expr.identifier.identifier,ast.Identifier)
                ):
                
                if  (len(node.expr.args) == 1 and
                     isinstance(node.expr.args[0],ast.String)):
                    if node.expr.identifier.identifier.value == "provide":
                    
                        if log.getEffectiveLevel() <= logging.DEBUG:
                            log.debug("Got expression call %s"%node.to_ecma())
                        
                        module = node.expr.args[0].value[1:-1]
                        
                        if log.getEffectiveLevel() <= logging.DEBUG:
                            log.debug("Module is %s"%module)
                            
                        modules.append(module)
                
                    elif node.expr.identifier.identifier.value == "require":
                        
                        if log.getEffectiveLevel() <= logging.DEBUG:
                            log.debug("Got expression call %s"%node.to_ecma())
                    
                        requirement = node.expr.args[0].value[1:-1]
    
                        if log.getEffectiveLevel() <= logging.DEBUG:
                            log.debug("Requirement is %s"%requirement)
                        
                        requirements.append(requirement)
                # catch goog.define('goog.ENABLE_DEBUG_LOADER', true)
                elif (node.expr.identifier.identifier.value == "define" and
                      len(node.expr.args) == 2 and
                      isinstance(node.expr.args[0],ast.String) and
                      isinstance(node.expr.args[1],ast.Boolean) and
                      node.expr.args[0].value[1:-1] == "goog.ENABLE_DEBUG_LOADER"):
                    
                    if log.getEffectiveLevel() <= logging.DEBUG:
                        log.debug("Got expression call %s"%node.to_ecma())

                    isbase = True
            
    return modules,requirements,isbase
    