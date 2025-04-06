import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

"""
File upload service module.

This module provides the `UploadFileService` class for managing file uploads 
to Cloudinary. It includes functionality for configuring Cloudinary and 
uploading files with specific transformations.

Classes:
    UploadFileService: A service class for uploading files to Cloudinary.
"""


class UploadFileService:
    """
    A service class for uploading files to Cloudinary.

    This class provides methods for configuring Cloudinary and uploading files
    with specific transformations.

    Attributes:
        cloud_name (str): The Cloudinary cloud name.
        api_key (str): The Cloudinary API key.
        api_secret (str): The Cloudinary API secret.
    """

    def __init__(self, cloud_name: str, api_key: str, api_secret: str):
        """
        Initializes the UploadFileService with Cloudinary configuration.

        Args:
            cloud_name (str): The Cloudinary cloud name.
            api_key (str): The Cloudinary API key.
            api_secret (str): The Cloudinary API secret.
        """
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    @staticmethod
    def upload_file(file: UploadFile, username: str) -> str:
        """
        Uploads a file to Cloudinary with specific transformations.

        Args:
            file (UploadFile): The file to upload (from FastAPI).
            username (str): The username to associate with the uploaded file.

        Returns:
            str: The URL of the uploaded file with transformations applied.
        """
        public_id = f"RestApp/{username}"
        r = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
        src_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=250, height=250, crop="fill", version=r.get("version")
        )
        return src_url
