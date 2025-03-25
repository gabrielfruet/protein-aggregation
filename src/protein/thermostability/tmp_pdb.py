import tempfile


def receive_pdb_content_instead_of_path(function_that_receives_pdb_filepath):
    def function_that_receives_pdb_string(pdb_content, *args, **kwargs):
        result = None
        with tempfile.NamedTemporaryFile(mode="w", delete=True, suffix=".pdb") as tmp:
            tmp.write(pdb_content)
            tmp.flush()
            file_path = tmp.name
            result = function_that_receives_pdb_filepath(file_path, *args, **kwargs)

        return result

    return function_that_receives_pdb_string
