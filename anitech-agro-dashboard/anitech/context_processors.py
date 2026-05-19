from .utils import get_current_lang


def language_context(request):
    lang = get_current_lang(request)
    return {
        'lang': lang,
        'language_name': 'Tagalog' if lang == 'tl' else 'English',
    }
