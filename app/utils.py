import re

class Utils:
    @staticmethod
    def escape_solr_text(text):
        if not text:
            return text

        # First clean the text
        text = re.sub(r'[^\w\s\.,;:!?\-\'\"()]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        # Then escape Solr special characters
        text = re.sub(r'([+\-&|!(){}\[\]^"\'~*?:/\\])', r'\\\1', text)

        return text

