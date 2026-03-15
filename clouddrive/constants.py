PREVIEWABLE_TYPES = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'webp': 'image/webp',
    'svg': 'image/svg+xml',
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'md': 'text/markdown',
    'json': 'application/json',
    'js': 'text/javascript',
    'ts': 'text/typescript',
    'py': 'text/x-python',
    'html': 'text/html',
    'css': 'text/css',
    'xml': 'application/xml',
    'yaml': 'application/x-yaml',
    'sh': 'text/x-shellscript',
    'yml': 'application/x-yaml',
}

PREVIEWABLE_EXTS = set(PREVIEWABLE_TYPES.keys())
MAX_PREVIEW_SIZE = 10 * 1024 * 1024  # 10MB
