// (c) The redundant industries for redundant stuff.
/*
   This file is brought to you by the redundancy department
   as javascript parsing example only.
 */

goog.provide("redundant.stuff");
goog.provide("redundant.stuff.Foo");

goog.require("redundant.stuff.Baz");
goog.require("redundant.stuff.Bar");

redundant.stuff.bar = function() {
	goog.provide("not_possible");
	return "bar";
};

redundant.stuff.Foo = function(a,b) {
	goog.require("not_possible");
	this.a = a;
	this.b = b;
}
