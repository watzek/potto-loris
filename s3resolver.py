# -*- coding: utf-8 -*-
"""
`s3resolver` -- Resolver for images coming from an AWS S3 bucket.
==============================================================
"""

from os.path import join, exists
from urlparse import urlparse
from urllib import unquote
import logging
import boto3
import botocore

from loris.resolver import _AbstractResolver
from loris.loris_exception import ResolverException, ConfigError
from loris.img_info import ImageInfo

logger = logging.getLogger('webapp')

class S3Resolver(_AbstractResolver):
    '''
    Resolver for images stored in an Amazon Web Services S3 bucket. The first
    call to `resolve()` copies the source image into a local cache; subsequent
    calls use local copy from the cache.

    The config dictionary MUST contain
     * `source_root`, the root directory for source images.

    The config dictionary MAY contain
     * `cache_root`, which is the absolute path to the directory where images
        should be cached. Will default to /cache in the loris app directory.
    '''
    def __init__(self, config):
        super(S3Resolver, self).__init__(config)

        if 'cache_root' in self.config:
            self.cache_root = self.config['cache_root']
        else:
            message = 'Configuration error: Missing setting for cache_root.'
            logger.error(message)
            raise ConfigError(message)

        if 'source_root' in self.config:
            self.source_root = self.config['source_root']
        else:
            message = 'Configuration error: Missing setting for source_root.'
            logger.error(message)
            raise ConfigError(message)

        urlparts = urlparse(self.source_root)
        self.s3_bucket = urlparts.netloc
        self.prefix = urlparts.path

        if not urlparts.scheme == 's3':
            message = 'Configuration error: source_root is not an s3:// url.'
            logger.error(message)
            raise ConfigError(message)

    def s3_key_name(self, ident):
        '''Get the s3 key name of an image.'''
        ident = unquote(ident)
        return '{0}{1}'.format(self.prefix, ident)

    def cache_file_path(self, ident):
        '''Get the filename of a cached image.'''
        ident = unquote(ident)
        return join(self.cache_root, ident)

    def in_cache(self, ident):
        '''Check if a file is already in the cache.'''
        return exists(self.cache_file_path(ident))

    def copy_to_cache(self, ident):
        '''Download the image to the cache.'''
        s3_key_name = self.s3_key_name(ident)
        cache_file_path = self.cache_file_path(ident)
        try:
            s3 = boto3.resource('s3')
            s3.Bucket(self.s3_bucket).download_file(s3_key_name, cache_file_path)
            logger.info('Downloaded key %s at: %s.', s3_key_name, cache_file_path)
            return cache_file_path
        except botocore.exceptions.ClientError as e:
            logger.error(e)
            raise

    def raise_404_for_ident(self, ident):
        '''Log the failure and throw a 404.'''
        s3_key_name = self.s3_key_name(ident)
        logger.warn(
            'Key %s not found in bucket: %s.',
            s3_key_name,
            self.s3_bucket
        )
        raise ResolverException('Key %s not found.' % s3_key_name)

    def is_resolvable(self, ident):
        '''Check if the image is in the cache or available in the s3 bucket.'''
        if self.in_cache(ident):
            return True
        else:
            s3_key_name = self.s3_key_name(ident)
            try:
                s3 = boto3.resource('s3')
                s3.Bucket(self.s3_bucket).Object(s3_key_name).load()
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == '404':
                    self.raise_404_for_ident(ident)
                else:
                    logger.error(e)
                    raise
            else:
                return True

    def resolve(self, app, ident, base_uri):
        '''Return information about the image, caching it if needed.'''
        if not self.is_resolvable(ident):
            self.raise_404_for_ident(ident)
        if not self.in_cache(ident):
            self.copy_to_cache(ident)
        cache_file_path = self.cache_file_path(ident)
        format_ = self.format_from_ident(ident)
        uri = self.fix_base_uri(base_uri)
        extra = self.get_extra_info(ident, cache_file_path)
        return ImageInfo(app, uri, cache_file_path, format_, extra)
