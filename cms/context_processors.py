from django.core.cache import cache
import os
# from users.models import Users

def global_context(request): 
    # if request.user.is_authenticated:
    #     cache_key = f"user_permissions_{request.user.id}"
    #     permission_list = cache.get(cache_key)

    #     if permission_list is None and not request.user.is_superuser:
    #         user_profile = Users.objects.get(user=request.user)
    #         permissions = request.user.get_all_permissions()
    #         permission_list = {
    #             'view_contacts': 'contacts.view_contact' in permissions,
    #             'view_galleries': 'galleries.view_gallery' in permissions,
    #             'view_pages': 'pages.view_page' in permissions,
    #             'view_postcategories': 'post_categories.view_postcategory' in permissions,
    #             'view_posts': 'posts.view_post' in permissions,
    #             'view_productcategories': 'product_categories.view_productcategory' in permissions,
    #             'view_products': 'products.view_product' in permissions,
    #             'view_users': 'users.view_users' in permissions,
    #             'view_roles': 'users.view_roles' in permissions,
    #         }
    #         cache.set(cache_key, permission_list, timeout=60 * 10)  # Cache for 10 minutes
    #         print("permission_list: ", permission_list)
    #     else:
    #         user_profile = Users.objects.get(user=request.user)
            
    #     return {
    #         'user_profile': user_profile,
    #         'permission_list': permission_list,
    #         'is_superuser': request.user.is_superuser,
    #         'url': os.getenv("R2_URL", ""), 
    #     }
    return {}
