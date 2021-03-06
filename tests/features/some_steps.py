from lettuce import *
import importlib

@step('I have the package name (\S+)')
def i_have_the_package_name(step, package_name):
  world.package_name = package_name
  assert world.package_name is not None, \
    "Got package_name %s" % world.package_name

@step('I import the package')
def i_import_the_package(step):
  imported = None
  try:
    world.package = importlib.import_module(world.package_name)
    imported = True
  except:
    imported = False
  assert imported is True, \
    "Package %s was imported" % world.package_name

@step('I get the package with name (\S+)')
def i_get_the_package_with_name(step, package_name):
  assert world.package.__name__ == package_name, \
    "Got package_name %s" % world.package.__name__
  
@step('I see the string (.*)')
def i_see_the_string(step, string):
    # Remove new lines for when comparing
    if type(world.string) == unicode or type(world.string) == str:
        world.string = world.string.replace("\n", "\\n")
    # Convert our value to int if world string is int for comparison
    if type(world.string) == int:
        string = int(string)
        
    if string == "None":
        string = None
    if string == "True":
        string = True
    if string == "False":
        string = False
        
    assert world.string == string, "Got %s" % world.string