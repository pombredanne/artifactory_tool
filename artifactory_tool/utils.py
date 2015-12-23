__author__ = 'sean-abbott'

import sys
import functools

#from tool.plugins.config import config_get
#import click


def normalize_url(url):
    """ ensure a url is "properly" constructed

    Remove trailing slashes
    Add http if http or https is not specified

    Parameters
    ----------
    url:  string
          A string to return as a url

    """
    if url.endswith('/'):
        url = url[:-1]
    if not url.startswith('http://') and not url.startswith('https://'):
        url = "http://{}".format(url)
    return url


#def rreplace(s, old, new, n=-1):
#  """ Replaces n occurences of old in s with new, starting from right
#  """
#  li = s.rsplit(old, n)
#  return new.join(li)
#
#
#def _user_option(func):
#  return click.option('-u', '--user')(func)
#
#
#def _password_option(func):
#  return click.option('-p', '--password')(func)
#
#
#def _url_arg(func):
#  return click.argument('url')(func)
#
#
#def get_option(opt_name, kwargs, config, default=None):
#  """
#  Returns the resolved value of an option. Resolution order is: cmd line args -> config -> default
#  :param opt_name: Name of the option to resolve
#  :param kwargs: command args
#  :param config: ConfigObj instance
#  :param default: default value
#  :return: Resolved value
#  """
#  opt_short_name = opt_name.split('.')[-1]
#  arg_value = kwargs.get(opt_short_name, None)
#
#  try:
#    config_value = config_get(config, opt_name)
#  except KeyError:
#    config_value = None
#
#  for val in (arg_value, config_value, default):
#    if val is not None:
#      return val
#  raise ValueError('You must either set {} or provide {} via command line.'.format(opt_name, opt_short_name))
#
#
#def common_args(func):
#  func = _user_option(func)
#  func = _password_option(func)
#  func = _url_arg(func)
#  func = click.pass_context(func)
#  return func
#
#
#def handle_errors(errors):
#  if not isinstance(errors, list):
#    errors = [errors]
#
#  def wrap(f):
#    @functools.wraps(f)
#    def wrapped_f(*args, **kwargs):
#      try:
#        return f(*args, **kwargs)
#      except BaseException as e:
#        if type(e) in errors:
#          click.echo(e.message)
#          sys.exit(1)
#        else:
#          raise
#    return wrapped_f
#  return wrap
