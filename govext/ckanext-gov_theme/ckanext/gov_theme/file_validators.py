# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import logging
import ckan.logic as logic
from ckan.common import config, _
import re

from messytables import CSVTableSet, type_guess, \
  types_processor, headers_guess, headers_processor, \
  offset_processor, any_tableset

log = logging.getLogger(__name__)

def check_file_extension(file_name):
    log.info('upload: checking file * %s * extension ', file_name)
    file_extensions = config.get('ckan.upload.file_extensions', '').lower()
    name, ext = os.path.splitext(file_name)
    # check if not empty first
    if len(ext[1:]) > 0:
        if ext[1:].lower() not in file_extensions:
            log.error("upload: the file * %s * was not uploaded - File extension * %s *  is not allowed", file_name, ext[1:].lower())
            raise logic.ValidationError(
                {'upload': ['File extension is not allowed']}
            )
    else:
        log.error("upload: the file * %s * was not uploaded - File extension is empty", file_name)
        raise logic.ValidationError(
            {'upload': ['File extension is empty']}
        )

def rollback_tmp(file_tmp, tmp_filepath):
    file_tmp.close()
    os.remove(tmp_filepath)

def validate_file(file_tmp, file_name, tmp_filepath):

    log.info("upload: checking file * %s * ", file_name)
    MAX_HEADER_LENGTH = 64
    # not allowed characters ( - ' " ’ ‘) regex
    inappropriate_chars = re.compile(r"[\-|\'|\"|\u2018|\u2019]");
    datastore_ext = config.get('ckan.mimetype_guess', "csv xls xlsx tsv")
    tmp_file_name, tmp_file_ext = os.path.splitext(file_name)

    tmp_file_ext_str = tmp_file_ext[1:].lower()
    #check if datastore file (csv xls xlsx tsv)
    if tmp_file_ext_str in datastore_ext:
        try:
            table_set = any_tableset(file_tmp)
        except:
            log.info("file is not valid * %s * ", file_name)
            raise logic.ValidationError( {'upload': ['The file is not valid']})
        #check if only one data sheet in the file
        if len(table_set.tables)>1:
            rollback_tmp(file_tmp, tmp_filepath)
            log.error("upload: the file * %s * was not uploaded - There is more then one data sheet in the file", file_name)
            raise logic.ValidationError(
                {'upload': [_('There is more then one data sheet in the file')]}
            )
        #check if table_set is not empty
        elif len(table_set.tables) > 0:
            row_set = table_set.tables[0]
            # guess header names and the offset of the header:
            offset, headers = headers_guess(row_set.sample)
            row_set.register_processor(headers_processor(headers))
            for header in headers:
                # too long header
                if len(header) > MAX_HEADER_LENGTH:
                    rollback_tmp(file_tmp, tmp_filepath)
                    log.error("upload: the file * %s * was not uploaded - too long header - * %s *",
                              file_name, header)
                    raise logic.ValidationError(
                        {'upload': [_('too long header (64 max)')]}
                    )
                # not allowed characters in header ( - ' " ’ ‘)
                #if inappropriate_chars.search(header):
                #    rollback_tmp(file_tmp, tmp_filepath)
                #    log.error("upload: the file * %s * was not uploaded - there are inappropriate characters in headers * %s *",
                #              file_name, header)
                #    raise logic.ValidationError(
                #        {'upload': [_('there are inappropriate characters in headers (apostrophe/apostrophes/dash)')]}
                #    )
            # Check for duplicate fields
            unique_fields = set(headers)
            if not len(unique_fields) == len(headers):
                rollback_tmp(file_tmp, tmp_filepath)
                log.error("upload: the file * %s * was not uploaded - Duplicate column names are not supported", file_name)
                raise logic.ValidationError({'upload': [_('Duplicate column names are not supported')]})

            log.info("passed validation succesfully - the file * %s * was uploaded to CKAN (filestore)", file_name)
        else:
            log.info("no table_set was created by messytables - skip headers validations in the file * %s * ", file_name)

    else:
        pass




