#!/usr/bin/env python
# -*- coding: utf-8 -*-
from decimal import getcontext
from os.path import join
import logging
import sys
import os
import platform
import getpass
import grp
from werkzeug.wrappers import Response
from werkzeug.exceptions import InternalServerError

''' subclass loris application for AWS S3 and Elastic Beanstalk '''

getcontext().prec = 25  # Decimal precision. This should be plenty.

this_dir = os.path.dirname(os.path.realpath(__file__))
DIR = os.getenv('APP_WORK', this_dir)

sys.path.append(join(this_dir, 'loris'))

import loris
import loris.webapp

# set up logging http://stackoverflow.com/a/14152283/1763984
handler = logging.StreamHandler(stream=sys.stderr)
log = logging.getLogger('webapp')
log.setLevel(os.getenv('LOG_LEVEL','INFO'))
log.addHandler(handler)

loris.webapp.logger = log

group = grp.getgrgid(os.getgid()).gr_name

log.debug(u'user={0} group={1}'.format(getpass.getuser(), group))
log.debug(u'uid={0} gid={1}'.format(os.getuid(), os.getgid()))

application = loris.webapp.Loris(
    {
        'loris.Loris': {
            'tmp_dp': join(DIR, 'tmp'),
            'www_dp': join(DIR, 'loris', 'www'),
            'enable_caching': True,
            'redirect_canonical_image_request': False,
            'redirect_id_slash_to_info': True
        },
        'logging': {
            'log_to': 'file',
            'log_level': os.getenv('LOG_LEVEL','ERROR'),
            'log_dir': join(DIR, 'log'),
            'max_size': 5242880,
            'max_backups': 5,
            'format': '%(asctime)s (%(name)s) [%(levelname)s]: %(message)s'
        },
        'resolver': {
            'impl': 's3resolver.S3Resolver',
            'cache_root': join(DIR, 'cache'),
            'source_root': os.getenv('SOURCE_ROOT'),
        },
        'img.ImageCache': {
            'cache_dp': join(DIR, 'cache-loris2'),
            'cache_links': join(DIR, 'cache-links')
        },
        'img_info.InfoCache': {
            'cache_dp': join(DIR, 'cache-loris2'),
        },
        'transforms': {
            'dither_bitonal_images': False,
            'target_formats': ['jpg', 'png', 'gif', 'webp'],
            'jpg': {'impl': 'JPG_Transformer'},
            'tif': {'impl': 'TIF_Transformer'},
            'jp2': {
                'impl': 'KakaduJP2Transformer',
                'tmp_dp': join(DIR, 'tmp'),
                'kdu_expand': join(this_dir, 'loris/bin', platform.system(), 'x86_64/kdu_expand'),
                'kdu_libs': join(this_dir, 'loris/lib/Linux/x86_64'),
                'num_threads': '4',
                'mkfifo': '/usr/bin/mkfifo',
                'map_profile_to_srgb': False,
                'srgb_profile_fp': '/usr/share/color/icc/colord/sRGB.icc'
            }
        }
    }
)

def status_check():
    ''' do some sort of health check here '''
    return True

def simple_dissect_uri(request):
    # we can use a much simpler uri dissector that does not have to call
    # `is_resolvable` (testing for existance is an http request for us)
    request_type = 'info'
    if request.path.endswith('default.jpg'):
        request_type = 'image'
    parts = request.path.strip('/').split('/', 1)
    ident = parts[0]
    params = parts[1] if len(parts) == 2 else ''
    return (
      u'{0}{1}'.format(request.host_url, ident),
      ident,
      params,
      request_type,
    )

application._dissect_uri = simple_dissect_uri

# set up for monkeypatch
stock_route = application.route
unwrapped_get_info = application.get_info


def new_route(request):
    ''' monkeypatch the url router for health check '''
    if request.path == "/":
        # "home" page doubles as health check
        if status_check():
            # looks good
            return Response('potto-loris status okay',
                            content_type='text/plain')
        else:
            # looks like things ain't working
            return InternalServerError(
                response=Response('500 potto-loris health check failed',
                                  content_type='text/plain')
            )
    # pass control back to loris router
    return stock_route(request)


def wrapped_get_info(request, ident, base_uri):
    # don't fail silently
    r = unwrapped_get_info(request, ident, base_uri)
    if not r.content_length:
        return InternalServerError('empty json')
    return r

# complete the monkey patch
application.route = new_route
application.get_info = wrapped_get_info


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    httpd = make_server('', 8989, application)
    print "Serving on port 8989..."
    httpd.serve_forever()

"""
Copyright © 2015, Regents of the University of California
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
- Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
- Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
- Neither the name of the University of California nor the names of its
  contributors may be used to endorse or promote products derived from this
  software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
