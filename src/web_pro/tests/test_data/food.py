class FoodPostData:
    food_post_template = {
        'foodName': 'TestFood',
        'foodDescription': 'TestFood',
        'postType': ''
    }

    def get_add_food_payload(self):
        payload = self.food_post_template.copy()
        payload['postType'] = 'add'
        return payload

    def get_add_existing_food_payload(self, food_post):
        return {
            'foodName': food_post.title,
            'foodDescription': food_post.description,
            'postType': 'add',
            'postId': food_post.id
        }

    def get_edit_food_payload(self, food_post):
        payload = self.food_post_template.copy()
        payload['foodId'] = food_post.id
        payload['postType'] = 'edit'
        return payload

    def get_delete_food_payload(self, food_post):
        payload = self.food_post_template.copy()
        payload['foodId'] = food_post.id
        payload['postType'] = 'delete'
        return payload

    def get_food_template(self, post_type):
        payload = self.food_post_template.copy()
        payload['postType'] = post_type
        return payload
