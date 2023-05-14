from form.post.form_tester import PostFormTester


class EditPostFormTester(PostFormTester):

    @property
    def of_which_action(self):
        return 'редактирования'
