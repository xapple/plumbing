#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Written by Lucas Sinclair.
MIT Licensed.
Contact at www.sinclair.bio
"""

# Built-in modules #

# Internal modules #

# First party modules #
from autopaths.file_path import FilePath

################################################################################
def check_blocked_request(tree):
    """
    Check if the request was denied by the server.
    And raise an exception if it was.
    """
    # Modules #
    from lxml import etree
    # Did we get a filepath? #
    if isinstance(tree, FilePath):
        if tree.count_bytes > 1000000: return
        tree = tree.contents
    # Did we get a tree or raw text? #
    if isinstance(tree, str): tree = etree.HTML(tree)
    # By default we are good #
    blocked = False
    # Try Incapsula #
    blocked = blocked or check_incapsula(tree)
    # If we were indeed blocked, we can stop here #
    if blocked: raise Exception("The request was flagged and blocked by the server.")

################################################################################
def check_incapsula(tree):
    # By default we are good #
    blocked = False
    # Result type 1 from Incapsula #
    meta = tree.xpath("//head/meta[@name='ROBOTS']")
    if meta and 'NOINDEX' in meta[0].get('content'): blocked = True
    # Result type 2 from Incapsula #
    meta = tree.xpath("//head/meta[@name='robots']")
    if meta and 'noindex' in meta[0].get('content'): blocked = True
    # If we were indeed blocked, we can stop here #
    return blocked