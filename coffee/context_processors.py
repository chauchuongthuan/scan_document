from django.core.cache import cache

def category_context(request):
    categories = {
        "parent_categories": [
            {
                "name": "Camera FOFU",
                "slug": "camera-fofu",
                "sub_categories": [
                    {"name": "Bộ KIT Wifi Fofu", "slug": "bo-kit-wifi-fofu"},
                    {"name": "Wifi Thân Ngoài Trời", "slug": "wifi-than-ngoai-troi"},
                    {"name": "Wifi Xoay 360", "slug": "wifi-xoay-360"},
                ],
            },
            {
                "name": "Camera KBVision",
                "slug": "camera-kbvision",
                "sub_categories": [
                    {"name": "Analog CVI /TVI / AHD Kbvision", "slug": "analog-cvi-tvi-ahd-kbvision"},
                    {"name": "Camera KBONE", "slug": "camera-kbone"},
                    {"name": "Camera KBWIN", "slug": "camera-kbvision"},
                    {"name": "IP Camera KBVision", "slug": "ip-camera-kbvision"},
                ],
            },
            {
                "name": "Camera PANASONIC",
                "slug": "camera-panasonic",
            },
            {
                "name": "Camera SAMSUNG",
                "slug": "camera-samsung",
            },
            {
                "name": "Camera UNIARCH",
                "slug": "camera-uniarch",
                "sub_categories": [
                    {"name": "BỘ KIT UNIARCH", "slug": "bo-kit-uniarch"},
                    {"name": "IP Camera UNIARCH", "slug": "ip-camera-uniarch"},
                    {"name": "Switch Uniarch", "slug": "switch-uniarch"},
                    {"name": "Thiết bị hội nghị Uniarch", "slug": "thiet-bi-hoi-nghi-uniarch"},
                ],
            },
            {
                "name": "Camera Vantech",
                "slug": "camera-vantech",
                "sub_categories": [
                    {"name": "AI Camera Vantech", "slug": "ai-camera-vantech"},
                    {"name": "Analog TVI|AHD|CVI Vantech", "slug": "analog-tvi-ahd-cvi-vantech"},
                    {"name": "IP Camera Vantech", "slug": "ip-camera-vantech"},
                ],
            },
            {
                "name": "Camera VIVOTEK",
                "slug": "camera-vivotek",
            },
            {
                "name": "Camera Wifi EBITCAM",
                "slug": "camera-wifi-ebitcam",
            },
            {
                "name": "Camera Wifi EYE",
                "slug": "camera-wifi-eye",
            }

        ]
    }
    return categories

def phukien_context(request):
    phukien = {
        'phukien_categories': [
        {
            "name": "Ổ cứng lưu trữ",
            "slug": "o-cung-luu-tru",
        },
        {
            "name": "Thẻ nhớ",
            "slug": "the-nho",
        },
        {
            "name": "Cáp tín hiệu",
            "slug": "cap-tin-hieu",
        },
        {
            "name": "Nguồn",
            "slug": "nguon",
        },
        {
            "name": "Màn hình",
                "slug": "man-hinh",
            },
        ]
    }
    return phukien

def featured_products_context(request):
    featured_products = {
        'featured_products': [
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
        ]
    }
    return featured_products
def best_products_context(request):
    best_products = {
        'best_products': [
            {
                "name": "DS-2CD1023G0E-IF",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-2.webp",
                "rating": 5,
                "slug": "ds-2cd1023g0e-if"
            },
            {
                "name": "DS-2CD1023G0E-IF",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-2.webp",
                "rating": 5,
                "slug": "ds-2cd1023g0e-if"
            },
            {
                "name": "DS-2CD1023G0E-IF",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-2.webp",
                "rating": 5,
                "slug": "ds-2cd1023g0e-if"
            },
            {
                "name": "DS-2CD1023G0E-IF",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-2.webp",
                "rating": 5,
                "slug": "ds-2cd1023g0e-if"
            },
            {
                "name": "DS-2CD1023G0E-IF",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-2.webp",
                "rating": 5,
                "slug": "ds-2cd1023g0e-if"
            },
        ]
    }
    return best_products
def best_seller_context(request):
    best_seller = {
        'best_seller': [
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
             {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
        ]
    }
    return best_seller
def arrival_context(request):
    arrival = {
        'arrival': [
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
            {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
             {
                "name": "Camera IP Wifi FOFU FF-C3L-720P",
                "category": "Camera",
                "price": "295.000",
                "image": "assets/images/product/sanpham-1.jpg",
                "rating": 5,
                "slug": "camera-ip-wifi-fofu-ff-c3l-720p"
            },
        ]
    }
    return arrival

def global_context(request): 
    if request.user.is_authenticated:
        cache_key = f"user_permissions_{request.user.id}"
        permission_list = cache.get(cache_key)

        if permission_list is None and not request.user.is_superuser:
            permissions = request.user.get_all_permissions()
            permission_list = {
                'view_products': 'products.view_product' in permissions,
            }
            cache.set(cache_key, permission_list, timeout=60 * 10)  # Cache for 10 minutes
            print("permission_list: ", permission_list)
            
        return {
            'permission_list': permission_list,
            'is_superuser': request.user.is_superuser,
            'user_name': request.user.username,
            'user_email': request.user.email
        }
    return {}