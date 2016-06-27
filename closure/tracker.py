'''
Created on 27. Juni 2016

@author: wglas
'''

from slimit.parser import Parser
from slimit import ast
import logging

log = logging.getLogger(__name__)

def analyse_modules(script):
    
    parser = Parser()
    tree = parser.parse(script)
    
    modules = []
    
    if isinstance(tree,ast.Program):
        for node in tree:
            
            # filter top-level goog.provide("foo.bar") statements.
            if (isinstance(node,ast.ExprStatement) and
                isinstance(node.expr,ast.FunctionCall) and
                isinstance(node.expr.identifier,ast.DotAccessor) and
                isinstance(node.expr.identifier.node,ast.Identifier) and
                node.expr.identifier.node.value == "goog" and
                isinstance(node.expr.identifier.identifier,ast.Identifier) and
                node.expr.identifier.identifier.value == "provide" and
                len(node.expr.args) == 1 and
                isinstance(node.expr.args[0],ast.String)
                ):
                
                if log.getEffectiveLevel() <= logging.DEBUG:
                    log.info("Got expression call %s"%node.to_ecma())
                    
                module = node.expr.args[0].value[1:-1]
                log.info("Module is %s"%module)
                modules.append(module)
                
            
    return modules
    