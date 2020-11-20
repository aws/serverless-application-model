FILE_TO_S3_URL_MAP = {
    "code.zip": {"type": "s3", "url": ""},
    "layer1.zip": {"type": "s3", "url": ""},
    "swagger1.json": {"type": "s3", "url": ""},
    "swagger2.json": {"type": "s3", "url": ""},
    "template.yaml": {"type": "http", "url": ""},
}

CODE_KEY_TO_FILE_MAP = {
    "codeuri": "code.zip",
    "contenturi": "layer1.zip",
    "definitionuri": "swagger1.json",
    "templateurl": "template.yaml",
}
