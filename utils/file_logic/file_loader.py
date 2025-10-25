from markitdown import MarkItDown

md = MarkItDown()


def read_file(file_bytes):
    """Load a DOCX, PDF file and convert its content to Markdown format.

    Args:
        file_bytes: .
    """
    return md.convert(file_bytes).markdown
