# config.py

DEFAULT_BRAND = 'KR4ML'

BRANDING_PROFILES = {
    'WM7X': {
        'logo_path': 'images/WM7XLogo.png',
        'callsign': 'WM7X',
        'site_name': 'WM7X Exam Results',
        'subtitle': 'For convenience only, not part of ExamTools.org',
        'favicons': [
            {'size': '32x32', 'href': 'https://wm7x.net/wp-content/uploads/2022/10/cropped-Site-Icon-32x32.png'},
            {'size': '192x192', 'href': 'https://wm7x.net/wp-content/uploads/2022/10/cropped-Site-Icon-192x192.png'},
            {'size': '180x180', 'href': 'https://wm7x.net/wp-content/uploads/2022/10/cropped-Site-Icon-180x180.png'},
            {'size': '270x270', 'href': 'https://wm7x.net/wp-content/uploads/2022/10/cropped-Site-Icon-270x270.png'}
        ]
    },
    'KR4ML': {
        'logo_path': 'images/KR4ML/KR4MLLogo.jpg',
        'callsign': 'KR4ML',
        'site_name': 'KR4ML Exam Results',
        'subtitle': 'For convenience only, not part of ExamTools.org',
        'favicons': [
            {'size': '32x32', 'href': '/static/images/KR4ML/favicon-32x32.png'},
            {'size': '192x192', 'href': '/static/images/KR4ML/favicon-192x192.png'},
            {'size': '180x180', 'href': '/static/images/KR4ML/apple-touch-icon.png'},
            {'size': '270x270', 'href': '/static/images/KR4ML/mstile-270x270.png'}
        ]
    }
}