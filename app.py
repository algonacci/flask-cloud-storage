import logging
import os
from typing import Union

from flask import Flask, request
from google.cloud import storage
from google.oauth2 import service_account

app = Flask(__name__)

# Configure this environment variable via app.yaml
# CLOUD_STORAGE_BUCKET = os.environ['CLOUD_STORAGE_BUCKET']
CLOUD_STORAGE_BUCKET = 'flask-cloud-storage'
credentials = service_account.Credentials.from_service_account_file("credentials.json")


@app.route('/')
def index() -> str:
    return """
<form method="POST" action="/upload" enctype="multipart/form-data">
    <input type="file" name="file">
    <input type="submit">
</form>
"""


@app.route('/upload', methods=['POST'])
def upload() -> str:
    """Process the uploaded file and upload it to Google Cloud Storage."""
    uploaded_file = request.files.get('file')

    if not uploaded_file:
        return 'No file uploaded.', 400

    # Create a Cloud Storage client.
    gcs = storage.Client(credentials=credentials)

    # Get the bucket that the file will be uploaded to.
    bucket = gcs.get_bucket(CLOUD_STORAGE_BUCKET)

    # Create a new blob and upload the file's content.
    blob = bucket.blob(uploaded_file.filename)

    blob.upload_from_string(
        uploaded_file.read(),
        content_type=uploaded_file.content_type
    )

    # Make the blob public. This is not necessary if the
    # entire bucket is public.
    # See https://cloud.google.com/storage/docs/access-control/making-data-public.
    blob.make_public()

    # The public URL can be used to directly access the uploaded file via HTTP.
    return blob.public_url


@app.errorhandler(500)
def server_error(e: Union[Exception, int]) -> str:
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
