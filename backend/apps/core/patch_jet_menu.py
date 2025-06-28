# from jet.utils import get_menu_items as original_get_menu_items

# def patched_get_menu_items(request):
#     menu = original_get_menu_items(request)
#     for app in menu:
#         if 'items' not in app:
#             app['items'] = []
#     return menua