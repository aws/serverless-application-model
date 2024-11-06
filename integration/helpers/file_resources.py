FILE_TO_S3_URI_MAP = {
    "code.zip": {"type": "s3", "uri": ""},
    "code2.zip": {"type": "s3", "uri": ""},
    "layer1.zip": {"type": "s3", "uri": ""},
    "layer2.zip": {"type": "s3", "uri": ""},
    "swagger1.json": {"type": "s3", "uri": ""},
    "swagger2.json": {"type": "s3", "uri": ""},
    "binary-media.zip": {"type": "s3", "uri": ""},
    "template.yaml": {"type": "http", "uri": ""},
    "MTLSCert.pem": {"type": "s3", "uri": ""},
    "MTLSCert-Updated.pem": {"type": "s3", "uri": ""},
}

CODE_KEY_TO_FILE_MAP = {
    "codeuri": "code.zip",
    "contenturi": "layer1.zip",
    "definitionuri": "swagger1.json",
    "templateurl": "template.yaml",
    "binaryMediaCodeUri": "binary-media.zip",
    "mtlsuri": "MTLSCert.pem",
}
