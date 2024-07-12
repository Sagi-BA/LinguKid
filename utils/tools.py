import os
from io import BytesIO

def save_uploaded_file(uploaded_file, upload_dir="uploads", filename=None):
    """
    Save the uploaded file to the specified directory and return the file path.
    """
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    if filename is None:
        filename = uploaded_file.name

    file_path = os.path.join(upload_dir, filename)
    
    if isinstance(uploaded_file, BytesIO):
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
    else:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    
    return file_path

