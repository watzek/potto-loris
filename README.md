# vogel iiif server

vogel is a modified version of [potto](), which is itself an alternative deployment for [loris](https://github.com/loris-imageserver/loris). it is designed to run in [AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/) and serve images stored in [AWS S3](https://aws.amazon.com/s3/) as a [iiif compliant](http://iiif.io/api/image/2.1/) image server.

## Getting Started
### Prerequisites
- [Python 2.7](https://www.python.org/download/releases/2.7/)

### Installing
clone the repository:
```sh
$ git clone https://github.com/watzek/vogel.git
$ cd vogel
```
install dependencies:
```sh
$ pip install -r requirements.txt
```
## Development
coming soon!
## Deployment
### Configuration
ensure that environment variables are set in AWS EB control panel:
- `SOURCE_ROOT` s3:// URL to s3 bucket and prefix where images are stored

optionally, set the following:
- `CACHE_ROOT` default `/cache` in loris app directory
- `LOG_LEVEL` default `INFO` of CRITICAL | ERROR | WARNING | INFO | DEBUG	| NOTSET - output goes to `/var/log/httpd/error_log` which gets shipped by default when you request logs from beanstalk.

### Uploading
check the environment names and versions already in beanstalk:
```sh
$ ./beanstalk-describe.sh
#
# '--version-label's (last 20 version names already used)
# ...
#
# '--environment-names's
# ...
```
you can zip and upload a new version with `deploy-version.sh vX.Y.Z env-name`, e.g.
```sh
$ ./deploy-version.sh v1.6.2 vogel-prod
```
note that you can't deploy on top of an existing version - you need to either delete it from the aws eb console, or bump the version number up.

version zipfiles are stored in the same s3 bucket currently used to serve images (`vogel-iiif`).
## License

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
