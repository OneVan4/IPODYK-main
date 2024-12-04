from data.database import Database
from WB_PARSER import GET_PRICE
db = Database("data/products.db")

class PriceTracker:
    def __init__(self):
        pass

    # Исправленный код для работы с user_id
    async def check_prices(self, user_id):
        products = await db.get_user_products(user_id)
        changes = []
        print("suka,!")

        for product in products:
            new_price = await GET_PRICE(product['url'])  # Получаем точную цену
            if new_price is not None and new_price != product['price']:
                change_percent = (
                    round(((new_price - product['price']) / product['price']) * 100, 2)
                    if product['price'] else 0
                )
                changes.append({
                    'user_id': user_id,  # Используйте правильный идентификатор пользователя
                    'url': product['url'],
                    'old_price': product['price'],
                    'new_price': new_price,
                    'change_percent': change_percent
                })
                await db.update_price(product['id'], new_price, user_id)
        return changes
