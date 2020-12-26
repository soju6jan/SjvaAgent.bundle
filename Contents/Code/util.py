# -*- coding: utf-8 -*-
import urllib
import os
import re

class Util:
    @staticmethod
    def change_html(text):
        return text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#35;', '#').replace('&#39;', "‘")
