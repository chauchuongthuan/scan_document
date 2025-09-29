
# from orders.models import Order
import random
import string
def generate_order_id():
    while True:
        # Tạo mã vé 12 chữ số ngẫu nhiên
        char = string.ascii_uppercase + string.digits
        order_id = ''.join([str(random.choice(char)) for _ in range(12)])
        if not Order.objects.filter(order_id=order_id).exists():
            return order_id

def gennerate_random_string(length=6):
    char = string.ascii_uppercase + string.digits
    return ''.join([str(random.choice(char)) for _ in range(length)])