class FileRenaming:
    @staticmethod
    def strip_unwanted_characters(str_to_replace):
        for char in ["\"", "/", ":", "*", "?", "<", ">", "|", '"']:
            if char in str_to_replace:
                str_to_replace = str_to_replace.replace(char, "")
        return str_to_replace