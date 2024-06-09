About different Dates/times.
"Created_time" and "modified_time" are simultaneously the same datetime.now() 
during Post creation or duplication. They are also datetime.now() as default 
value in the Post model.

"Created_time" is being writed while:
    

"Modified_time" is being writed while:
    define_as_children,
    Post.move_to_general_post,
    Post.save,
    edit_general_post,
    edit_food,
    edit_winepost.

"Published_time" is being writed while:
    edit_food which if not yet published,
    edit_general_post if not yet published,
    Post.publish,
        while edit_winepost if not yet published,
        
"Validated_at" is being writed while:
    Post.publish.
